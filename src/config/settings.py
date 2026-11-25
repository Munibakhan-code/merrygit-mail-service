import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable loading."""
    
    # Server Configuration
    app_name: str = Field(default="OTP Mail Service", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    port: int = Field(default=8000, alias="PORT")
    host: str = Field(default="0.0.0.0", alias="HOST")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # RabbitMQ Configuration
    rabbitmq_url: str = Field(..., alias="RABBITMQ_URL")
    rabbitmq_queue_name: str = Field(default="send-otp", alias="RABBITMQ_QUEUE_NAME")
    rabbitmq_prefetch_count: int = Field(default=10, alias="RABBITMQ_PREFETCH_COUNT")
    
    # RabbitMQ Reconnection Settings
    rabbitmq_reconnect_attempts: int = Field(default=5, alias="RABBITMQ_RECONNECT_ATTEMPTS")
    rabbitmq_reconnect_delay: int = Field(default=5, alias="RABBITMQ_RECONNECT_DELAY")
    rabbitmq_reconnect_max_delay: int = Field(default=30, alias="RABBITMQ_RECONNECT_MAX_DELAY")
    
    # Resend Email Configuration
    resend_api_key: str = Field(..., alias="RESEND_API_KEY")
    resend_from_email: str = Field(default="info@merrygit.tech", alias="RESEND_FROM_EMAIL")
    resend_from_name: str = Field(default="MerryGit", alias="RESEND_FROM_NAME")
    
    # Email Template Settings
    email_timeout: int = Field(default=30, alias="EMAIL_TIMEOUT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
    
    @property
    def actual_port(self) -> int:
        """
        Get the actual port to use.
        Render provides PORT environment variable, so use that if available.
        """
        return int(os.getenv("PORT", self.port))


# Create global settings instance
settings = Settings() 