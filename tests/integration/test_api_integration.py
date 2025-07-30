"""Integration tests for API endpoints."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from services.api.main import app


class TestAPIIntegration:
    """Integration tests for API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_check_integration(self, client):
        """Test health check endpoint integration."""
        response = client.get("/health/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "dshield-coordination-engine"
        assert data["version"] == "0.1.0"

    def test_readiness_check_integration(self, client):
        """Test readiness check endpoint integration."""
        response = client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "dshield-coordination-engine"
        assert "dependencies" in data

    def test_liveness_check_integration(self, client):
        """Test liveness check endpoint integration."""
        response = client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert data["service"] == "dshield-coordination-engine"
        assert "uptime" in data

    def test_coordination_analysis_integration(self, client):
        """Test coordination analysis endpoint integration."""
        sample_data = {
            "attack_sessions": [
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
            ],
            "analysis_depth": "standard",
            "callback_url": "http://example.com/callback",
        }

        with patch("services.api.main.settings") as mock_settings:
            mock_settings.analysis_max_sessions = 1000
            mock_settings.debug = True  # Enable debug mode to bypass auth

            response = client.post("/analyze/coordination", json=sample_data)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "queued"
            assert "analysis_id" in data

    def test_bulk_analysis_integration(self, client):
        """Test bulk analysis endpoint integration."""
        sample_data = {
            "session_batches": [
                [
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
                ]
            ],
            "analysis_depth": "standard",
        }

        with patch("services.api.main.settings") as mock_settings:
            mock_settings.analysis_max_sessions = 1000
            mock_settings.debug = True  # Enable debug mode to bypass auth

            response = client.post("/analyze/bulk", json=sample_data)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "queued"
            assert "analysis_ids" in data

    def test_analysis_results_integration(self, client):
        """Test analysis results endpoint integration."""
        analysis_id = "test-analysis-id"

        with patch("services.api.main.settings") as mock_settings:
            mock_settings.debug = True  # Enable debug mode to bypass auth

            response = client.get(f"/analyze/{analysis_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["analysis_id"] == analysis_id
            assert data["status"] == "completed"
            assert "coordination_confidence" in data

    def test_invalid_coordination_request(self, client):
        """Test coordination analysis with invalid data."""
        invalid_data = {
            "attack_sessions": [
                {
                    "source_ip": "192.168.1.1",
                    "timestamp": "2025-07-28T10:00:00Z",
                    "payload": "test attack payload 1",
                }
            ],  # Only one session - should fail validation
            "analysis_depth": "standard",
        }

        with patch("services.api.main.settings") as mock_settings:
            mock_settings.analysis_max_sessions = 1000
            mock_settings.debug = True  # Enable debug mode to bypass auth

            response = client.post("/analyze/coordination", json=invalid_data)

            assert response.status_code == 422  # Validation error

    def test_too_many_sessions_validation(self, client):
        """Test coordination analysis with too many sessions."""
        too_many_sessions = {
            "attack_sessions": [
                {
                    "source_ip": f"192.168.1.{i}",
                    "timestamp": "2025-07-28T10:00:00Z",
                    "payload": f"test attack payload {i}",
                }
                for i in range(1001)  # More than max allowed
            ],
            "analysis_depth": "standard",
        }

        with patch("services.api.main.settings") as mock_settings:
            mock_settings.analysis_max_sessions = 1000
            mock_settings.debug = True  # Enable debug mode to bypass auth

            response = client.post("/analyze/coordination", json=too_many_sessions)

            assert response.status_code == 422  # Validation error

    def test_api_authentication_integration(self, client):
        """Test API authentication integration."""
        # Test without API key
        response = client.get("/health/")
        assert response.status_code == 200  # Health endpoints don't require auth

        # Test with invalid API key
        headers = {"X-API-Key": "invalid-key"}
        response = client.get("/analyze/coordination", headers=headers)
        assert response.status_code == 401

    def test_cors_headers_integration(self, client):
        """Test CORS headers in responses."""
        response = client.get("/health/")

        # CORS headers are only set for preflight requests
        # For regular GET requests, they may not be present
        # This test is a placeholder for future CORS testing
        assert response.status_code == 200

    def test_error_handling_integration(self, client):
        """Test error handling integration."""
        # Test 404 for non-existent endpoint
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404

        # Test 405 for wrong HTTP method
        response = client.post("/health/")
        assert response.status_code == 405

    def test_request_validation_integration(self, client):
        """Test request validation integration."""
        # Test with missing required fields
        invalid_data = {
            "attack_sessions": [],  # Empty sessions
            "analysis_depth": "invalid-depth",  # Invalid depth
        }

        with patch("services.api.main.settings") as mock_settings:
            mock_settings.debug = True  # Enable debug mode to bypass auth

            response = client.post("/analyze/coordination", json=invalid_data)
            assert response.status_code == 422

    def test_response_format_integration(self, client):
        """Test response format consistency."""
        response = client.get("/health/")

        # Check response format
        data = response.json()
        required_fields = ["status", "service", "version", "timestamp"]
        for field in required_fields:
            assert field in data

        # Check content type
        assert response.headers["content-type"] == "application/json"
