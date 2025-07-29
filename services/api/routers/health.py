"""Health check endpoints."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/")
async def health_check() -> dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "dshield-coordination-engine",
        "version": "0.1.0",
    }


@router.get("/ready")
async def readiness_check() -> dict[str, Any]:
    """Readiness check for Kubernetes."""
    try:
        # Add dependency checks here (database, redis, etc.)
        return {"status": "ready", "service": "dshield-coordination-engine"}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready") from e


@router.get("/live")
async def liveness_check() -> dict[str, Any]:
    """Liveness check for Kubernetes."""
    return {"status": "alive", "service": "dshield-coordination-engine"}
