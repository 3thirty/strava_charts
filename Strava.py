import json
import logging
import math
import sys

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
        oauth = OAuth2Session(
            client_id=Authentication._config.get('strava_client_id'),
            state=Authentication._getState(session),
        )

        try:
            token = oauth.fetch_token(
                'https://www.strava.com/oauth/token',
                authorization_response=url,
                include_client_id=True,
                client_secret=Authentication._config.get('strava_client_secret'),
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


class Activity:
    start_date = None
    average_watts = None

    def newFromDict(d):
        if ('average_watts' not in d):
            raise ValueError('average_watts is required')

        if ('weighted_average_watts' not in d):
            raise ValueError('weighted_average_watts is required')

        ret = Activity()
        ret.start_date = d['start_date']
        ret.average_watts = d['average_watts']

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


class ActivityList(list):
    def sortByDate(self):
        return sorted(self, key=lambda self: self.getDateTimestamp())

    def getMinDate(self):
        return self.sortByDate()[0].getDateTime()

    def getMaxDate(self):
        return self.sortByDate()[len(self) - 1].getDateTime()


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
            log.addHandler(logging.StreamHandler(sys.stdout))
            log.setLevel(logging.DEBUG)

            self.log.addHandler(logging.StreamHandler(sys.stdout))
            self.log.setLevel(logging.DEBUG)
        else:
            log.addHandler(logging.StreamHandler(logging.NullHandler()))

        return on

    def __init__(self, token_storage, debug=False, force=False):
        self.log = logging.getLogger('strava')

        if (debug):
            self.debug(True)
            self.log.debug("Debug enabled")

        self.config = Config()
        self.log.debug("Config loaded: %s" % self.config.dump())

        self.token_storage = token_storage

        token = token_storage.get()

        if (force):
            self.oauth = OAuth2Session(
                token=token,
                auto_refresh_url='https://www.strava.com/oauth/token',
                auto_refresh_kwargs={
                    'client_id': self.config.get('strava_client_id'),
                    'client_secret': self.config.get('strava_client_secret')
                }
            )
        else:
            self.oauth = OAuth2CachedSession(
                token=token,
                auto_refresh_url='https://www.strava.com/oauth/token',
                auto_refresh_kwargs={
                    'client_id': self.config.get('strava_client_id'),
                    'client_secret': self.config.get('strava_client_secret')
                }
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
                "pagination parameter are: num=%s offset=%s remaining=%s"
                % (num, offset, remaining)
            )

            page = math.floor(offset / num) + 1

            base_url = 'https://www.strava.com/api/v3/athlete/activities'
            url = '%s?page=%d&per_page=%d' % (base_url, page, num)

            res = None
            try:
                res = self.oauth.get(url=url)
            except TokenUpdated as e:
                self.token_storage.set(e.token)
                res = self.oauth.get(url=url)

            if (res.status_code != 200):
                raise AuthenticationException("invalid auth token")

            try:
                if (res.from_cache):
                    self.log.debug("read %s from cache" % url)
                else:
                    self.log.debug("read %s from network" % url)
            except AttributeError:
                self.log.debug("read %s from network" % url)

            activities = json.loads(res.content)

            for activity in activities:
                try:
                    out.append(Activity.newFromDict(activity))
                except ValueError as e:
                    self.log.warning("Activity missing required field: %s" % e)

            remaining = remaining - num
            offset += num
            num = self.MAX_PAGE_SIZE

        return out


class AuthenticationException(BaseException):
    pass
