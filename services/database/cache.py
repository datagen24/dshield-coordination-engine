"""Cache management system for DShield Coordination Engine."""

import json
import logging
from typing import Any

from redis.exceptions import RedisError

from services.database.redis_client import get_redis_context

logger = logging.getLogger(__name__)

# Cache TTL constants (in seconds)
CACHE_TTL = {
    "analysis_result": 86400,  # 24 hours
    "campaign_data": 21600,  # 6 hours
    "threat_intel": 3600,  # 1 hour
    "workflow_state": 3600,  # 1 hour
    "rate_limit": 60,  # 1 minute
    "user_session": 1800,  # 30 minutes
    "search_result": 1800,  # 30 minutes
    "enrichment_data": 7200,  # 2 hours
}

# Cache key prefixes
CACHE_PREFIXES = {
    "analysis": "analysis",
    "campaign": "campaign",
    "threat_intel": "threat",
    "workflow": "workflow",
    "rate_limit": "ratelimit",
    "user": "user",
    "search": "search",
    "enrichment": "enrichment",
}


class CacheManager:
    """Manages Redis caching operations with TTL and invalidation strategies."""

    def __init__(self):
        self.default_ttl = 3600  # 1 hour default

    def _make_key(self, prefix: str, identifier: str) -> str:
        """Create a cache key with prefix.

        Args:
            prefix: Key prefix
            identifier: Unique identifier

        Returns:
            str: Formatted cache key
        """
        return f"{prefix}:{identifier}"

    def _serialize_data(self, data: Any) -> str:
        """Serialize data for Redis storage.

        Args:
            data: Data to serialize

        Returns:
            str: Serialized data
        """
        if isinstance(data, dict | list):
            return json.dumps(data, default=str)
        return str(data)

    def _deserialize_data(self, data: str) -> Any:
        """Deserialize data from Redis storage.

        Args:
            data: Serialized data

        Returns:
            Any: Deserialized data
        """
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data

    def set_analysis_result(self, session_id: str, result: dict[str, Any]) -> bool:
        """Cache analysis result with 24-hour TTL.

        Args:
            session_id: Analysis session ID
            result: Analysis result data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(CACHE_PREFIXES["analysis"], session_id)
                serialized_data = self._serialize_data(result)
                redis_client.setex(key, CACHE_TTL["analysis_result"], serialized_data)
                logger.debug(f"Cached analysis result for session {session_id}")
                return True
        except RedisError as e:
            logger.error(f"Failed to cache analysis result: {e}")
            return False

    def get_analysis_result(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve cached analysis result.

        Args:
            session_id: Analysis session ID

        Returns:
            Optional[Dict[str, Any]]: Cached result or None
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(CACHE_PREFIXES["analysis"], session_id)
                data = redis_client.get(key)
                if data:
                    return self._deserialize_data(data)
                return None
        except RedisError as e:
            logger.error(f"Failed to retrieve cached analysis result: {e}")
            return None

    def set_campaign_data(self, campaign_id: str, data: dict[str, Any]) -> bool:
        """Cache campaign data with 6-hour TTL.

        Args:
            campaign_id: Campaign ID
            data: Campaign data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(CACHE_PREFIXES["campaign"], campaign_id)
                serialized_data = self._serialize_data(data)
                redis_client.setex(key, CACHE_TTL["campaign_data"], serialized_data)
                logger.debug(f"Cached campaign data for campaign {campaign_id}")
                return True
        except RedisError as e:
            logger.error(f"Failed to cache campaign data: {e}")
            return False

    def get_campaign_data(self, campaign_id: str) -> dict[str, Any] | None:
        """Retrieve cached campaign data.

        Args:
            campaign_id: Campaign ID

        Returns:
            Optional[Dict[str, Any]]: Cached campaign data or None
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(CACHE_PREFIXES["campaign"], campaign_id)
                data = redis_client.get(key)
                if data:
                    return self._deserialize_data(data)
                return None
        except RedisError as e:
            logger.error(f"Failed to retrieve cached campaign data: {e}")
            return None

    def set_threat_intel(self, indicator: str, data: dict[str, Any]) -> bool:
        """Cache threat intelligence data with 1-hour TTL.

        Args:
            indicator: Threat indicator
            data: Threat intelligence data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(CACHE_PREFIXES["threat_intel"], indicator)
                serialized_data = self._serialize_data(data)
                redis_client.setex(key, CACHE_TTL["threat_intel"], serialized_data)
                logger.debug(f"Cached threat intel for indicator {indicator}")
                return True
        except RedisError as e:
            logger.error(f"Failed to cache threat intel: {e}")
            return False

    def get_threat_intel(self, indicator: str) -> dict[str, Any] | None:
        """Retrieve cached threat intelligence data.

        Args:
            indicator: Threat indicator

        Returns:
            Optional[Dict[str, Any]]: Cached threat intel or None
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(CACHE_PREFIXES["threat_intel"], indicator)
                data = redis_client.get(key)
                if data:
                    return self._deserialize_data(data)
                return None
        except RedisError as e:
            logger.error(f"Failed to retrieve cached threat intel: {e}")
            return None

    def set_workflow_state(self, workflow_id: str, state: dict[str, Any]) -> bool:
        """Cache workflow state with 1-hour TTL.

        Args:
            workflow_id: Workflow ID
            state: Workflow state data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(CACHE_PREFIXES["workflow"], workflow_id)
                serialized_data = self._serialize_data(state)
                redis_client.setex(key, CACHE_TTL["workflow_state"], serialized_data)
                logger.debug(f"Cached workflow state for workflow {workflow_id}")
                return True
        except RedisError as e:
            logger.error(f"Failed to cache workflow state: {e}")
            return False

    def get_workflow_state(self, workflow_id: str) -> dict[str, Any] | None:
        """Retrieve cached workflow state.

        Args:
            workflow_id: Workflow ID

        Returns:
            Optional[Dict[str, Any]]: Cached workflow state or None
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(CACHE_PREFIXES["workflow"], workflow_id)
                data = redis_client.get(key)
                if data:
                    return self._deserialize_data(data)
                return None
        except RedisError as e:
            logger.error(f"Failed to retrieve cached workflow state: {e}")
            return None

    def set_enrichment_data(self, key: str, data: dict[str, Any]) -> bool:
        """Cache enrichment data with 2-hour TTL.

        Args:
            key: Enrichment key
            data: Enrichment data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                cache_key = self._make_key(CACHE_PREFIXES["enrichment"], key)
                serialized_data = self._serialize_data(data)
                redis_client.setex(
                    cache_key, CACHE_TTL["enrichment_data"], serialized_data
                )
                logger.debug(f"Cached enrichment data for key {key}")
                return True
        except RedisError as e:
            logger.error(f"Failed to cache enrichment data: {e}")
            return False

    def get_enrichment_data(self, key: str) -> dict[str, Any] | None:
        """Retrieve cached enrichment data.

        Args:
            key: Enrichment key

        Returns:
            Optional[Dict[str, Any]]: Cached enrichment data or None
        """
        try:
            with get_redis_context() as redis_client:
                cache_key = self._make_key(CACHE_PREFIXES["enrichment"], key)
                data = redis_client.get(cache_key)
                if data:
                    return self._deserialize_data(data)
                return None
        except RedisError as e:
            logger.error(f"Failed to retrieve cached enrichment data: {e}")
            return None

    def invalidate_analysis_result(self, session_id: str) -> bool:
        """Invalidate cached analysis result.

        Args:
            session_id: Analysis session ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(CACHE_PREFIXES["analysis"], session_id)
                redis_client.delete(key)
                logger.debug(f"Invalidated analysis result for session {session_id}")
                return True
        except RedisError as e:
            logger.error(f"Failed to invalidate analysis result: {e}")
            return False

    def invalidate_campaign_data(self, campaign_id: str) -> bool:
        """Invalidate cached campaign data.

        Args:
            campaign_id: Campaign ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(CACHE_PREFIXES["campaign"], campaign_id)
                redis_client.delete(key)
                logger.debug(f"Invalidated campaign data for campaign {campaign_id}")
                return True
        except RedisError as e:
            logger.error(f"Failed to invalidate campaign data: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern.

        Args:
            pattern: Key pattern to match

        Returns:
            int: Number of keys deleted
        """
        try:
            with get_redis_context() as redis_client:
                keys = redis_client.keys(pattern)
                if keys:
                    deleted = redis_client.delete(*keys)
                    logger.debug(
                        f"Invalidated {deleted} keys matching pattern {pattern}"
                    )
                    return deleted
                return 0
        except RedisError as e:
            logger.error(f"Failed to invalidate pattern {pattern}: {e}")
            return 0

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            dict: Cache statistics
        """
        try:
            with get_redis_context() as redis_client:
                stats = {}
                for prefix_name, prefix in CACHE_PREFIXES.items():
                    pattern = f"{prefix}:*"
                    keys = redis_client.keys(pattern)
                    stats[f"{prefix_name}_keys"] = len(keys)

                    # Calculate total memory usage for this prefix
                    total_memory = 0
                    for key in keys:
                        memory = redis_client.memory_usage(key)
                        if memory:
                            total_memory += memory
                    stats[f"{prefix_name}_memory_bytes"] = total_memory

                return stats
        except RedisError as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}

    def warm_cache(self, data: dict[str, Any]) -> bool:
        """Warm cache with frequently accessed data.

        Args:
            data: Dictionary of cache entries to warm

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                pipeline = redis_client.pipeline()

                for cache_type, entries in data.items():
                    if cache_type == "analysis_results":
                        for session_id, result in entries.items():
                            key = self._make_key(CACHE_PREFIXES["analysis"], session_id)
                            serialized_data = self._serialize_data(result)
                            pipeline.setex(
                                key, CACHE_TTL["analysis_result"], serialized_data
                            )

                    elif cache_type == "campaign_data":
                        for campaign_id, campaign_data in entries.items():
                            key = self._make_key(
                                CACHE_PREFIXES["campaign"], campaign_id
                            )
                            serialized_data = self._serialize_data(campaign_data)
                            pipeline.setex(
                                key, CACHE_TTL["campaign_data"], serialized_data
                            )

                pipeline.execute()
                logger.info("Cache warming completed successfully")
                return True
        except RedisError as e:
            logger.error(f"Failed to warm cache: {e}")
            return False


# Global cache manager instance
cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """Get cache manager instance.

    Returns:
        CacheManager: Cache manager instance
    """
    return cache_manager
