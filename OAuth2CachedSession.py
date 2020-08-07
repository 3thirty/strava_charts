import requests_cache
import requests_oauthlib


class OAuth2CachedSession(
    requests_oauthlib.OAuth2Session,
    requests_cache.CachedSession
):
    pass
