"""Pytest configuration and common fixtures."""

from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from services.api.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_attack_sessions() -> list[dict[str, Any]]:
    """Sample attack sessions for testing."""
    return [
        {
            "source_ip": "192.168.1.1",
            "timestamp": "2025-07-28T10:00:00Z",
            "payload": "test attack payload 1",
            "target_port": 22,
            "protocol": "SSH",
        },
        {
            "source_ip": "192.168.1.2",
            "timestamp": "2025-07-28T10:05:00Z",
            "payload": "test attack payload 2",
            "target_port": 80,
            "protocol": "HTTP",
        },
        {
            "source_ip": "192.168.1.3",
            "timestamp": "2025-07-28T10:10:00Z",
            "payload": "test attack payload 3",
            "target_port": 443,
            "protocol": "HTTPS",
        },
    ]


@pytest.fixture
def sample_coordination_request(sample_attack_sessions) -> dict[str, Any]:
    """Sample coordination analysis request."""
    return {
        "attack_sessions": sample_attack_sessions,
        "analysis_depth": "standard",
        "callback_url": "http://example.com/callback",
    }


@pytest.fixture
def sample_analysis_result() -> dict[str, Any]:
    """Sample analysis result for testing."""
    return {
        "analysis_id": "test-analysis-id",
        "status": "completed",
        "coordination_confidence": 0.75,
        "evidence": {
            "temporal_correlation": 0.8,
            "behavioral_similarity": 0.7,
            "infrastructure_clustering": 0.6,
        },
        "enrichment_applied": True,
    }


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch("services.api.routers.coordination.settings") as mock:
        mock.analysis_max_sessions = 1000
        yield mock


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
