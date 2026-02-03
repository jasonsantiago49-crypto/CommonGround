"""
Redis-backed rate limiter for Common Ground.
Sliding window counters with per-IP and per-actor tracking.
"""
import structlog
from fastapi import Depends, HTTPException, Request

import redis.asyncio as aioredis

from app.core.config import settings

logger = structlog.get_logger()

_redis_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=20,
        )
    return _redis_pool


class RateLimiter:
    """
    FastAPI dependency that enforces per-IP rate limits via Redis.
    Usage: Depends(RateLimiter(requests=5, window=300, prefix="login"))
    """

    def __init__(self, requests: int, window: int, prefix: str = "general"):
        """
        Args:
            requests: Max number of requests allowed in the window.
            window: Time window in seconds.
            prefix: Key prefix for grouping (e.g., "login", "register").
        """
        self.requests = requests
        self.window = window
        self.prefix = prefix

    async def __call__(self, request: Request) -> None:
        try:
            r = await get_redis()
            client_ip = self._get_client_ip(request)
            key = f"cg:rate:{self.prefix}:{client_ip}"

            current = await r.get(key)
            if current is not None and int(current) >= self.requests:
                logger.warning(
                    "rate_limit_exceeded",
                    prefix=self.prefix,
                    ip=client_ip,
                    limit=self.requests,
                    window=self.window,
                )
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later.",
                )

            pipe = r.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.window)
            await pipe.execute()
        except HTTPException:
            raise
        except Exception as e:
            # If Redis is down, allow the request but log the failure.
            # Never block the service because rate limiting is unavailable.
            logger.error("rate_limiter_redis_error", error=str(e))

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract real client IP, respecting X-Forwarded-For from Traefik."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # First IP in the chain is the real client
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"


# ── Pre-configured limiters ──────────────────────────────────────────
# These match the constants in constants.py but enforced at the route level.

rate_limit_login = RateLimiter(requests=5, window=300, prefix="login")
rate_limit_register = RateLimiter(requests=3, window=3600, prefix="register")
rate_limit_post = RateLimiter(requests=5, window=3600, prefix="post")
rate_limit_comment = RateLimiter(requests=30, window=3600, prefix="comment")
rate_limit_vote = RateLimiter(requests=100, window=3600, prefix="vote")
rate_limit_flag = RateLimiter(requests=10, window=3600, prefix="flag")
