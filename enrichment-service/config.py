"""Configuration management for the AI-Augmented SOAR enrichment service.

All settings are loaded from environment variables (with .env file support)
using pydantic-settings BaseSettings. Import `settings` to access configuration.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings sourced from environment variables or .env file."""

    # Anthropic API configuration
    anthropic_api_key: str
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    # Elasticsearch configuration
    elasticsearch_url: str = "http://localhost:9200"
    elastic_password: str = "changeme"
    elastic_username: str = "elastic"

    # Redis configuration
    redis_url: str = "redis://localhost:6379"

    # Application configuration
    log_level: str = "info"

    # Feature flags
    enable_feedback_loop: bool = True
    enable_virustotal: bool = False
    enable_abuseipdb: bool = False

    # External threat intelligence API keys
    virustotal_api_key: str = ""
    abuseipdb_api_key: str = ""

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }


# Singleton settings instance
settings = Settings()
