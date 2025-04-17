from requests_cache import CachedSession
from requests_oauthlib import OAuth2Session


class OAuth2CachedSession(
    OAuth2Session,
    CachedSession
):
    def __init__(self, *, oauth_kwargs: dict, cache_kwargs: dict):
        CachedSession.__init__(self, **cache_kwargs)
        OAuth2Session.__init__(self, **oauth_kwargs)

    def getCacheKey(self, request) -> str:
        """
        Get the cache key that requests_cache uses for the given request

        :param request The request

        :return string the cache key
        """
        return self.cache.create_key(request)

    def clear(self, request) -> None:
        """
        clear the cache for a result

        :param request the request to clear from the cache

        :return None
        """
        key = self.getCacheKey(request)
        self.cache.delete(key)
