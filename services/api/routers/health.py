"""Health check endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "dshield-coordination-engine",
        "version": "0.1.0"
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check for Kubernetes."""
    try:
        # Add dependency checks here (database, redis, etc.)
        return {
            "status": "ready",
            "service": "dshield-coordination-engine"
        }
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """Liveness check for Kubernetes."""
    return {
        "status": "alive",
        "service": "dshield-coordination-engine"
    } 