"""Database package for DShield Coordination Engine.

This package contains the database models, schemas, repositories, and migrations
for the multi-database architecture (PostgreSQL, Redis, Elasticsearch, MISP).
"""

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

__all__ = [
    "get_database_session",
    "check_database_health",
    "get_engine_info",
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
]
