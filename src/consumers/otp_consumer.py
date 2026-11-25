import logging
from typing import Dict, Any

from src.core.email_client import email_client
from src.models.schemas import EmailRequest

logger = logging.getLogger(__name__)


class OTPConsumer:
    """
    Consumer for processing OTP email messages.
    Follows Single Responsibility Principle.
    """
    
    def __init__(self):
        self.email_client = email_client
        self._is_processing = False
        
    async def start(self) -> None:
        """
        Start the OTP consumer.
        
        Returns:
            None
        """
        logger.info("🚀 Starting OTP email consumer...")
        
        # Verify email client connection
        if await self.email_client.verify_connection():
            logger.info("✅ Email client is ready")
        else:
            logger.warning("⚠️ Email client verification had issues, will attempt on send")
        
        self._is_processing = True
        logger.info("👂 OTP mail consumer is waiting for messages...")
    
    async def process_message(self, message: Dict[str, Any]) -> None:
        """
        Process a single email message from RabbitMQ.
        
        Args:
            message: Dictionary containing email data
            
        Raises:
            ValueError: If message validation fails
            Exception: If email sending fails
        """
        try:
            # Validate and parse message using Pydantic
            email_request = EmailRequest(**message)
            
            logger.info(f"📨 Processing email for: {email_request.to}")
            
            # Send email using Resend
            response = await self.email_client.send_email(
                to=email_request.to,
                subject=email_request.subject,
                text=email_request.text,
                html=email_request.html
            )
            
            logger.info(f"✅ OTP email sent: {response.id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to process email message: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the consumer."""
        self._is_processing = False
        logger.info("🛑 OTP consumer stopped")
    
    @property
    def is_processing(self) -> bool:
        """Check if consumer is processing messages."""
        return self._is_processing


# Singleton instance for application-wide use
otp_consumer = OTPConsumer()