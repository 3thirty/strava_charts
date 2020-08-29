import logging
import sys

import bottle
from bottle import route, run, template, request, response, redirect, \
                   static_file
from bottle.ext import beaker

from Chart import Chart
from Strava import Strava, Authentication, AuthenticationException, \
                   CookieTokenStorage, AggregationPeriod

session_opts = {
    'session.type': 'memory',
    'session.cookie_expires': 300,
    'session.auto': True
}

application = beaker.middleware.SessionMiddleware(bottle.app(), session_opts)


@route('/favico/<file:re:.*\\.(ico|png|webmanifest)$>')
def favico(file):
    return static_file(file, root="favico/")


@route('/ping')
def ping():
    return 'pong'


@route('/')
def main():
    token_store = CookieTokenStorage(bottle.request, response)
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
@route('/chart/<metric>/<period>')
def chart(metric: str = 'average_watts', period: str = 'week'):
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

    chart_title = "%s by %s" % (metric, period)
    chart.options.title.text = chart_title

    chart.labels.labels = []
    chart.data.Metric.data = []

    activities = strava.getActivities(100)

    log = logging.getLogger('strava')

    data = activities.aggregateMetricByPeriod(
                metric=metric,
                period=AggregationPeriod.strToEnum(period))

    log.debug(data)

    for label in data:
        chart.labels.labels.append(label)
        chart.data.Metric.data.append(data[label])

    chartJSON = chart.get()

    return template('chart', chartJSON=chartJSON)


if ('dev' in sys.argv):
    run(
        app=application,
        host='localhost',
        port=8080,
        debug=True,
        reloader=True,
        certfile='cert.crt',
        keyfile='private.key',
        server='gunicorn',
    )
