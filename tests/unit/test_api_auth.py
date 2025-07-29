"""Unit tests for API authentication."""

import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch

from services.api.auth import verify_api_key, get_current_user


class TestVerifyAPIKey:
    """Test API key verification."""

    @pytest.mark.unit
    def test_verify_api_key_debug_mode(self, mock_settings):
        """Test API key verification in debug mode."""
        mock_settings.debug = True
        request = Mock()
        request.headers = {}
        
        result = verify_api_key(request)
        assert result is True

    @pytest.mark.unit
    def test_verify_api_key_missing_key(self, mock_settings):
        """Test API key verification with missing key."""
        mock_settings.debug = False
        mock_settings.api_key_header = "X-API-Key"
        request = Mock()
        request.headers = {}
        request.client.host = "127.0.0.1"
        
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(request)
        
        assert exc_info.value.status_code == 401
        assert "Missing API key" in str(exc_info.value.detail)

    @pytest.mark.unit
    def test_verify_api_key_invalid_key(self, mock_settings):
        """Test API key verification with invalid key."""
        mock_settings.debug = False
        mock_settings.api_key_header = "X-API-Key"
        mock_settings.api_key = "valid-key"
        request = Mock()
        request.headers = {"X-API-Key": "invalid-key"}
        request.client.host = "127.0.0.1"
        
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(request)
        
        assert exc_info.value.status_code == 401
        assert "Invalid API key" in str(exc_info.value.detail)

    @pytest.mark.unit
    def test_verify_api_key_valid_key(self, mock_settings):
        """Test API key verification with valid key."""
        mock_settings.debug = False
        mock_settings.api_key_header = "X-API-Key"
        mock_settings.api_key = "valid-key"
        request = Mock()
        request.headers = {"X-API-Key": "valid-key"}
        request.client.host = "127.0.0.1"
        
        result = verify_api_key(request)
        assert result is True


class TestGetCurrentUser:
    """Test current user extraction."""

    @pytest.mark.unit
    def test_get_current_user_with_client(self):
        """Test getting current user with client IP."""
        request = Mock()
        request.client.host = "192.168.1.100"
        
        result = get_current_user(request)
        assert result == "192.168.1.100"

    @pytest.mark.unit
    def test_get_current_user_without_client(self):
        """Test getting current user without client."""
        request = Mock()
        request.client = None
        
        result = get_current_user(request)
        assert result == "unknown" 