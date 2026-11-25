from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class EmailRequest(BaseModel):
    """Schema for incoming email requests from RabbitMQ."""
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject", min_length=1, max_length=200)
    text: str = Field(..., description="Plain text content", min_length=1)
    html: Optional[str] = Field(None, description="HTML content (optional)")
    
    @validator('to')
    def validate_email(cls, v):
        """Basic email validation."""
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "to": "user@example.com",
                "subject": "Your OTP Code",
                "text": "Your OTP code is 123456",
                "html": "<p>Your OTP code is <strong>123456</strong></p>"
            }
        }


class EmailResponse(BaseModel):
    """Schema for email sending response."""
    id: str = Field(..., description="Resend email ID")
    message: str = Field(..., description="Status message")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "email_123456789",
                "message": "Email sent successfully",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class HealthCheck(BaseModel):
    """Schema for health check response."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now)
    rabbitmq_connected: bool = Field(..., description="RabbitMQ connection status")
    email_service_ready: bool = Field(..., description="Email service status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00Z",
                "rabbitmq_connected": True,
                "email_service_ready": True
            }
        }