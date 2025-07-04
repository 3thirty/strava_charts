import base64
import json
import logging
import math
import sys
import time

from requests_cache import RedisCache
from requests_oauthlib import OAuth2Session, TokenUpdated
from oauthlib.oauth2.rfc6749.errors import MissingTokenError

from Config import Config
from Activity import Activity, ActivityList
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

        try:
            ret = json.loads(token)
        except json.decoder.JSONDecodeError:
            raise AuthenticationException

        return ret


class CookieTokenStorage(TokenStorage):
    def __init__(self, request, response):
        self.request = request
        self.response = response

    def set(self, token):
        super().set(token)
        encoded_token = self._encode(token).encode('utf-8')
        cookie_token = base64.urlsafe_b64encode(encoded_token).decode('ascii')
        self.log.debug('Set token in cookie: %s' % cookie_token)
        self.response.set_cookie('token', cookie_token)

    def get(self):
        cookie_data = self.request.get_cookie('token', "")
        cookie_token = base64.urlsafe_b64decode(cookie_data).decode('utf-8')
        self.token = self._decode(cookie_token)
        self.log.debug('Loaded token from cookie: %s' % cookie_token)
        return super().get()


class Strava:
    max_page_size = 100

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
        self.max_page_size = self.config.get('max_page_size', 100)
        self.log.debug("Config loaded: %s" % self.config.dump())

        self.token_storage = token_storage

        token = token_storage.get()

        if (self.config.get('cache_backend') == 'redis'):
            backend = RedisCache(
                host=self.config.get('redis_host'),
                port=self.config.get('redis_port', 6379),
                username=self.config.get('redis_username', 'default'),
                password=self.config.get('redis_password'),
                ssl=self.config.get('redis_ssl', True),
            )

            cache_kwargs = {
                'backend': backend,
                'expire_after': self.config.get('cache_ttl')
            }
        else:
            cache_kwargs = {
                'backend': self.config.get('cache_backend'),
                'cache_name': self.config.get('cache_data_dir', '/app')
                + '/strava_charts.sqlite',
                'expire_after': self.config.get('cache_ttl')
            }

        self.oauth = OAuth2CachedSession(
            oauth_kwargs={
                'token': token,
                'auto_refresh_url': 'https://www.strava.com/oauth/token',
                'auto_refresh_kwargs': {
                    'client_id': self.config.get('strava_client_id'),
                    'client_secret': self.config.get('strava_client_secret')
                },
            },
            cache_kwargs=cache_kwargs
        )

    def getActivities(self, num: int, offset: int = 0) -> ActivityList:
        orig_num = num

        if (num > self.max_page_size):
            remaining = num - self.max_page_size
            num = self.max_page_size
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

            offset += num
            remaining = orig_num - offset
            num = self.max_page_size

        out = out.sortByDate(True)

        if (len(out) > orig_num):
            return ActivityList.slice(out, 0, orig_num)

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
            activities = self.getActivitiesPage(page, self.max_page_size)

            for activity in activities:
                try:
                    out.append(Activity.newFromDict(activity))
                except ValueError as e:
                    self.log.warning("Activity missing required field: %s" % e)

            page = page + 1

            if (len(activities) < self.max_page_size):
                self.log.debug(
                    "Asked for %d got %d. Assuming all activities are fetched"
                    % (self.max_page_size, len(activities))
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
        start_time = time.perf_counter()

        base_url = 'https://www.strava.com/api/v3/athlete/activities'
        url = '%s?page=%d&per_page=%d' % (base_url, page, perPage)

        res = self.get(url)

        if (res.status_code != 200):
            raise AuthenticationException("invalid auth token")

        try:
            self.log.debug("read %s from %s in %0.3f"
                           % (url, "cache" if res.from_cache else "network",
                              time.perf_counter() - start_time))
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


class StravaDemo(Strava):
    def __init__(self, debug: bool = False):
        self.log = logging.getLogger('strava')

        if (debug):
            self.debug(True)
            self.log.debug("Debug enabled")

        self.config = Config()
        self.max_page_size = self.config.get('max_page_size', 100)
        self.log.debug("Config loaded: %s" % self.config.dump())

    def getActivities(self, num: int, offset: int = 0) -> ActivityList:
        out = ActivityList()

        activities = self.getActivitiesPage(0, 0)

        for activity in activities:
            try:
                out.append(Activity.newFromDict(activity))
            except ValueError as e:
                self.log.warning("Activity missing required field: %s" % e)

        out = out.sortByDate(True)

        if (len(out) > num):
            return ActivityList.slice(out, 0, num)

        return out

    def getAllActivities(self) -> ActivityList:
        """
        Get all activities for the user, for all time. Keep walking back
        page-by-page until it looks like we have everything

        return: ActivityList
        """
        out = ActivityList()

        activities = self.getActivitiesPage(0, self.max_page_size)

        for activity in activities:
            try:
                out.append(Activity.newFromDict(activity))
            except ValueError as e:
                self.log.warning("Activity missing required field: %s" % e)

        return out

    def getActivitiesPage(self, page: int, perPage: int) -> dict:
        """
        Fetch a specific page of strava activities

        :param: page the page number to fetch
        :param: perPage the number of activities per page to fetch

        return: dict
        """
        with open('data/demo.json') as demofile:
            return json.load(demofile)

    def get(self, url: str):
        pass


class AuthenticationException(BaseException):
    pass
