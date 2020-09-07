import enum
import json
import logging
import math
import sys

from collections import OrderedDict
from datetime import datetime
from requests_oauthlib import OAuth2Session, TokenUpdated
from oauthlib.oauth2.rfc6749.errors import MissingTokenError

from Config import Config
from OAuth2CachedSession import OAuth2CachedSession


class Authentication:
    _config = Config()

    def start(session):
        """Start an oauth dance

        :param: web session

        :return: string URL on strava.com that the user should be redirected to
        """
        oauth = OAuth2Session(
            Authentication._config.get('strava_client_id'),
            redirect_uri=Authentication._config.get('strava_redirect_uri'),
            scope=['activity:read']
        )

        authorization_url, state = oauth.authorization_url(
            'https://www.strava.com/oauth/authorize',
            access_type="offline"
        )

        Authentication._storeState(
            session=session,
            state=state
        )

        return authorization_url

    def complete(url: str, session, token_store=None):
        """Finish an oauth dance. Verify the token in the returned URL against
        the saved state

        :param url: The callback URL that strava called
        :param session: the user's web session

        :return: string the token for the user
        """
        client_id = Authentication._config.get('strava_client_id')
        secret = Authentication._config.get('strava_client_secret')

        oauth = OAuth2Session(
            client_id=client_id,
            state=Authentication._getState(session),
        )

        try:
            token = oauth.fetch_token(
                'https://www.strava.com/oauth/token',
                authorization_response=url,
                include_client_id=True,
                client_secret=secret,
            )
        except MissingTokenError:
            return None

        if (token_store):
            token_store.set(token)

        return token

    def _storeState(session, state):
        """Write oauth state data to this user's session

        :param session: the user's web session
        :param state: The oauth state string to write

        :return: string the token for the user
        """
        session['sate'] = state
        session.save()

    def _getState(session):
        """Determine the filename to use for this session

        :param session: the user's web session

        :return: string the token for the user
        """
        return session.get('state')


class AggregationPeriod(enum.Enum):
    DAY = 1
    WEEK = 2
    MONTH = 3
    YEAR = 4

    def strToEnum(s: str):
        try:
            return getattr(AggregationPeriod, s.upper())
        except AttributeError:
            return AggregationPeriod.DAY


class Activity:
    start_date = None
    average_watts = None

    def newFromDict(d):
        # TODO: handle this more sensibly
        if ('average_watts' not in d):
            raise ValueError('average_watts is required')

        if ('weighted_average_watts' not in d):
            raise ValueError('weighted_average_watts is required')

        ret = Activity()
        ret.start_date = d['start_date']
        ret.average_watts = d['average_watts']
        ret.average_speed = d['average_speed']
        ret.distance = d['distance']
        ret.moving_time = d['moving_time']
        ret.total_elevation_gain = d['total_elevation_gain']

        return ret

    def getDateTime(self):
        date_string = self.start_date.rstrip('Z')
        date = datetime.fromisoformat(date_string)

        return date

    def getDateTimestamp(self):
        return self.getDateTime().timestamp()

    def getDateHumanReadable(self):
        date = self.getDateTime()

        return(datetime.strftime(date, "%x"))

    def dump(self):
        out = {}
        out['start_date'] = self.start_date
        out['average_watts'] = self.average_watts
        out['average_speed'] = self.average_speed
        out['distance'] = self.distance
        out['moving_time'] = self.moving_time
        out['total_elevation_gain'] = self.total_elevation_gain

        return out


