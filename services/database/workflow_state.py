"""Workflow state management for DShield Coordination Engine."""

import json
import logging
from datetime import datetime
from typing import Any

from redis.exceptions import RedisError

from services.database.redis_client import get_redis_context

logger = logging.getLogger(__name__)

# Workflow state TTL (1 hour)
WORKFLOW_STATE_TTL = 3600

# State key prefixes
STATE_PREFIXES = {
    "workflow": "workflow:state",
    "progress": "workflow:progress",
    "checkpoint": "workflow:checkpoint",
    "error": "workflow:error",
    "metadata": "workflow:metadata",
}


class WorkflowStateManager:
    """Manages workflow state persistence and recovery."""

    def __init__(self):
        self.default_ttl = WORKFLOW_STATE_TTL

    def _make_key(self, prefix: str, workflow_id: str, suffix: str = "") -> str:
        """Create a workflow state key.

        Args:
            prefix: Key prefix
            workflow_id: Workflow ID
            suffix: Optional suffix

        Returns:
            str: Formatted state key
        """
        if suffix:
            return f"{prefix}:{workflow_id}:{suffix}"
        return f"{prefix}:{workflow_id}"

    def _serialize_state(self, state: dict[str, Any]) -> str:
        """Serialize workflow state for Redis storage.

        Args:
            state: Workflow state data

        Returns:
            str: Serialized state
        """
        return json.dumps(state, default=str)

    def _deserialize_state(self, state_data: str) -> dict[str, Any]:
        """Deserialize workflow state from Redis storage.

        Args:
            state_data: Serialized state data

        Returns:
            Dict[str, Any]: Deserialized state
        """
        try:
            return json.loads(state_data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to deserialize workflow state: {e}")
            return {}

    def save_workflow_state(
        self, workflow_id: str, state: dict[str, Any], ttl: int | None = None
    ) -> bool:
        """Save workflow state to Redis.

        Args:
            workflow_id: Workflow ID
            state: Workflow state data
            ttl: Optional TTL override

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(STATE_PREFIXES["workflow"], workflow_id)
                serialized_state = self._serialize_state(state)
                ttl_value = ttl or self.default_ttl

                redis_client.setex(key, ttl_value, serialized_state)
                logger.debug(f"Saved workflow state for workflow {workflow_id}")
                return True
        except RedisError as e:
            logger.error(f"Failed to save workflow state: {e}")
            return False

    def get_workflow_state(self, workflow_id: str) -> dict[str, Any] | None:
        """Retrieve workflow state from Redis.

        Args:
            workflow_id: Workflow ID

        Returns:
            Optional[Dict[str, Any]]: Workflow state or None
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(STATE_PREFIXES["workflow"], workflow_id)
                state_data = redis_client.get(key)

                if state_data:
                    return self._deserialize_state(state_data)
                return None
        except RedisError as e:
            logger.error(f"Failed to retrieve workflow state: {e}")
            return None

    def update_workflow_progress(
        self, workflow_id: str, progress: dict[str, Any]
    ) -> bool:
        """Update workflow progress.

        Args:
            workflow_id: Workflow ID
            progress: Progress data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(STATE_PREFIXES["progress"], workflow_id)
                serialized_progress = self._serialize_state(progress)

                redis_client.setex(key, self.default_ttl, serialized_progress)
                logger.debug(f"Updated progress for workflow {workflow_id}")
                return True
        except RedisError as e:
            logger.error(f"Failed to update workflow progress: {e}")
            return False

    def get_workflow_progress(self, workflow_id: str) -> dict[str, Any] | None:
        """Retrieve workflow progress.

        Args:
            workflow_id: Workflow ID

        Returns:
            Optional[Dict[str, Any]]: Progress data or None
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(STATE_PREFIXES["progress"], workflow_id)
                progress_data = redis_client.get(key)

                if progress_data:
                    return self._deserialize_state(progress_data)
                return None
        except RedisError as e:
            logger.error(f"Failed to retrieve workflow progress: {e}")
            return None

    def create_checkpoint(
        self, workflow_id: str, checkpoint_data: dict[str, Any]
    ) -> bool:
        """Create a workflow checkpoint.

        Args:
            workflow_id: Workflow ID
            checkpoint_data: Checkpoint data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                # Add timestamp to checkpoint
                checkpoint_data["timestamp"] = datetime.utcnow().isoformat()

                key = self._make_key(STATE_PREFIXES["checkpoint"], workflow_id)
                serialized_checkpoint = self._serialize_state(checkpoint_data)

                redis_client.setex(key, self.default_ttl, serialized_checkpoint)
                logger.debug(f"Created checkpoint for workflow {workflow_id}")
                return True
        except RedisError as e:
            logger.error(f"Failed to create workflow checkpoint: {e}")
            return False

    def get_checkpoint(self, workflow_id: str) -> dict[str, Any] | None:
        """Retrieve workflow checkpoint.

        Args:
            workflow_id: Workflow ID

        Returns:
            Optional[Dict[str, Any]]: Checkpoint data or None
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(STATE_PREFIXES["checkpoint"], workflow_id)
                checkpoint_data = redis_client.get(key)

                if checkpoint_data:
                    return self._deserialize_state(checkpoint_data)
                return None
        except RedisError as e:
            logger.error(f"Failed to retrieve workflow checkpoint: {e}")
            return None

    def save_error_state(self, workflow_id: str, error_data: dict[str, Any]) -> bool:
        """Save workflow error state.

        Args:
            workflow_id: Workflow ID
            error_data: Error information

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                # Add timestamp to error
                error_data["timestamp"] = datetime.utcnow().isoformat()

                key = self._make_key(STATE_PREFIXES["error"], workflow_id)
                serialized_error = self._serialize_state(error_data)

                # Error states have longer TTL for debugging
                redis_client.setex(key, self.default_ttl * 2, serialized_error)
                logger.debug(f"Saved error state for workflow {workflow_id}")
                return True
        except RedisError as e:
            logger.error(f"Failed to save error state: {e}")
            return False

    def get_error_state(self, workflow_id: str) -> dict[str, Any] | None:
        """Retrieve workflow error state.

        Args:
            workflow_id: Workflow ID

        Returns:
            Optional[Dict[str, Any]]: Error state or None
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(STATE_PREFIXES["error"], workflow_id)
                error_data = redis_client.get(key)

                if error_data:
                    return self._deserialize_state(error_data)
                return None
        except RedisError as e:
            logger.error(f"Failed to retrieve error state: {e}")
            return None

    def save_metadata(self, workflow_id: str, metadata: dict[str, Any]) -> bool:
        """Save workflow metadata.

        Args:
            workflow_id: Workflow ID
            metadata: Metadata information

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(STATE_PREFIXES["metadata"], workflow_id)
                serialized_metadata = self._serialize_state(metadata)

                redis_client.setex(key, self.default_ttl, serialized_metadata)
                logger.debug(f"Saved metadata for workflow {workflow_id}")
                return True
        except RedisError as e:
            logger.error(f"Failed to save metadata: {e}")
            return False

    def get_metadata(self, workflow_id: str) -> dict[str, Any] | None:
        """Retrieve workflow metadata.

        Args:
            workflow_id: Workflow ID

        Returns:
            Optional[Dict[str, Any]]: Metadata or None
        """
        try:
            with get_redis_context() as redis_client:
                key = self._make_key(STATE_PREFIXES["metadata"], workflow_id)
                metadata = redis_client.get(key)

                if metadata:
                    return self._deserialize_state(metadata)
                return None
        except RedisError as e:
            logger.error(f"Failed to retrieve metadata: {e}")
            return None

    def cleanup_workflow_state(self, workflow_id: str) -> bool:
        """Clean up all workflow state data.

        Args:
            workflow_id: Workflow ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_redis_context() as redis_client:
                # Delete all keys related to this workflow
                patterns = [
                    f"{STATE_PREFIXES['workflow']}:{workflow_id}",
                    f"{STATE_PREFIXES['progress']}:{workflow_id}",
                    f"{STATE_PREFIXES['checkpoint']}:{workflow_id}",
                    f"{STATE_PREFIXES['error']}:{workflow_id}",
                    f"{STATE_PREFIXES['metadata']}:{workflow_id}",
                ]

                deleted_count = 0
                for pattern in patterns:
                    keys = redis_client.keys(pattern)
                    if keys:
                        deleted = redis_client.delete(*keys)
                        deleted_count += deleted

                logger.debug(
                    f"Cleaned up {deleted_count} state keys for workflow {workflow_id}"
                )
                return True
        except RedisError as e:
            logger.error(f"Failed to cleanup workflow state: {e}")
            return False

    def get_active_workflows(self) -> list[str]:
        """Get list of active workflow IDs.

        Returns:
            List[str]: List of active workflow IDs
        """
        try:
            with get_redis_context() as redis_client:
                pattern = f"{STATE_PREFIXES['workflow']}:*"
                keys = redis_client.keys(pattern)

                # Extract workflow IDs from keys
                workflow_ids = []
                for key in keys:
                    # Extract ID from key like "workflow:state:workflow_id"
                    parts = key.split(":")
                    if len(parts) >= 3:
                        workflow_ids.append(parts[2])

                return list(set(workflow_ids))  # Remove duplicates
        except RedisError as e:
            logger.error(f"Failed to get active workflows: {e}")
            return []

    def get_workflow_stats(self) -> dict[str, Any]:
        """Get workflow state statistics.

        Returns:
            dict: Workflow statistics
        """
        try:
            with get_redis_context() as redis_client:
                stats = {}

                for prefix_name, prefix in STATE_PREFIXES.items():
                    pattern = f"{prefix}:*"
                    keys = redis_client.keys(pattern)
                    stats[f"{prefix_name}_count"] = len(keys)

                # Get active workflows
                active_workflows = self.get_active_workflows()
                stats["active_workflows"] = len(active_workflows)

                return stats
        except RedisError as e:
            logger.error(f"Failed to get workflow stats: {e}")
            return {"error": str(e)}

    def recover_workflow_state(self, workflow_id: str) -> dict[str, Any] | None:
        """Attempt to recover workflow state from checkpoint.

        Args:
            workflow_id: Workflow ID

        Returns:
            Optional[Dict[str, Any]]: Recovered state or None
        """
        try:
            # Try to get checkpoint first
            checkpoint = self.get_checkpoint(workflow_id)
            if checkpoint:
                logger.info(f"Recovered workflow {workflow_id} from checkpoint")
                return checkpoint

            # Fall back to current state
            state = self.get_workflow_state(workflow_id)
            if state:
                logger.info(f"Recovered workflow {workflow_id} from current state")
                return state

            logger.warning(f"No recovery data found for workflow {workflow_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to recover workflow state: {e}")
            return None


# Global workflow state manager instance
workflow_state_manager = WorkflowStateManager()


def get_workflow_state_manager() -> WorkflowStateManager:
    """Get workflow state manager instance.

    Returns:
        WorkflowStateManager: Workflow state manager instance
    """
    return workflow_state_manager
