import asyncio
import logging
import signal
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import os 
from src.config.settings import settings
from src.core.rabbitmq import rabbitmq
from src.core.email_client import email_client
from src.consumers.otp_consumer import otp_consumer
from src.models.schemas import HealthCheck

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("=" * 50)
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    logger.info("=" * 50)
    
    try:
        # Connect to RabbitMQ
        if await rabbitmq.connect():
            logger.info("✅ RabbitMQ connected successfully")
        else:
            logger.warning("⚠️ Failed to connect to RabbitMQ on startup, will retry...")
            # Schedule reconnection
            asyncio.create_task(rabbitmq.reconnect())
        
        # Start OTP consumer
        await otp_consumer.start()
        
        # Start consuming messages if connected to RabbitMQ
        if rabbitmq.is_connected:
            asyncio.create_task(
                rabbitmq.consume(otp_consumer.process_message)
            )
            logger.info("✅ Message consumption started")
        else:
            logger.warning("⚠️ Not starting message consumption - RabbitMQ not connected")
        
        logger.info("✅ Service startup completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("=" * 50)
    logger.info("🛑 Shutting down OTP Mail Service...")
    logger.info("=" * 50)
    
    try:
        # Stop consumer
        await otp_consumer.stop()
        logger.info("✅ OTP consumer stopped")
        
        # Close RabbitMQ connection
        await rabbitmq.close()
        logger.info("✅ RabbitMQ connection closed")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")
    
    logger.info("👋 Service shutdown completed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Microservice for sending OTP emails using RabbitMQ and Resend",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirects to docs."""
    return {"message": f"Welcome to {settings.app_name}. Visit /docs for API documentation."}


@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        HealthCheck: Service health status
    """
    try:
        return HealthCheck(
            status="healthy",
            rabbitmq_connected=rabbitmq.is_connected,
            email_service_ready=email_client.is_connected,
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service health check failed: {str(e)}"
        )


@app.get("/info", tags=["Info"])
async def service_info():
    """Get service information."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "rabbitmq_connected": rabbitmq.is_connected,
        "email_service_ready": email_client.is_connected,
        "environment": {
            "host": settings.host,
            "port": settings.port,
            "log_level": settings.log_level
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        # Signal will be handled by uvicorn
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


if __name__ == "__main__":
    # Setup signal handlers
    setup_signal_handlers()
    
    # Get port from environment variable (for Render deployment)
    port = int(os.getenv("PORT", settings.port))
    
    logger.info(f"Starting server on {settings.host}:{port}")
    
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=port,
        log_level=settings.log_level.lower(),
        access_log=True,
        timeout_keep_alive=30,
    )