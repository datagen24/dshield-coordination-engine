"""Unit tests for API configuration."""

from unittest.mock import Mock, patch

from services.api.config import Settings


class TestSettings:
    """Test the Settings class."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()

        # API Configuration
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000
        assert settings.api_workers == 4
        assert settings.api_reload is False
        assert settings.api_log_level == "info"

        # Security Configuration
        assert settings.secret_key == "your-secret-key-here-change-this-in-production"
        assert settings.algorithm == "HS256"
        assert settings.access_token_expire_minutes == 30

        # API Authentication
        assert settings.api_key_header == "X-API-Key"
        assert settings.api_key == "your-api-key-here-change-this-in-production"

        # CORS Settings
        assert settings.allowed_origins == [
            "http://localhost:3000",
            "http://localhost:8080",
        ]
        assert settings.allowed_methods == ["GET", "POST", "PUT", "DELETE"]
        assert settings.allowed_headers == ["*"]

        # Database Configuration
        assert (
            settings.database_url
            == "postgresql://user:password@localhost:5432/coordination"
        )
        assert settings.database_pool_size == 10
        assert settings.database_max_overflow == 20
        assert settings.database_pool_timeout == 30

        # Redis Configuration
        assert settings.redis_url == "redis://localhost:6379/0"
        assert settings.redis_password == ""
        assert settings.redis_db == 0
        assert settings.redis_max_connections == 20

        # Elasticsearch Configuration
        assert settings.elasticsearch_url == "http://localhost:9200"
        assert settings.elasticsearch_username == ""
        assert settings.elasticsearch_password == ""
        assert settings.elasticsearch_index_prefix == "dshield"
        assert settings.elasticsearch_timeout == 30

        # LLM Configuration
        assert settings.llm_service_url == "http://localhost:11434"
        assert settings.llm_model == "llama-3.1-8b-instruct"
        assert settings.llm_fallback_model == "mistral-7b-instruct"
        assert settings.llm_timeout == 300
        assert settings.llm_max_tokens == 4096
        assert settings.llm_temperature == 0.1

        # Analysis Configuration
        assert settings.analysis_timeout_seconds == 300
        assert settings.analysis_max_sessions == 1000
        assert settings.analysis_confidence_threshold == 0.7
        assert settings.analysis_temporal_window_seconds == 300
        assert settings.analysis_batch_size == 100

        # Development Configuration
        assert settings.debug is False
        assert settings.environment == "production"
        assert settings.enable_swagger_ui is True
        assert settings.enable_redoc is True

        # Performance Configuration
        assert settings.max_memory_mb == 16000
        assert settings.max_cpu_percent == 80
        assert settings.worker_processes == 4
        assert settings.worker_threads == 2

    def test_parse_list_fields_with_string(self):
        """Test parse_list_fields with string input."""
        # Test with valid JSON string
        json_string = '["http://localhost:3000", "http://localhost:8080"]'
        result = Settings.parse_list_fields(json_string)
        assert result == ["http://localhost:3000", "http://localhost:8080"]

        # Test with invalid JSON string (should return single item list)
        invalid_string = "invalid-json"
        result = Settings.parse_list_fields(invalid_string)
        assert result == ["invalid-json"]

        # Test with non-list JSON (should return single item list)
        non_list_json = '"single-item"'
        result = Settings.parse_list_fields(non_list_json)
        assert result == ['"single-item"']  # JSON string is preserved as-is

    def test_parse_list_fields_with_list(self):
        """Test parse_list_fields with list input."""
        input_list = ["item1", "item2", "item3"]
        result = Settings.parse_list_fields(input_list)
        assert result == input_list

    def test_set_debug_defaults_true(self):
        """Test set_debug_defaults with debug=True."""
        info = Mock()
        info.data = {"enable_swagger_ui": False, "enable_redoc": False}

        result = Settings.set_debug_defaults(True, info)

        assert result is True
        assert info.data["enable_swagger_ui"] is True
        assert info.data["enable_redoc"] is True

    def test_set_debug_defaults_false(self):
        """Test set_debug_defaults with debug=False."""
        info = Mock()
        info.data = {"enable_swagger_ui": True, "enable_redoc": True}

        result = Settings.set_debug_defaults(False, info)

        assert result is False
        # Should not change existing values
        assert info.data["enable_swagger_ui"] is True
        assert info.data["enable_redoc"] is True

    @patch.dict(
        "os.environ",
        {
            "API_HOST": "127.0.0.1",
            "API_PORT": "9000",
            "DEBUG": "true",
            "ALLOWED_ORIGINS": '["https://example.com", "https://test.com"]',
        },
    )
    def test_settings_from_environment(self):
        """Test settings loaded from environment variables."""
        settings = Settings()

        assert settings.api_host == "127.0.0.1"
        assert settings.api_port == 9000
        assert settings.debug is True
        assert settings.allowed_origins == ["https://example.com", "https://test.com"]

    def test_model_config(self):
        """Test model configuration."""
        settings = Settings()

        # Test that model_config exists and has expected structure
        assert hasattr(settings, "model_config")
        assert isinstance(settings.model_config, dict)


class TestSettingsValidation:
    """Test settings validation."""

    def test_parse_list_fields_edge_cases(self):
        """Test parse_list_fields with edge cases."""
        # Test with empty string
        result = Settings.parse_list_fields("")
        assert result == [""]

        # Test with empty list
        result = Settings.parse_list_fields([])
        assert result == []

    def test_set_debug_defaults_edge_cases(self):
        """Test set_debug_defaults with edge cases."""
        info = Mock()
        info.data = {}

        # Test with True
        result = Settings.set_debug_defaults(True, info)
        assert result is True
        assert info.data["enable_swagger_ui"] is True
        assert info.data["enable_redoc"] is True

        # Test with False
        info.data = {}
        result = Settings.set_debug_defaults(False, info)
        assert result is False
        # Should not set defaults for False
        assert "enable_swagger_ui" not in info.data
        assert "enable_redoc" not in info.data