class ActivityList(list):
    def sortByDate(self):
        return sorted(self, key=lambda self: self.getDateTimestamp())

    def getMinDate(self):
        return self.sortByDate()[0].getDateTime()

    def getMaxDate(self):
        return self.sortByDate()[len(self) - 1].getDateTime()

    def aggregateAverageMetricByPeriod(
            self, metric: str, period: AggregationPeriod) -> OrderedDict:
        """
        Average the requested metric for the activities in the list over the
        given time format

        :param metric: the metric to average
        :param period: the time period to aggregate over

        :return Dict of activies with activity keys set based on timef
        """
        grouped_by_time = {}

        for activity in self:
            time_key = self._getTimeKey(activity, period)

            if ('time_key' not in grouped_by_time):
                grouped_by_time[time_key] = []

            grouped_by_time[time_key].append(activity)

        ret = {}
        for time in grouped_by_time:
            out_value = 0
            for activity in grouped_by_time[time]:
                try:
                    out_value += getattr(activity, metric)
                except KeyError:
                    pass

            ret[time] = (out_value / len(grouped_by_time[time]))

        return OrderedDict(sorted(ret.items(), key=lambda item: item[0]))

    def aggregateTotalMetricByPeriod(
            self, metric: str, period: AggregationPeriod) -> OrderedDict:
        """
        Total the requested metric for the activities in the list over the
        given time format

        :param metric: the metric to average
        :param period: the time period to aggregate over

        :return Dict of activies with activity keys set based on timef
        """
        grouped_by_time = {}

        for activity in self:
            time_key = self._getTimeKey(activity, period)

            if ('time_key' not in grouped_by_time):
                grouped_by_time[time_key] = []

            grouped_by_time[time_key].append(activity)

        ret = {}
        for time in grouped_by_time:
            ret[time] = 0

            for activity in grouped_by_time[time]:
                ret[time] += getattr(activity, metric, 0)

        return OrderedDict(sorted(ret.items(), key=lambda item: item[0]))

    def _getTimeKey(
            self, activity: Activity,
            period: AggregationPeriod) -> str:
        """Determine the time key (i.e. the period start date) for an activity
        and aggregation period

        :param period:   the aggregation period
        :param activity: the activity to deterime the time key for

        :return string the time key in Y-m-d format
        """
        if period == AggregationPeriod.WEEK:
            week = datetime.strftime(activity.getDateTime(), "%Y-%U-1")
            return datetime.strptime(week, "%Y-%U-%w").strftime("%Y-%m-%d")

        if period == AggregationPeriod.MONTH:
            return datetime.strftime(activity.getDateTime(), "%Y-%m-01")

        if period == AggregationPeriod.YEAR:
            return datetime.strftime(activity.getDateTime(), "%Y")

        return datetime.strftime(activity.getDateTime(), "%Y-%m-%d")

    def dump(self) -> str:
        """
        Dump out the entire activity list in json
        """
        out = []

        for activity in self:
            out.append(activity.dump())

        return json.dumps(out)


class TokenStorage():
    token = None
    log = logging.getLogger('strava')

    def set(self, token: dict):
        self.token = token

    def get(self) -> dict:
        if (not self.token):
            self.log.debug("failed to read token from storage")
            raise AuthenticationException("no token found")

        return self.token

    def _encode(self, token: dict) -> str:
        """Encode a token dict into a string for storage

        :param token: string representation of the token

        :return token dict
        """
        if (not token):
            return None

        return json.dumps(token)

    def _decode(self, token: str) -> dict:
        """Decode a token string into a token dict

        :param token: string representation of the token

        :return token dict
        """
        if (not token):
            return None

        return json.loads(token)


class CookieTokenStorage(TokenStorage):
    def __init__(self, request, response):
        self.request = request
        self.response = response

    def set(self, token):
        super().set(token)
        cookie_token = self._encode(token)
        self.log.debug('Set token in cookie: %s' % cookie_token)
        self.response.set_cookie('token', cookie_token)

    def get(self):
        cookie_token = self.request.get_cookie('token')
        self.token = self._decode(cookie_token)
        self.log.debug('Loaded token from cookie: %s' % cookie_token)
        return super().get()


