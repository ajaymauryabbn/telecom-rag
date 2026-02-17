
import time
import os
from typing import Optional


class RateLimiter:
    """
    Redis-based sliding window rate limiter.
    Falls back to in-memory tracking when Redis is unavailable.
    """
    def __init__(self, limit: int = 100, window: int = 60):
        self.limit = limit
        self.window = window
        self.redis_client = None
        self._local_requests: dict = {}  # fallback: user_id -> list of timestamps
        self._init_redis()

    def _init_redis(self):
        try:
            import redis as redis_lib
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            self.redis_client = redis_lib.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1
            )
            self.redis_client.ping()
        except Exception as e:
            print(f"⚠️ RateLimiter: Redis not available ({e}). Using in-memory rate limiting.")
            self.redis_client = None

    def is_allowed(self, user_id: str) -> bool:
        """Check if request is allowed for user_id."""
        now = time.time()

        if not self.redis_client:
            # In-memory fallback
            if user_id not in self._local_requests:
                self._local_requests[user_id] = []
            reqs = self._local_requests[user_id]
            # Prune expired entries
            reqs[:] = [t for t in reqs if now - t < self.window]
            if len(reqs) >= self.limit:
                return False
            reqs.append(now)
            return True

        key = f"rate_limit:{user_id}"

        try:
            pipeline = self.redis_client.pipeline()
            pipeline.zremrangebyscore(key, 0, now - self.window)
            pipeline.zcard(key)
            pipeline.zadd(key, {str(now): now})
            pipeline.expire(key, self.window + 1)

            results = pipeline.execute()
            request_count = results[1]
            return request_count < self.limit

        except Exception as e:
            print(f"⚠️ Rate limit check failed: {e}")
            return True
            
    def get_remaining(self, user_id: str) -> int:
        if not self.redis_client:
            now = time.time()
            reqs = self._local_requests.get(user_id, [])
            active = [t for t in reqs if now - t < self.window]
            return max(0, self.limit - len(active))

        key = f"rate_limit:{user_id}"
        try:
            count = self.redis_client.zcard(key)
            return max(0, self.limit - count)
        except Exception:
            return self.limit
