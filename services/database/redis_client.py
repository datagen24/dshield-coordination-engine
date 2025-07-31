"""Redis client for DShield Coordination Engine."""

import logging
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import redis
from redis.exceptions import ConnectionError, RedisError, TimeoutError

from services.api.config import settings

logger = logging.getLogger(__name__)

# Redis connection pool
redis_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    password=settings.redis_password,
    db=settings.redis_db,
    max_connections=settings.redis_max_connections,
    decode_responses=True,  # Automatically decode responses to strings
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
    health_check_interval=30,
)

# Redis client instance
redis_client = redis.Redis(connection_pool=redis_pool)


class RedisConnectionManager:
    """Manages Redis connections with health monitoring and error handling."""

    def __init__(self):
        self.client = redis_client
        self.last_health_check = 0
        self.health_check_interval = 60  # Check health every 60 seconds

    def get_connection(self) -> redis.Redis:
        """Get a Redis connection from the pool."""
        return self.client

    @contextmanager
    def get_connection_context(self) -> Generator[redis.Redis, None, None]:
        """Context manager for Redis connections with automatic error handling."""
        connection = self.get_connection()
        try:
            yield connection
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection error: {e}")
            raise
        except RedisError as e:
            logger.error(f"Redis operation error: {e}")
            raise

    async def check_health(self) -> dict[str, Any]:
        """Check Redis connection health.

        Returns:
            dict: Health status with details
        """
        try:
            # Test basic operations
            start_time = time.time()
            self.client.ping()
            response_time = (time.time() - start_time) * 1000

            # Get connection pool info
            pool = self.client.connection_pool
            pool_info = {
                "connection_kwargs": pool.connection_kwargs,
                "max_connections": pool.max_connections,
                "connection_class": pool.connection_class.__name__,
            }

            return {
                "status": "healthy",
                "message": "Redis connection successful",
                "response_time_ms": round(response_time, 2),
                "pool_info": pool_info,
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Redis connection failed: {str(e)}",
                "response_time_ms": None,
                "pool_info": None,
            }

    def get_info(self) -> dict[str, Any]:
        """Get Redis server information for monitoring.

        Returns:
            dict: Redis server information
        """
        try:
            info = self.client.info()
            return {
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
                "uptime_in_seconds": info.get("uptime_in_seconds"),
            }
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {"error": str(e)}

    def get_memory_usage(self) -> dict[str, Any]:
        """Get Redis memory usage statistics.

        Returns:
            dict: Memory usage information
        """
        try:
            info = self.client.info("memory")
            return {
                "used_memory": info.get("used_memory"),
                "used_memory_human": info.get("used_memory_human"),
                "used_memory_peak": info.get("used_memory_peak"),
                "used_memory_peak_human": info.get("used_memory_peak_human"),
                "maxmemory": info.get("maxmemory"),
                "maxmemory_human": info.get("maxmemory_human"),
                "maxmemory_policy": info.get("maxmemory_policy"),
            }
        except Exception as e:
            logger.error(f"Failed to get Redis memory usage: {e}")
            return {"error": str(e)}

    def flush_all(self) -> bool:
        """Flush all Redis data (use with caution).

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.client.flushall()
            logger.warning("Redis flushall executed")
            return True
        except Exception as e:
            logger.error(f"Redis flushall failed: {e}")
            return False

    def get_keys_count(self, pattern: str = "*") -> int:
        """Get count of keys matching pattern.

        Args:
            pattern: Key pattern to match

        Returns:
            int: Number of matching keys
        """
        try:
            return len(self.client.keys(pattern))
        except Exception as e:
            logger.error(f"Failed to get keys count: {e}")
            return 0


# Global Redis connection manager instance
redis_manager = RedisConnectionManager()


def get_redis_client() -> redis.Redis:
    """Get Redis client instance.

    Returns:
        redis.Redis: Redis client
    """
    return redis_manager.get_connection()


@contextmanager
def get_redis_context() -> Generator[redis.Redis, None, None]:
    """Context manager for Redis operations.

    Yields:
        redis.Redis: Redis client

    Example:
        with get_redis_context() as redis_client:
            redis_client.set("key", "value")
    """
    with redis_manager.get_connection_context() as client:
        yield client


async def check_redis_health() -> dict[str, Any]:
    """Check Redis health status.

    Returns:
        dict: Health status with details
    """
    return await redis_manager.check_health()


def get_redis_info() -> dict[str, Any]:
    """Get Redis server information.

    Returns:
        dict: Redis server information
    """
    return redis_manager.get_info()


def get_redis_memory_usage() -> dict[str, Any]:
    """Get Redis memory usage.

    Returns:
        dict: Memory usage information
    """
    return redis_manager.get_memory_usage()
