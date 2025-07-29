"""Pytest configuration and common fixtures."""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from services.api.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def sample_attack_sessions() -> list:
    """Sample attack sessions for testing."""
    return [
        {
            "source_ip": "192.168.1.1",
            "timestamp": "2025-01-28T10:00:00Z",
            "payload": "test attack payload 1",
            "target_port": 22,
            "protocol": "ssh"
        },
        {
            "source_ip": "192.168.1.2",
            "timestamp": "2025-01-28T10:05:00Z",
            "payload": "test attack payload 2",
            "target_port": 22,
            "protocol": "ssh"
        },
        {
            "source_ip": "192.168.1.3",
            "timestamp": "2025-01-28T10:10:00Z",
            "payload": "test attack payload 3",
            "target_port": 80,
            "protocol": "http"
        }
    ]


@pytest.fixture
def sample_coordination_request(sample_attack_sessions) -> Dict[str, Any]:
    """Sample coordination analysis request."""
    return {
        "attack_sessions": sample_attack_sessions,
        "analysis_depth": "standard",
        "callback_url": None
    }


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch("services.api.config.settings") as mock:
        mock.debug = True
        mock.api_key = "test-api-key"
        mock.api_key_header = "X-API-Key"
        yield mock


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    with patch("structlog.get_logger") as mock:
        yield mock


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch("redis.Redis") as mock:
        mock.return_value.ping.return_value = True
        yield mock


@pytest.fixture
def mock_postgres():
    """Mock PostgreSQL connection."""
    with patch("sqlalchemy.create_engine") as mock:
        yield mock


@pytest.fixture
def mock_elasticsearch():
    """Mock Elasticsearch client."""
    with patch("elasticsearch.Elasticsearch") as mock:
        mock.return_value.ping.return_value = True
        yield mock


@pytest.fixture
def mock_llm_service():
    """Mock LLM service."""
    with patch("httpx.AsyncClient") as mock:
        mock.return_value.post.return_value.json.return_value = {
            "response": "test response"
        }
        yield mock


@pytest.fixture
def sample_analysis_result() -> Dict[str, Any]:
    """Sample analysis result for testing."""
    return {
        "analysis_id": "test-analysis-id",
        "status": "completed",
        "coordination_confidence": 0.75,
        "evidence": {
            "temporal_correlation": 0.8,
            "behavioral_similarity": 0.7,
            "infrastructure_clustering": 0.6
        },
        "enrichment_applied": True
    }


# Markers for different test types
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "security: Security tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    ) 