import logging
from datetime import datetime, timedelta

import bottle
from bottle import route, run, template, request, response, redirect
from bottle.ext import beaker

from Chart import Chart
from Strava import Strava, Authentication, AuthenticationException, \
                   TokenStorage, CookieTokenStorage

session_opts = {
    'session.type': 'memory',
    'session.cookie_expires': 300,
    'session.auto': True
}

app = beaker.middleware.SessionMiddleware(bottle.app(), session_opts)


@route('/ping')
def ping():
    return 'pong'


@route('/')
def main():
    token_store = CookieTokenStorage(request, response)
    strava = Strava(token_storage=token_store, debug=True)

    out = ''
    activities = strava.getActivities(300)

    for a in activities:
        out += "%s\n" % (
            a.average_watts
        )

    return out


@route('/verify')
def verify():
    session = bottle.request.environ.get('beaker.session')

    token_store = CookieTokenStorage(request, response)

    token = Authentication.complete(
        url=request.url,
        session=session,
        token_store=token_store
    )

    if (token):
        # todo: redirect should be a param?
        redirect('/chart')
    else:
        response.status = 400
        return "Authentication failure"


@route('/chart')
def chart():
    if (request.query.force):
        force = True
    else:
        force = False

    token_store = CookieTokenStorage(request, response)

    try:
        strava = Strava(
            token_storage=token_store,
            debug=True,
            force=force
        )
    except AuthenticationException:
        session = bottle.request.environ.get('beaker.session')

        url = Authentication.start(
            session=session
        )

        redirect(url)

    chart = Chart()

    chart.labels.labels = []
    chart.data.Power.data = []

    out_activities = {}

    activities = strava.getActivities(100)

    log = logging.getLogger('strava')

    for a in activities:
        out_activities[a.getDateHumanReadable()] = a.average_watts

    total_days = (activities.getMaxDate() - activities.getMinDate()).days + 2  # why 2?
    min_date = datetime.date(activities.getMinDate())

    print("chart params: maxdate=%s mindate=%s total_days=%s" %
        (activities.getMaxDate(), activities.getMinDate(), total_days)
    )

    print("out_activities: %s", out_activities)

    for i in range(0, total_days):
        hr_date = datetime.strftime((min_date + timedelta(days=i)), "%x")
        chart.labels.labels.append(hr_date)

        if (hr_date in out_activities):
            chart.data.Power.data.append(out_activities[hr_date])
        else:
            chart.data.Power.data.append(None)

    chartJSON = chart.get()

    return template('chart', chartJSON=chartJSON)


run(
    host='localhost',
    port=8080,
    debug=True,
    reloader=True,
    certfile='cert.crt',
    keyfile='private.key',
    server='gunicorn',
    app=app
)
