"""Unit tests for API authentication."""

from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from services.api.auth import get_current_user, verify_api_key


class TestVerifyApiKey:
    """Test API key verification."""

    @pytest.mark.asyncio
    async def test_verify_api_key_debug_mode(self):
        """Test API key verification in debug mode."""
        from unittest.mock import patch
        with patch("services.api.auth.settings") as mock_settings:
            mock_settings.debug = True
            request = Mock()
            request.headers = {}

            result = await verify_api_key(request)
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_api_key_missing_key(self):
        """Test API key verification with missing key."""
        request = Mock()
        request.headers = {}
        request.client.host = "127.0.0.1"

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(request)

        assert exc_info.value.status_code == 401
        assert "Missing API key" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_verify_api_key_invalid_key(self):
        """Test API key verification with invalid key."""
        request = Mock()
        request.headers = {"X-API-Key": "invalid-key"}
        request.client.host = "127.0.0.1"

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(request)

        assert exc_info.value.status_code == 401
        assert "Invalid API key" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_verify_api_key_valid_key(self):
        """Test API key verification with valid key."""
        from unittest.mock import patch
        with patch("services.api.auth.settings") as mock_settings:
            mock_settings.debug = False
            mock_settings.api_key = "valid-key"
            mock_settings.api_key_header = "X-API-Key"
            request = Mock()
            request.headers = {"X-API-Key": "valid-key"}
            request.client.host = "127.0.0.1"

            result = await verify_api_key(request)
            assert result is True


class TestGetCurrentUser:
    """Test current user retrieval."""

    def test_get_current_user_with_client(self):
        """Test getting current user with client IP."""
        request = Mock()
        request.client.host = "192.168.1.100"

        result = get_current_user(request)
        assert result == "192.168.1.100"

    def test_get_current_user_without_client(self):
        """Test getting current user without client."""
        request = Mock()
        request.client = None

        result = get_current_user(request)
        assert result == "unknown"
