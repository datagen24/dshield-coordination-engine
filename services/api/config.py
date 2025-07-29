"""Configuration settings for the DShield Coordination Engine API."""

from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_reload: bool = False
    api_log_level: str = "info"

    # Security Configuration
    secret_key: str = "your-secret-key-here-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # API Authentication
    api_key_header: str = "X-API-Key"
    api_key: str = "your-api-key-here-change-this-in-production"

    # CORS Settings
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    allowed_methods: list[str] = ["GET", "POST", "PUT", "DELETE"]
    allowed_headers: list[str] = ["*"]

    # Database Configuration
    database_url: str = "postgresql://user:password@localhost:5432/coordination"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30

    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str = ""
    redis_db: int = 0
    redis_max_connections: int = 20

    # Elasticsearch Configuration
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_username: str = ""
    elasticsearch_password: str = ""
    elasticsearch_index_prefix: str = "dshield"
    elasticsearch_timeout: int = 30

    # LLM Configuration
    llm_service_url: str = "http://localhost:11434"
    llm_model: str = "llama-3.1-8b-instruct"
    llm_fallback_model: str = "mistral-7b-instruct"
    llm_timeout: int = 300
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.1

    # Analysis Configuration
    analysis_timeout_seconds: int = 300
    analysis_max_sessions: int = 1000
    analysis_confidence_threshold: float = 0.7
    analysis_temporal_window_seconds: int = 300
    analysis_batch_size: int = 100

    # Development Configuration
    debug: bool = False
    environment: str = "production"
    enable_swagger_ui: bool = True
    enable_redoc: bool = True

    # Performance Configuration
    max_memory_mb: int = 16000
    max_cpu_percent: int = 80
    worker_processes: int = 4
    worker_threads: int = 2

    @validator("allowed_origins", "allowed_methods", "allowed_headers", pre=True)
    def parse_list_fields(cls, v):
        """Parse list fields from environment variables."""
        if isinstance(v, str):
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        return v

    @validator("debug")
    def set_debug_defaults(cls, v, values):
        """Set debug-related defaults."""
        if v:
            values["enable_swagger_ui"] = True
            values["enable_redoc"] = True
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()
