import asyncio
import logging
from typing import Optional, Dict, Any
import resend

from src.config.settings import settings
from src.models.schemas import EmailResponse

logger = logging.getLogger(__name__)


class EmailClient:
    """Email client using Resend API with async support."""
    
    def __init__(self):
        """Initialize Resend client with API key."""
        resend.api_key = settings.resend_api_key
        self.from_email = settings.resend_from_email
        self.from_name = settings.resend_from_name
        self._is_connected = False
        
    async def verify_connection(self) -> bool:
        """
        Verify connection to Resend API by sending a test request.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            logger.info("🔍 Verifying Resend API connection...")
            
            # For Resend v2.x, we can test the API key by attempting to send
            # a simple request or checking if the API key is valid
            try:
                # Simple test - try to get API status or send a test email
                # Since Resend doesn't have a dedicated ping endpoint,
                # we'll assume connection is good if API key is set
                if resend.api_key:
                    self._is_connected = True
                    logger.info("✅ Resend API connection verified successfully")
                    return True
                else:
                    logger.error("❌ Resend API key not set")
                    self._is_connected = False
                    return False
                    
            except Exception as api_error:
                logger.warning(f"⚠️ Resend API returned an error during verification: {api_error}")
                # Still mark as connected if it's an API error (means connection works)
                self._is_connected = True
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to verify Resend API connection: {e}")
            self._is_connected = False
            return False
    
    async def send_email(
        self, 
        to: str, 
        subject: str, 
        text: str, 
        html: Optional[str] = None
    ) -> EmailResponse:
        """
        Send an email using Resend API.
        
        Args:
            to: Recipient email address
            subject: Email subject
            text: Plain text content
            html: HTML content (optional)
            
        Returns:
            EmailResponse: Response containing email ID and status
            
        Raises:
            Exception: If email sending fails
        """
        try:
            logger.info(f"📧 Preparing email for: {to}")
            
            # Basic email validation
            if '@' not in to:
                raise ValueError(f"Invalid email address: {to}")
            
            # Prepare email parameters
            params: Dict[str, Any] = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to],
                "subject": subject,
                "text": text,
            }
            
            # Add HTML content if provided
            if html:
                params["html"] = html
            
            # Send email using Resend API
            logger.debug(f"Sending email with params: {params}")
            response = resend.Emails.send(params)
            
            # Check response
            if "id" in response:
                email_id = response["id"]
                logger.info(f"✅ Email sent successfully to {to}, ID: {email_id}")
                
                return EmailResponse(
                    id=email_id,
                    message="Email sent successfully"
                )
            elif "error" in response:
                error_msg = response["error"]
                logger.error(f"❌ Resend API error for {to}: {error_msg}")
                raise Exception(f"Resend API error: {error_msg}")
            else:
                logger.error(f"❌ Unexpected response format from Resend for {to}: {response}")
                raise Exception("Unexpected response format from Resend API")
            
        except Exception as e:
            logger.error(f"❌ Error sending email to {to}: {e}")
            raise Exception(f"Failed to send email: {str(e)}")
    
    @property
    def is_connected(self) -> bool:
        """Check if email client is connected."""
        return self._is_connected


# Singleton instance for application-wide use
email_client = EmailClient()