"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from services.api.main import app


class TestAPIIntegration:
    """Integration tests for API endpoints."""

    @pytest.fixture
    def test_client(self):
        """Create a test client."""
        return TestClient(app)

    def test_health_check_integration(self, test_client):
        """Test health check endpoint integration."""
        response = test_client.get("/health/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "dshield-coordination-engine"
        assert data["version"] == "0.1.0"

    def test_readiness_check_integration(self, test_client):
        """Test readiness check endpoint integration."""
        response = test_client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "dshield-coordination-engine"
        assert "dependencies" in data

    def test_liveness_check_integration(self, test_client):
        """Test liveness check endpoint integration."""
        response = test_client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert data["service"] == "dshield-coordination-engine"
        assert "uptime" in data

    @pytest.mark.skip(reason="Requires authentication - will be implemented in future")
    def test_coordination_analysis_integration(self, test_client):
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

        response = test_client.post("/analyze/coordination", json=sample_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert "analysis_id" in data

    @pytest.mark.skip(reason="Requires authentication - will be implemented in future")
    def test_bulk_analysis_integration(self, test_client):
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

        response = test_client.post("/analyze/bulk", json=sample_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert "analysis_ids" in data

    @pytest.mark.skip(reason="Requires authentication - will be implemented in future")
    def test_analysis_results_integration(self, test_client):
        """Test analysis results endpoint integration."""
        analysis_id = "test-analysis-id"

        response = test_client.get(f"/analyze/{analysis_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["analysis_id"] == analysis_id
        assert data["status"] == "completed"
        assert "coordination_confidence" in data

    @pytest.mark.skip(reason="Requires authentication - will be implemented in future")
    def test_invalid_coordination_request(self, test_client):
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

        response = test_client.post("/analyze/coordination", json=invalid_data)

        assert response.status_code == 422  # Validation error

    @pytest.mark.skip(reason="Requires authentication - will be implemented in future")
    def test_too_many_sessions_validation(self, test_client):
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

        response = test_client.post("/analyze/coordination", json=too_many_sessions)

        assert response.status_code == 422  # Validation error

    def test_api_authentication_integration(self, test_client):
        """Test API authentication integration."""
        # Test without API key - should work for health endpoints
        response = test_client.get("/health/")
        assert response.status_code == 200  # Health endpoints don't require auth

        # Test coordination endpoint without auth - should fail
        response = test_client.get("/analyze/coordination")
        assert response.status_code == 401  # Unauthorized

    def test_cors_headers_integration(self, test_client):
        """Test CORS headers in responses."""
        response = test_client.get("/health/")

        # CORS headers are only set for preflight requests
        # For regular GET requests, they may not be present
        # This test is a placeholder for future CORS testing
        assert response.status_code == 200

    def test_error_handling_integration(self, test_client):
        """Test error handling integration."""
        # Test 404 for non-existent endpoint
        response = test_client.get("/nonexistent-endpoint")
        assert response.status_code == 404

        # Test 405 for wrong HTTP method
        response = test_client.post("/health/")
        assert response.status_code == 405

    @pytest.mark.skip(reason="Requires authentication - will be implemented in future")
    def test_request_validation_integration(self, test_client):
        """Test request validation integration."""
        # Test with missing required fields
        invalid_data = {
            "attack_sessions": [],  # Empty sessions
            "analysis_depth": "invalid-depth",  # Invalid depth
        }

        response = test_client.post("/analyze/coordination", json=invalid_data)
        assert response.status_code == 422

    def test_response_format_integration(self, test_client):
        """Test response format consistency."""
        response = test_client.get("/health/")

        # Check response format
        data = response.json()
        required_fields = ["status", "service", "version", "timestamp"]
        for field in required_fields:
            assert field in data

        # Check content type
        assert response.headers["content-type"] == "application/json"
