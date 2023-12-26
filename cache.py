import time


class Cache:
    cache = {}

    @staticmethod
    def get_max_age(cache_control):
        if "max-age=" in cache_control:
            parts = cache_control.split(",")
            for part in parts:
                if part.startswith("max-age="):
                    return int(part.split("=")[1])
        return None

    @classmethod
    def store_in_cache(cls, cache, max_age, url):
        if max_age is not None:
            expiry_time = time.time() + max_age
            cls.cache[url] = (cache, expiry_time)

    # Check if the response is in the cache and if it's not expired.
    @classmethod
    def get_cached_response(cls, url):
        cached_data = cls.cache.get(url)
        if cached_data:
            cache, expiry_time = cached_data
            if time.time() < expiry_time:
                return cache
        return None
