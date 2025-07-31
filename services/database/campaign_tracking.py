"""Real-time campaign tracking for DShield Coordination Engine."""

import json
import logging
from datetime import datetime
from typing import Any

from redis.exceptions import RedisError

from services.database.redis_client import get_redis_context

logger = logging.getLogger(__name__)

# Campaign tracking constants
CAMPAIGN_TRACKING_TTL = 86400  # 24 hours for campaign tracking
ACTIVITY_STREAM_TTL = 604800  # 7 days for activity streams

# Campaign tracking key prefixes
CAMPAIGN_PREFIXES = {
    "active": "campaigns:active",
    "indicators": "campaign:indicators",
    "activity": "campaign:activity",
    "alerts": "campaign:alerts",
    "metrics": "campaign:metrics",
    "synchronization": "campaign:sync",
}


class CampaignTracker:
    """Manages real-time campaign tracking and monitoring."""

    def __init__(self):
        self.default_ttl = CAMPAIGN_TRACKING_TTL

    def _make_key(self, prefix: str, campaign_id: str, suffix: str = "") -> str:
        """Create a campaign tracking key.

        Args:
            prefix: Key prefix
            campaign_id: Campaign ID
            suffix: Optional suffix

        Returns:
            str: Formatted campaign key
        """
        if suffix:
            return f"{prefix}:{campaign_id}:{suffix}"
        return f"{prefix}:{campaign_id}"

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

    def add_active_campaign(
        self, campaign_id: str, campaign_data: dict[str, Any]
    ) -> bool:
        """Add campaign to active campaigns set.

        Args:
            campaign_id: Campaign ID
            campaign_data: Campaign data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                # Add to active campaigns set
                redis_client.sadd(CAMPAIGN_PREFIXES["active"], campaign_id)

                # Store campaign data
                key = self._make_key("campaign", campaign_id, "data")
                serialized_data = self._serialize_data(campaign_data)
                redis_client.setex(key, self.default_ttl, serialized_data)

                logger.debug(f"Added active campaign {campaign_id}")
                return True
        except RedisError as e:
            logger.error(f"Failed to add active campaign: {e}")
            return False

    def remove_active_campaign(self, campaign_id: str) -> bool:
        """Remove campaign from active campaigns set.

        Args:
            campaign_id: Campaign ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                # Remove from active campaigns set
                redis_client.srem(CAMPAIGN_PREFIXES["active"], campaign_id)

                # Clean up campaign data
                key = self._make_key("campaign", campaign_id, "data")
                redis_client.delete(key)

                logger.debug(f"Removed active campaign {campaign_id}")
                return True
        except RedisError as e:
            logger.error(f"Failed to remove active campaign: {e}")
            return False

    def get_active_campaigns(self) -> set[str]:
        """Get set of active campaign IDs.

        Returns:
            Set[str]: Set of active campaign IDs
        """
        try:
            with get_redis_context() as redis_client:
                campaigns = redis_client.smembers(CAMPAIGN_PREFIXES["active"])
                return {
                    campaign.decode() if isinstance(campaign, bytes) else campaign
                    for campaign in campaigns
                }
        except RedisError as e:
            logger.error(f"Failed to get active campaigns: {e}")
            return set()

    def get_campaign_data(self, campaign_id: str) -> dict[str, Any] | None:
        """Get campaign data.

        Args:
            campaign_id: Campaign ID

        Returns:
            Optional[Dict[str, Any]]: Campaign data or None
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key("campaign", campaign_id, "data")
                data = redis_client.get(key)

                if data:
                    return self._deserialize_data(data)
                return None
        except RedisError as e:
            logger.error(f"Failed to get campaign data: {e}")
            return None

    def add_campaign_indicator(
        self, campaign_id: str, indicator_type: str, indicator_value: str
    ) -> bool:
        """Add indicator to campaign.

        Args:
            campaign_id: Campaign ID
            indicator_type: Type of indicator (ip, domain, hash, etc.)
            indicator_value: Indicator value

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(
                    CAMPAIGN_PREFIXES["indicators"], campaign_id, indicator_type
                )
                redis_client.sadd(key, indicator_value)
                redis_client.expire(key, self.default_ttl)

                logger.debug(
                    f"Added {indicator_type} indicator {indicator_value} to campaign {campaign_id}"
                )
                return True
        except RedisError as e:
            logger.error(f"Failed to add campaign indicator: {e}")
            return False

    def get_campaign_indicators(
        self, campaign_id: str, indicator_type: str | None = None
    ) -> dict[str, set[str]]:
        """Get campaign indicators.

        Args:
            campaign_id: Campaign ID
            indicator_type: Optional indicator type filter

        Returns:
            Dict[str, Set[str]]: Indicators grouped by type
        """
        try:
            with get_redis_context() as redis_client:
                indicators = {}

                if indicator_type:
                    # Get specific indicator type
                    key = self._make_key(
                        CAMPAIGN_PREFIXES["indicators"], campaign_id, indicator_type
                    )
                    values = redis_client.smembers(key)
                    indicators[indicator_type] = {
                        val.decode() if isinstance(val, bytes) else val
                        for val in values
                    }
                else:
                    # Get all indicator types
                    pattern = self._make_key(
                        CAMPAIGN_PREFIXES["indicators"], campaign_id, "*"
                    )
                    keys = redis_client.keys(pattern)

                    for key in keys:
                        # Extract indicator type from key
                        parts = key.split(":")
                        if len(parts) >= 4:
                            ind_type = parts[3]
                            values = redis_client.smembers(key)
                            indicators[ind_type] = {
                                val.decode() if isinstance(val, bytes) else val
                                for val in values
                            }

                return indicators
        except RedisError as e:
            logger.error(f"Failed to get campaign indicators: {e}")
            return {}

    def add_campaign_activity(
        self, campaign_id: str, activity_type: str, activity_data: dict[str, Any]
    ) -> bool:
        """Add activity to campaign stream.

        Args:
            campaign_id: Campaign ID
            activity_type: Type of activity
            activity_data: Activity data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                # Add to activity stream
                stream_key = self._make_key(CAMPAIGN_PREFIXES["activity"], campaign_id)

                # Prepare stream entry
                entry_data = {
                    "type": activity_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": self._serialize_data(activity_data),
                }

                # Add to Redis stream
                redis_client.xadd(stream_key, entry_data, maxlen=1000)
                redis_client.expire(stream_key, ACTIVITY_STREAM_TTL)

                logger.debug(
                    f"Added {activity_type} activity to campaign {campaign_id}"
                )
                return True
        except RedisError as e:
            logger.error(f"Failed to add campaign activity: {e}")
            return False

    def get_campaign_activity(
        self, campaign_id: str, count: int = 100
    ) -> list[dict[str, Any]]:
        """Get recent campaign activity.

        Args:
            campaign_id: Campaign ID
            count: Number of activities to retrieve

        Returns:
            List[Dict[str, Any]]: List of activities
        """
        try:
            with get_redis_context() as redis_client:
                stream_key = self._make_key(CAMPAIGN_PREFIXES["activity"], campaign_id)

                # Get recent entries from stream
                entries = redis_client.xrevrange(stream_key, count=count)

                activities = []
                for entry_id, data in entries:
                    activity = {
                        "id": entry_id.decode()
                        if isinstance(entry_id, bytes)
                        else entry_id,
                        "type": data[b"type"].decode()
                        if b"type" in data
                        else "unknown",
                        "timestamp": data[b"timestamp"].decode()
                        if b"timestamp" in data
                        else "",
                        "data": self._deserialize_data(
                            data[b"data"].decode() if b"data" in data else "{}"
                        ),
                    }
                    activities.append(activity)

                return activities
        except RedisError as e:
            logger.error(f"Failed to get campaign activity: {e}")
            return []

    def add_campaign_alert(
        self, campaign_id: str, alert_type: str, alert_data: dict[str, Any]
    ) -> bool:
        """Add alert for campaign.

        Args:
            campaign_id: Campaign ID
            alert_type: Type of alert
            alert_data: Alert data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                alert_key = self._make_key(CAMPAIGN_PREFIXES["alerts"], campaign_id)

                alert_entry = {
                    "type": alert_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": alert_data,
                }

                # Add to alerts list
                redis_client.lpush(alert_key, self._serialize_data(alert_entry))
                redis_client.ltrim(alert_key, 0, 999)  # Keep last 1000 alerts
                redis_client.expire(alert_key, self.default_ttl)

                logger.debug(f"Added {alert_type} alert for campaign {campaign_id}")
                return True
        except RedisError as e:
            logger.error(f"Failed to add campaign alert: {e}")
            return False

    def get_campaign_alerts(
        self, campaign_id: str, count: int = 50
    ) -> list[dict[str, Any]]:
        """Get recent campaign alerts.

        Args:
            campaign_id: Campaign ID
            count: Number of alerts to retrieve

        Returns:
            List[Dict[str, Any]]: List of alerts
        """
        try:
            with get_redis_context() as redis_client:
                alert_key = self._make_key(CAMPAIGN_PREFIXES["alerts"], campaign_id)

                # Get recent alerts
                alerts_data = redis_client.lrange(alert_key, 0, count - 1)

                alerts = []
                for alert_data in alerts_data:
                    alert = self._deserialize_data(
                        alert_data.decode()
                        if isinstance(alert_data, bytes)
                        else alert_data
                    )
                    alerts.append(alert)

                return alerts
        except RedisError as e:
            logger.error(f"Failed to get campaign alerts: {e}")
            return []

    def update_campaign_metrics(
        self, campaign_id: str, metrics: dict[str, Any]
    ) -> bool:
        """Update campaign metrics.

        Args:
            campaign_id: Campaign ID
            metrics: Metrics data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                metrics_key = self._make_key(CAMPAIGN_PREFIXES["metrics"], campaign_id)

                # Add timestamp to metrics
                metrics["timestamp"] = datetime.utcnow().isoformat()

                # Store metrics
                serialized_metrics = self._serialize_data(metrics)
                redis_client.setex(metrics_key, self.default_ttl, serialized_metrics)

                logger.debug(f"Updated metrics for campaign {campaign_id}")
                return True
        except RedisError as e:
            logger.error(f"Failed to update campaign metrics: {e}")
            return False

    def get_campaign_metrics(self, campaign_id: str) -> dict[str, Any] | None:
        """Get campaign metrics.

        Args:
            campaign_id: Campaign ID

        Returns:
            Optional[Dict[str, Any]]: Campaign metrics or None
        """
        try:
            with get_redis_context() as redis_client:
                metrics_key = self._make_key(CAMPAIGN_PREFIXES["metrics"], campaign_id)
                metrics_data = redis_client.get(metrics_key)

                if metrics_data:
                    return self._deserialize_data(metrics_data)
                return None
        except RedisError as e:
            logger.error(f"Failed to get campaign metrics: {e}")
            return None

    def set_synchronization_status(
        self, campaign_id: str, sync_status: dict[str, Any]
    ) -> bool:
        """Set campaign synchronization status.

        Args:
            campaign_id: Campaign ID
            sync_status: Synchronization status

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                sync_key = self._make_key(
                    CAMPAIGN_PREFIXES["synchronization"], campaign_id
                )

                # Add timestamp
                sync_status["timestamp"] = datetime.utcnow().isoformat()

                # Store sync status
                serialized_status = self._serialize_data(sync_status)
                redis_client.setex(sync_key, self.default_ttl, serialized_status)

                logger.debug(f"Updated sync status for campaign {campaign_id}")
                return True
        except RedisError as e:
            logger.error(f"Failed to set synchronization status: {e}")
            return False

    def get_synchronization_status(self, campaign_id: str) -> dict[str, Any] | None:
        """Get campaign synchronization status.

        Args:
            campaign_id: Campaign ID

        Returns:
            Optional[Dict[str, Any]]: Synchronization status or None
        """
        try:
            with get_redis_context() as redis_client:
                sync_key = self._make_key(
                    CAMPAIGN_PREFIXES["synchronization"], campaign_id
                )
                sync_data = redis_client.get(sync_key)

                if sync_data:
                    return self._deserialize_data(sync_data)
                return None
        except RedisError as e:
            logger.error(f"Failed to get synchronization status: {e}")
            return None

    def get_campaign_tracking_stats(self) -> dict[str, Any]:
        """Get campaign tracking statistics.

        Returns:
            dict: Campaign tracking statistics
        """
        try:
            with get_redis_context() as redis_client:
                stats = {}

                # Active campaigns count
                active_campaigns = self.get_active_campaigns()
                stats["active_campaigns"] = len(active_campaigns)

                # Indicators count by type
                total_indicators = 0
                for campaign_id in active_campaigns:
                    indicators = self.get_campaign_indicators(campaign_id)
                    for _indicator_type, values in indicators.items():
                        total_indicators += len(values)

                stats["total_indicators"] = total_indicators

                # Activity streams count
                activity_pattern = f"{CAMPAIGN_PREFIXES['activity']}:*"
                activity_keys = redis_client.keys(activity_pattern)
                stats["activity_streams"] = len(activity_keys)

                # Alerts count
                alerts_pattern = f"{CAMPAIGN_PREFIXES['alerts']}:*"
                alerts_keys = redis_client.keys(alerts_pattern)
                stats["alert_streams"] = len(alerts_keys)

                return stats
        except RedisError as e:
            logger.error(f"Failed to get campaign tracking stats: {e}")
            return {"error": str(e)}

    def cleanup_expired_campaigns(self) -> int:
        """Clean up expired campaign data.

        Returns:
            int: Number of campaigns cleaned up
        """
        try:
            with get_redis_context() as redis_client:
                cleaned_count = 0

                # Get all campaign data keys
                pattern = "campaign:*:data"
                keys = redis_client.keys(pattern)

                for key in keys:
                    # Check if key has expired
                    ttl = redis_client.ttl(key)
                    if ttl == -2:  # Key doesn't exist
                        continue
                    elif ttl == -1:  # No TTL set, clean it up
                        redis_client.delete(key)
                        cleaned_count += 1
                    elif ttl == 0:  # Key has expired
                        redis_client.delete(key)
                        cleaned_count += 1

                logger.info(f"Cleaned up {cleaned_count} expired campaign entries")
                return cleaned_count
        except RedisError as e:
            logger.error(f"Failed to cleanup expired campaigns: {e}")
            return 0


# Global campaign tracker instance
campaign_tracker = CampaignTracker()


def get_campaign_tracker() -> CampaignTracker:
    """Get campaign tracker instance.

    Returns:
        CampaignTracker: Campaign tracker instance
    """
    return campaign_tracker
