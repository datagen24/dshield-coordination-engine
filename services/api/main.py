"""DShield Coordination Engine API Service.

This module provides the main FastAPI application for the DShield Coordination Engine,
a cybersecurity research tool for analyzing attack coordination patterns.

The API provides endpoints for:
- Health monitoring and readiness checks
- Coordination analysis of attack sessions
- Bulk analysis capabilities
- Real-time status monitoring

For detailed API documentation, visit:
- Swagger UI: /docs
- ReDoc: /redoc
- OpenAPI JSON: /openapi.json
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from typing import Any

import structlog

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer

from services.api.config import settings
from services.api.auth import verify_api_key
from services.api.routers import coordination, health

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Security
security = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    Logs application lifecycle events for monitoring and debugging.
    """
    logger.info("Starting DShield Coordination Engine API")
    yield
    logger.info("Shutting down DShield Coordination Engine API")


def custom_openapi() -> dict[str, Any]:
    """Generate custom OpenAPI schema with enhanced documentation.

    Returns:
        Dict[str, Any]: Custom OpenAPI schema with additional metadata
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="DShield Coordination Engine API",
        version="0.1.0",
        description="""
# DShield Coordination Engine API

AI-powered attack coordination detection service for cybersecurity research and analysis.

## Overview

The DShield Coordination Engine analyzes attack patterns from honeypot data to distinguish between coordinated campaigns and coincidental timing. This addresses critical academic and operational needs for evidence-based attribution in cybersecurity research.

## Key Features

- **Temporal Correlation Analysis**: Detect timing patterns with statistical significance testing
- **Behavioral Clustering**: Group attacks by TTP similarity with confidence scores
- **Infrastructure Relationship Mapping**: Analyze IP/ASN relationships, geographic clustering
- **Coordination Confidence Scoring**: Provide 0-1 confidence score with evidence breakdown
- **Academic Credibility**: Reproducible analysis with documented methodology

## Authentication

All API endpoints require authentication using API keys. Include your API key in the request header:

```
X-API-Key: your-api-key-here
```

## Rate Limiting

API requests are rate-limited to ensure fair usage and system stability. Current limits:
- 100 requests per minute per API key
- 1000 requests per hour per API key

## Error Handling

The API uses standard HTTP status codes and returns detailed error messages in JSON format:

```json
{
  "detail": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-07-28T10:00:00Z"
}
```

## Common Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid API key
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Getting Started

1. Obtain an API key from your administrator
2. Include the API key in all requests
3. Submit attack session data for analysis
4. Monitor analysis status and retrieve results

For detailed usage examples, see the individual endpoint documentation below.
        """,
        routes=app.routes,
    )

    # Add custom metadata
    openapi_schema["info"]["contact"] = {
        "name": "DShield Team",
        "email": "team@dshield.org",
        "url": "https://dshield.org",
    }
    openapi_schema["info"]["license"] = {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    }
    openapi_schema["info"]["x-logo"] = {"url": "https://dshield.org/logo.png"}

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication",
        }
    }

    # Add global security requirement
    openapi_schema["security"] = [{"ApiKeyAuth": []}]

    # Add server information
    openapi_schema["servers"] = [
        {"url": "http://localhost:8000", "description": "Development server"},
        {"url": "https://api.dshield.org", "description": "Production server"},
    ]

    # Add tags metadata
    openapi_schema["tags"] = [
        {
            "name": "health",
            "description": "Health monitoring and readiness checks",
            "externalDocs": {
                "description": "Health Check Documentation",
                "url": "https://dshield.org/docs/health",
            },
        },
        {
            "name": "coordination",
            "description": "Attack coordination analysis endpoints",
            "externalDocs": {
                "description": "Coordination Analysis Documentation",
                "url": "https://dshield.org/docs/coordination",
            },
        },
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title="DShield Coordination Engine API",
        description="AI-powered attack coordination detection service for cybersecurity research",
        version="0.1.0",
        docs_url="/docs" if settings.enable_swagger_ui else None,
        redoc_url="/redoc" if settings.enable_redoc else None,
        lifespan=lifespan,
        openapi_url="/openapi.json",
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,
            "defaultModelExpandDepth": 2,
            "docExpansion": "list",
            "filter": True,
            "showExtensions": True,
            "showCommonExtensions": True,
        },
    )

    # Set custom OpenAPI schema
    app.openapi = lambda: custom_openapi()

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
    )

    # Include routers
    app.include_router(
        health.router,
        prefix="/health",
        tags=["health"],
    )

    app.include_router(
        coordination.router,
        prefix="/analyze",
        tags=["coordination"],
        dependencies=[Depends(verify_api_key)] if not settings.debug else [],
    )

    return app


# Create the application instance
app = create_app()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> HTTPException:
    """Global exception handler for unhandled exceptions.

    Args:
        request: The incoming request
        exc: The unhandled exception

    Returns:
        HTTPException: Standardized error response
    """
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        path=request.url.path,
        method=request.method,
    )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "services.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.api_log_level,
    )
