from datetime import datetime
import json
import logging
import sys
import time

import bottle
from bottle import route, run, template, request, response, redirect, \
                   static_file
from bottle.ext import beaker

from Chart import Chart
from Strava import Strava, ActivityList, Authentication, \
                   AuthenticationException, CookieTokenStorage, \
                   AggregationPeriod

session_opts = {
    'session.type': 'memory',
    'session.cookie_expires': 300,
    'session.auto': True
}

application = beaker.middleware.SessionMiddleware(bottle.app(), session_opts)


@route('/favico/<file:re:.*\\.(ico|png|webmanifest)$>')
@route('/<file:re:favicon.ico$>')
def favico(file):
    return static_file(file, root="favico/")


@route('/ping')
def ping():
    return 'pong'


@route('/dump')
def main():
    try:
        token_store = CookieTokenStorage(bottle.request, response)
        strava = Strava(token_storage=token_store, debug=True)
    except AuthenticationException:
        response.status = 401

        return "Not Authorized"

    if (request.query.count):
        count = int(request.query.count)
    else:
        count = 100

    activities = strava.getActivities(count)

    response.set_header('Content-Type', 'application/json')
    return activities.dump()


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
        redirect('/preload')
    else:
        response.status = 400
        return "Authentication failure"


@route('/preload')
def preload():
    """
    Load all strava data for the loggedin user into the requests cache. Right
    now, this is done synchronously and will likely time out for users with
    many activities. In future, we should make these requests offline and use
    this endpoint to trigger a fetch and query current status

    The current behaviour is to keep redirecting this endpoint until all data
    is loaded in a timely manner, at which point we redirect to /chart
    """
    MAX_EXEC_TIME = 25

    force = bool(request.query.force)
    token_store = CookieTokenStorage(request, response)
    start = time.perf_counter()

    try:
        strava = Strava(
            token_storage=token_store,
            debug=True,
            force=force
        )
    except AuthenticationException:
        response.status = 401

        return "Not Authorized"

    page = 1
    done = False
    while (not done):
        if ((time.perf_counter() - start) > MAX_EXEC_TIME):
            break

        activities = strava.getActivitiesPage(page, strava.MAX_PAGE_SIZE)

        page = page + 1
        if (len(activities) < strava.MAX_PAGE_SIZE):
            strava.log.debug(
                "Asked for %d got %d. Assuming all activities are fetched"
                % (strava.MAX_PAGE_SIZE, len(activities))
            )

            done = True

    if (done):
        redirect('/chart')
    else:
        redirect('/preload')


@route('/chart')
@route('/chart/<type>/<metric>/<period>')
def chart(type: str = 'average', metric: str = 'average_watts',
          period: str = 'week'):
    """
    Produce a page with a chart

    Accepted arguments:
        limit: Maximum number of activities to chart
        after: Only chart events with a start date after this (expected to be
               a date in format YYYY-mm-dd)
    """
    log = logging.getLogger('strava')

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

    if (request.query.limit):
        activities = strava.getActivities(int(request.query.limit))
    else:
        activities = strava.getAllActivities()

    if (request.query.after):
        try:
            after_date = datetime.fromisoformat(request.query.after)
            activities = ActivityList.trimBeforeDate(activities, after_date)
        except ValueError:
            pass

    if (type == 'total'):
        data = activities.aggregateTotalMetricByPeriod(
                    metric=metric,
                    period=AggregationPeriod.strToEnum(period))
    else:
        data = activities.aggregateAverageMetricByPeriod(
                    metric=metric,
                    period=AggregationPeriod.strToEnum(period))

    log.debug("chart data: %s" % data)

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