class Strava:
    MAX_PAGE_SIZE = 100

    def debug(self, on=False):
        log = logging.getLogger('requests_oauthlib')

        if (on):
            if (not log.hasHandlers()):
                log.addHandler(logging.StreamHandler(sys.stdout))
                log.setLevel(logging.DEBUG)

            if (not self.log.hasHandlers()):
                self.log.addHandler(logging.StreamHandler(sys.stdout))
                self.log.setLevel(logging.DEBUG)
        else:
            log.addHandler(logging.StreamHandler(logging.NullHandler()))

        return on

    def __init__(
            self, token_storage, debug: bool = False, force: bool = False):
        self.force = force
        self.log = logging.getLogger('strava')

        if (debug):
            self.debug(True)
            self.log.debug("Debug enabled")

        self.config = Config()
        self.log.debug("Config loaded: %s" % self.config.dump())

        self.token_storage = token_storage

        token = token_storage.get()

        self.oauth = OAuth2CachedSession(
            token=token,
            auto_refresh_url='https://www.strava.com/oauth/token',
            auto_refresh_kwargs={
                'client_id': self.config.get('strava_client_id'),
                'client_secret': self.config.get('strava_client_secret')
            },
            expire_after=self.config.get('cache_ttl')
        )

    def getActivities(self, num: int, offset: int = 0) -> ActivityList:
        if (num > self.MAX_PAGE_SIZE):
            remaining = num - self.MAX_PAGE_SIZE
            num = self.MAX_PAGE_SIZE
        else:
            remaining = 0

        out = ActivityList()
        while (remaining >= 0):
            self.log.debug(
                "pagination parameters are: num=%s offset=%s remaining=%s"
                % (num, offset, remaining)
            )

            page = math.floor(offset / num) + 1

            activities = self.getActivitiesPage(page, num)

            for activity in activities:
                try:
                    out.append(Activity.newFromDict(activity))
                except ValueError as e:
                    self.log.warning("Activity missing required field: %s" % e)

            remaining = remaining - num
            offset += num
            num = self.MAX_PAGE_SIZE

        return out

    def getAllActivities(self) -> ActivityList:
        """
        Get all activities for the user, for all time. Keep walking back
        page-by-page until it looks like we have everything

        return: ActivityList
        """
        page = 1
        done = False
        out = ActivityList()

        while (not done):
            activities = self.getActivitiesPage(page, self.MAX_PAGE_SIZE)

            for activity in activities:
                try:
                    out.append(Activity.newFromDict(activity))
                except ValueError as e:
                    self.log.warning("Activity missing required field: %s" % e)

            page = page + 1

            if (len(activities) < self.MAX_PAGE_SIZE):
                self.log.debug(
                    "Asked for %d got %d. Assuming all activities are fetched"
                    % (self.MAX_PAGE_SIZE, len(activities))
                )

                done = True

        return out

    def getActivitiesPage(self, page: int, perPage: int) -> dict:
        """
        Fetch a specific page of strava activities

        :param: page the page number to fetch
        :param: perPage the number of activities per page to fetch

        return: dict
        """
        base_url = 'https://www.strava.com/api/v3/athlete/activities'
        url = '%s?page=%d&per_page=%d' % (base_url, page, perPage)

        res = self.get(url)

        if (res.status_code != 200):
            raise AuthenticationException("invalid auth token")

        try:
            if (res.from_cache):
                self.log.debug("read %s from cache" % url)
            else:
                self.log.debug("read %s from network" % url)
        except AttributeError:
            self.log.debug("read %s from network" % url)

        return json.loads(res.content)

    def get(self, url: str):
        """
        Fetch strava data from the given url, with oauth credentials. This
        handles expired tokens and cache clearing as required

        return: Requests response
        """
        res = None

        self.log.debug("fetching %s" % url)

        try:
            res = self.oauth.get(url=url)
        except TokenUpdated as e:
            self.log.debug("need to update token...")
            self.token_storage.set(e.token)
            return self.get(url=url)

        if (res.from_cache and self.force):
            self.log.debug("clearing cache to prompt re-fetch for %s"
                           % res.request)
            self.oauth.clear(res.request)
            return self.get(url=url)

        return res


class AuthenticationException(BaseException):
    pass
