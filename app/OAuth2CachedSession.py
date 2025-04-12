import requests_cache
import requests_oauthlib


class OAuth2CachedSession(
    requests_oauthlib.OAuth2Session,
    requests_cache.CachedSession
):
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
