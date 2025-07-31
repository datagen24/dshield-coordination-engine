"""Database package for DShield Coordination Engine.

This package contains the database models, schemas, repositories, and migrations
for the multi-database architecture (PostgreSQL, Redis, Elasticsearch, MISP).
"""

from .cache import cache_manager, get_cache_manager
from .campaign_tracking import campaign_tracker, get_campaign_tracker
from .connection import check_database_health, get_database_session, get_engine_info
from .models import (
    AnalysisResult,
    AnalysisSession,
    APIKey,
    APIUsageLog,
    AttackSession,
    AuditLog,
    Campaign,
    CampaignIndicator,
    CampaignSession,
    ToolExecutionLog,
)
from .rate_limiting import get_rate_limiter, rate_limiter
from .redis_client import (
    check_redis_health,
    get_redis_client,
    get_redis_context,
    get_redis_info,
    get_redis_memory_usage,
    redis_manager,
)
from .workflow_state import get_workflow_state_manager, workflow_state_manager

__all__ = [
    # Database connection
    "get_database_session",
    "check_database_health",
    "get_engine_info",
    # Database models
    "AnalysisSession",
    "Campaign",
    "CampaignSession",
    "CampaignIndicator",
    "AttackSession",
    "AnalysisResult",
    "ToolExecutionLog",
    "APIKey",
    "APIUsageLog",
    "AuditLog",
    # Redis client
    "get_redis_client",
    "get_redis_context",
    "check_redis_health",
    "get_redis_info",
    "get_redis_memory_usage",
    "redis_manager",
    # Cache management
    "get_cache_manager",
    "cache_manager",
    # Workflow state management
    "get_workflow_state_manager",
    "workflow_state_manager",
    # Rate limiting
    "get_rate_limiter",
    "rate_limiter",
    # Campaign tracking
    "get_campaign_tracker",
    "campaign_tracker",
]
