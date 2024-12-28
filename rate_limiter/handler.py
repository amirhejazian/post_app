import functools
import math
import time
from datetime import datetime

from rate_limiter.exceptions import RateLimitExceededException


class RateLimiter:
    def __init__(self, redis_client, prefix="rate_limiter"):
        self.redis = redis_client
        self.prefix = prefix

    def _get_hour_bucket(self, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        dt = datetime.utcfromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d-%H")

    def increment(self, key, amount=1):
        bucket = self._get_hour_bucket()
        redis_key = f"{self.prefix}:{key}"
        self.redis.hincrby(redis_key, bucket, amount)
        self.redis.expire(redis_key, 3 * 60 * 60)

    def get_count(self, key, specific_time=None):
        if specific_time is None:
            now = time.time()
        else:
            now = specific_time

        current_bucket = self._get_hour_bucket(now)
        previous_bucket = self._get_hour_bucket(now - 3600)  # 1 hour before

        redis_key = f"{self.prefix}:{key}"

        # Get the values from Redis
        data = self.redis.hmget(redis_key, [current_bucket, previous_bucket])
        current_count = int(data[0]) if data[0] else 0
        previous_count = int(data[1]) if data[1] else 0

        # Calculate the weighted count
        current_minute = datetime.utcfromtimestamp(now).minute
        weight = (60 - current_minute) / 60
        weighted_previous = math.ceil(previous_count * weight)

        return current_count + weighted_previous

    def is_limited(self, key, min_limit=1000, max_limit=None, bucket_increase_rate=0.3):
        limit = self.get_count(key, time.time() - 3600) * (1 + bucket_increase_rate)
        print(limit)
        limit = max(limit, min_limit)
        if max_limit is not None:
            limit = min(limit, max_limit)
        print(limit, self.get_count(key))
        return limit <= self.get_count(key)

    def limit(self, limit_args, min_limit=1000, max_limit=None, bucket_increase_rate=0.3):
        def limiter(func):
            @functools.wraps(func)
            def inner(*args, **kwargs):
                to_limit_args = [str(kwargs.get(k)) for k in limit_args]
                key = f"{func.__name__}:{"".join(to_limit_args)}"
                if self.is_limited(key, min_limit, max_limit, bucket_increase_rate):
                    raise RateLimitExceededException("Rate limit exceeded for method {}".format(func.__name__))
                self.increment(key)
                return func(*args, **kwargs)

            return inner

        return limiter
