"""Rate limiting implementation for DShield Coordination Engine."""

import logging
import time

import redis
from redis.exceptions import RedisError

from services.database.redis_client import get_redis_context

logger = logging.getLogger(__name__)

# Rate limiting constants
RATE_LIMIT_TTL = 60  # 1 minute for rate limit tracking
RATE_LIMIT_WINDOW = 60  # 1 minute sliding window

# Rate limit key prefixes
RATE_LIMIT_PREFIXES = {
    "api_key": "ratelimit:api",
    "endpoint": "ratelimit:endpoint",
    "global": "ratelimit:global",
    "ip": "ratelimit:ip",
    "user": "ratelimit:user",
}


class RateLimiter:
    """Implements sliding window rate limiting with Redis."""

    def __init__(self):
        self.default_window = RATE_LIMIT_WINDOW

    def _make_key(self, prefix: str, identifier: str, endpoint: str = "") -> str:
        """Create a rate limit key.

        Args:
            prefix: Key prefix
            identifier: Unique identifier (API key, IP, user ID)
            endpoint: Optional endpoint name

        Returns:
            str: Formatted rate limit key
        """
        if endpoint:
            return f"{prefix}:{identifier}:{endpoint}"
        return f"{prefix}:{identifier}"

    def _get_current_timestamp(self) -> int:
        """Get current timestamp in seconds.

        Returns:
            int: Current timestamp
        """
        return int(time.time())

    def _clean_old_entries(
        self, redis_client: redis.Redis, key: str, window: int
    ) -> int:
        """Clean old entries from the sliding window.

        Args:
            redis_client: Redis client
            key: Rate limit key
            window: Time window in seconds

        Returns:
            int: Number of entries removed
        """
        current_time = self._get_current_timestamp()
        cutoff_time = current_time - window

        # Remove entries older than the window
        removed = redis_client.zremrangebyscore(key, 0, cutoff_time)
        return removed

    def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window: int = RATE_LIMIT_WINDOW,
        prefix: str = "api_key",
    ) -> tuple[bool, dict[str, any]]:
        """Check if request is within rate limit.

        Args:
            identifier: Unique identifier (API key, IP, user ID)
            limit: Maximum requests allowed in window
            window: Time window in seconds
            prefix: Rate limit prefix

        Returns:
            Tuple[bool, Dict]: (allowed, rate_limit_info)
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(RATE_LIMIT_PREFIXES[prefix], identifier)
                current_time = self._get_current_timestamp()

                # Clean old entries
                self._clean_old_entries(redis_client, key, window)

                # Get current request count
                request_count = redis_client.zcard(key)

                # Check if limit exceeded
                if request_count >= limit:
                    # Get oldest request time for retry-after calculation
                    oldest_request = redis_client.zrange(key, 0, 0, withscores=True)
                    retry_after = 0
                    if oldest_request:
                        oldest_time = oldest_request[0][1]
                        retry_after = window - (current_time - oldest_time)

                    return False, {
                        "allowed": False,
                        "limit": limit,
                        "remaining": 0,
                        "reset_time": current_time + window,
                        "retry_after": max(0, retry_after),
                        "window": window,
                    }

                # Add current request
                redis_client.zadd(key, {str(current_time): current_time})
                redis_client.expire(key, window)

                return True, {
                    "allowed": True,
                    "limit": limit,
                    "remaining": limit - request_count - 1,
                    "reset_time": current_time + window,
                    "retry_after": 0,
                    "window": window,
                }
        except RedisError as e:
            logger.error(f"Rate limit check failed: {e}")
            # Allow request if Redis is unavailable
            return True, {
                "allowed": True,
                "limit": limit,
                "remaining": limit,
                "reset_time": self._get_current_timestamp() + window,
                "retry_after": 0,
                "window": window,
                "error": "Rate limit check failed, allowing request",
            }

    def check_endpoint_rate_limit(
        self,
        api_key: str,
        endpoint: str,
        limit: int,
        window: int = RATE_LIMIT_WINDOW,
    ) -> tuple[bool, dict[str, any]]:
        """Check endpoint-specific rate limit.

        Args:
            api_key: API key
            endpoint: Endpoint name
            limit: Maximum requests allowed in window
            window: Time window in seconds

        Returns:
            Tuple[bool, Dict]: (allowed, rate_limit_info)
        """
        return self.check_rate_limit(
            f"{api_key}:{endpoint}",
            limit,
            window,
            "endpoint",
        )

    def check_global_rate_limit(
        self, endpoint: str, limit: int, window: int = RATE_LIMIT_WINDOW
    ) -> tuple[bool, dict[str, any]]:
        """Check global rate limit for endpoint.

        Args:
            endpoint: Endpoint name
            limit: Maximum requests allowed in window
            window: Time window in seconds

        Returns:
            Tuple[bool, Dict]: (allowed, rate_limit_info)
        """
        return self.check_rate_limit(endpoint, limit, window, "global")

    def check_ip_rate_limit(
        self, ip_address: str, limit: int, window: int = RATE_LIMIT_WINDOW
    ) -> tuple[bool, dict[str, any]]:
        """Check IP-based rate limit.

        Args:
            ip_address: IP address
            limit: Maximum requests allowed in window
            window: Time window in seconds

        Returns:
            Tuple[bool, Dict]: (allowed, rate_limit_info)
        """
        return self.check_rate_limit(ip_address, limit, window, "ip")

    def check_user_rate_limit(
        self, user_id: str, limit: int, window: int = RATE_LIMIT_WINDOW
    ) -> tuple[bool, dict[str, any]]:
        """Check user-based rate limit.

        Args:
            user_id: User ID
            limit: Maximum requests allowed in window
            window: Time window in seconds

        Returns:
            Tuple[bool, Dict]: (allowed, rate_limit_info)
        """
        return self.check_rate_limit(user_id, limit, window, "user")

    def get_rate_limit_info(
        self, identifier: str, prefix: str = "api_key"
    ) -> dict[str, any]:
        """Get rate limit information for an identifier.

        Args:
            identifier: Unique identifier
            prefix: Rate limit prefix

        Returns:
            Dict: Rate limit information
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(RATE_LIMIT_PREFIXES[prefix], identifier)

                # Get all requests in the window
                current_time = self._get_current_timestamp()
                window_start = current_time - self.default_window

                requests = redis_client.zrangebyscore(
                    key, window_start, current_time, withscores=True
                )

                return {
                    "identifier": identifier,
                    "prefix": prefix,
                    "request_count": len(requests),
                    "window_start": window_start,
                    "window_end": current_time,
                    "requests": [
                        {"timestamp": req[1], "request_id": req[0]} for req in requests
                    ],
                }
        except RedisError as e:
            logger.error(f"Failed to get rate limit info: {e}")
            return {"error": str(e)}

    def reset_rate_limit(self, identifier: str, prefix: str = "api_key") -> bool:
        """Reset rate limit for an identifier.

        Args:
            identifier: Unique identifier
            prefix: Rate limit prefix

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(RATE_LIMIT_PREFIXES[prefix], identifier)
                redis_client.delete(key)
                logger.debug(f"Reset rate limit for {prefix}:{identifier}")
                return True
        except RedisError as e:
            logger.error(f"Failed to reset rate limit: {e}")
            return False

    def get_rate_limit_stats(self) -> dict[str, any]:
        """Get rate limiting statistics.

        Returns:
            dict: Rate limiting statistics
        """
        try:
            with get_redis_context() as redis_client:
                stats = {}

                for prefix_name, prefix in RATE_LIMIT_PREFIXES.items():
                    pattern = f"{prefix}:*"
                    keys = redis_client.keys(pattern)
                    stats[f"{prefix_name}_keys"] = len(keys)

                    # Count total requests across all keys for this prefix
                    total_requests = 0
                    for key in keys:
                        request_count = redis_client.zcard(key)
                        total_requests += request_count

                    stats[f"{prefix_name}_total_requests"] = total_requests

                return stats
        except RedisError as e:
            logger.error(f"Failed to get rate limit stats: {e}")
            return {"error": str(e)}

    def cleanup_expired_rate_limits(self) -> int:
        """Clean up expired rate limit entries.

        Returns:
            int: Number of keys cleaned up
        """
        try:
            with get_redis_context() as redis_client:
                cleaned_count = 0

                for _prefix_name, prefix in RATE_LIMIT_PREFIXES.items():
                    pattern = f"{prefix}:*"
                    keys = redis_client.keys(pattern)

                    for key in keys:
                        # Check if key has expired
                        ttl = redis_client.ttl(key)
                        if ttl == -1:  # No TTL set, clean it up
                            redis_client.delete(key)
                            cleaned_count += 1
                        elif ttl == -2:  # Key doesn't exist
                            continue

                logger.info(f"Cleaned up {cleaned_count} expired rate limit keys")
                return cleaned_count
        except RedisError as e:
            logger.error(f"Failed to cleanup expired rate limits: {e}")
            return 0

    def set_rate_limit_config(
        self, identifier: str, config: dict[str, any], prefix: str = "api_key"
    ) -> bool:
        """Set rate limit configuration for an identifier.

        Args:
            identifier: Unique identifier
            config: Rate limit configuration
            prefix: Rate limit prefix

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                config_key = (
                    f"config:{self._make_key(RATE_LIMIT_PREFIXES[prefix], identifier)}"
                )
                redis_client.setex(
                    config_key,
                    RATE_LIMIT_TTL * 10,  # Longer TTL for config
                    str(config),
                )
                logger.debug(f"Set rate limit config for {prefix}:{identifier}")
                return True
        except RedisError as e:
            logger.error(f"Failed to set rate limit config: {e}")
            return False

    def get_rate_limit_config(
        self, identifier: str, prefix: str = "api_key"
    ) -> dict[str, any] | None:
        """Get rate limit configuration for an identifier.

        Args:
            identifier: Unique identifier
            prefix: Rate limit prefix

        Returns:
            Optional[Dict]: Rate limit configuration or None
        """
        try:
            with get_redis_context() as redis_client:
                config_key = (
                    f"config:{self._make_key(RATE_LIMIT_PREFIXES[prefix], identifier)}"
                )
                config_data = redis_client.get(config_key)

                if config_data:
                    return eval(config_data)  # Convert string back to dict
                return None
        except RedisError as e:
            logger.error(f"Failed to get rate limit config: {e}")
            return None


# Global rate limiter instance
rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance.

    Returns:
        RateLimiter: Rate limiter instance
    """
    return rate_limiter
