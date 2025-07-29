"""Authentication utilities for the DShield Coordination Engine API."""

import structlog
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer

from services.api.config import settings

logger = structlog.get_logger(__name__)
security = HTTPBearer(auto_error=False)


async def verify_api_key(request: Request) -> bool:
    """Verify API key from request headers."""
    # Skip authentication in debug mode
    if settings.debug:
        return True

    # Get API key from header
    api_key = request.headers.get(settings.api_key_header)

    if not api_key:
        logger.warning("Missing API key", client_ip=request.client.host)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify API key
    if api_key != settings.api_key:
        logger.warning(
            "Invalid API key",
            client_ip=request.client.host,
            provided_key=api_key[:8] + "..." if len(api_key) > 8 else "***"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("API key verified", client_ip=request.client.host)
    return True


def get_current_user(request: Request) -> str:
    """Get current user identifier from request."""
    # For now, return client IP as user identifier
    # In a real implementation, this would extract user info from JWT token
    return request.client.host if request.client else "unknown"
