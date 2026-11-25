import asyncio
import json
import logging
from typing import Optional, Callable, Any, Awaitable
from aio_pika import connect_robust, Connection, Channel, Queue
from aio_pika.abc import AbstractIncomingMessage, ExchangeType

from src.config.settings import settings

logger = logging.getLogger(__name__)


class RabbitMQConnection:
    """
    RabbitMQ connection manager with automatic reconnection.
    """
    
    def __init__(self):
        self.connection: Optional[Connection] = None
        self.channel: Optional[Channel] = None
        self.queue: Optional[Queue] = None
        
        # Reconnection settings
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = settings.rabbitmq_reconnect_attempts
        self._base_reconnect_delay = settings.rabbitmq_reconnect_delay
        self._max_reconnect_delay = settings.rabbitmq_reconnect_max_delay
        
        # Connection state
        self._is_connected = False
        self._is_consuming = False
    
    async def connect(self) -> bool:
        """
        Establish connection to RabbitMQ with retry logic.
        """
        try:
            logger.info(f"🔗 Connecting to RabbitMQ using provided URL")
            
            # Establish connection
            self.connection = await connect_robust(settings.rabbitmq_url)
            
            # Create channel
            self.channel = await self.connection.channel()
            
            # Set QoS for throughput
            await self.channel.set_qos(
                prefetch_count=settings.rabbitmq_prefetch_count
            )
            
            # Try to declare queue without DLX arguments first (simpler)
            try:
                self.queue = await self.channel.declare_queue(
                    settings.rabbitmq_queue_name,
                    durable=True
                )
                logger.info("✅ RabbitMQ queue declared (simple mode)")
            except Exception as queue_error:
                # If simple declaration fails, try without any arguments
                logger.warning(f"Queue declaration failed, trying alternative: {queue_error}")
                try:
                    # First, delete the existing queue
                    await self.channel.queue_delete(settings.rabbitmq_queue_name)
                    logger.info("Deleted existing queue")
                    
                    # Then recreate it
                    self.queue = await self.channel.declare_queue(
                        settings.rabbitmq_queue_name,
                        durable=True
                    )
                    logger.info("✅ RabbitMQ queue recreated")
                except Exception as delete_error:
                    logger.error(f"Failed to recreate queue: {delete_error}")
                    # Try one more time with passive declaration
                    self.queue = await self.channel.declare_queue(
                        settings.rabbitmq_queue_name,
                        passive=True  # Just check if queue exists
                    )
                    logger.info("✅ Using existing RabbitMQ queue (passive mode)")
            
            # Reset reconnection attempts on successful connection
            self._reconnect_attempts = 0
            self._is_connected = True
            
            logger.info("✅ RabbitMQ connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            self._is_connected = False
            return False
    
    async def reconnect(self) -> bool:
        """
        Attempt reconnection with exponential backoff.
        """
        while self._reconnect_attempts < self._max_reconnect_attempts:
            self._reconnect_attempts += 1
            
            # Calculate delay with exponential backoff, capped at max delay
            delay = min(
                self._max_reconnect_delay,
                self._base_reconnect_delay * (2 ** (self._reconnect_attempts - 1))
            )
            
            logger.info(f"🔄 Reconnection attempt {self._reconnect_attempts}/"
                       f"{self._max_reconnect_attempts} in {delay}s")
            
            await asyncio.sleep(delay)
            
            if await self.connect():
                logger.info("✅ Reconnection successful")
                return True
        
        logger.error(f"❌ Max reconnection attempts ({self._max_reconnect_attempts}) reached")
        return False
    
    def _on_connection_close(self, connection: Connection, reason: Optional[Exception] = None) -> None:
        """Handle connection close events."""
        logger.error(f"🔌 RabbitMQ connection closed: {reason}")
        self._is_connected = False
        self._is_consuming = False
        
        # Schedule reconnection
        asyncio.create_task(self._schedule_reconnection())
    
    async def _schedule_reconnection(self):
        """Schedule automatic reconnection."""
        await self.reconnect()
    
    async def consume(
        self, 
        callback: Callable[[dict], Awaitable[Any]]
    ) -> None:
        """
        Start consuming messages from the queue.
        """
        if not self.queue or not self.channel:
            raise RuntimeError("Not connected to RabbitMQ. Call connect() first.")
        
        async def on_message(message: AbstractIncomingMessage) -> None:
            """Process incoming messages."""
            try:
                # Parse message body
                body = json.loads(message.body.decode())
                logger.debug(f"📩 Received message: {body}")
                
                # Process message using provided callback
                await callback(body)
                
                # Acknowledge successful processing
                await message.ack()
                logger.debug(f"✅ Message processed and acknowledged")
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON in message: {e}")
                await message.nack(requeue=False)
            except Exception as e:
                logger.error(f"❌ Failed to process message: {e}")
                # Don't requeue
                await message.nack(requeue=False)
        
        # Start consuming with manual acknowledgment
        await self.queue.consume(on_message, no_ack=False)
        self._is_consuming = True
        logger.info(f"🚀 Started consuming from queue: {settings.rabbitmq_queue_name}")
    
    async def close(self) -> None:
        """Close RabbitMQ connection gracefully."""
        try:
            self._is_consuming = False
            self._is_connected = False
            
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                logger.info("🔌 RabbitMQ connection closed gracefully")
                
        except Exception as e:
            logger.error(f"❌ Error closing RabbitMQ connection: {e}")
        finally:
            self.connection = None
            self.channel = None
            self.queue = None
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to RabbitMQ."""
        return self._is_connected
    
    @property
    def is_consuming(self) -> bool:
        """Check if actively consuming messages."""
        return self._is_consuming


# Singleton instance for application-wide use
rabbitmq = RabbitMQConnection()