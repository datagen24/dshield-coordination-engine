"""Worker Service for DShield Coordination Engine.

This module provides background worker processes for coordination analysis,
including Celery task management and asynchronous processing capabilities.

The worker service supports:
- Background task processing
- Celery task queue management
- Asynchronous coordination analysis
- Result storage and retrieval
- Error handling and retry logic
"""

__version__ = "0.1.0"
__author__ = "DShield Team"
__email__ = "team@dshield.org"

from .celery_app import celery_app
from .tasks import (
    analyze_coordination_task,
    enrich_attack_sessions_task,
    process_bulk_analysis_task,
)

__all__ = [
    "celery_app",
    "analyze_coordination_task",
    "process_bulk_analysis_task",
    "enrich_attack_sessions_task",
]
