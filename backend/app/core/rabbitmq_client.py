import asyncio
import aio_pika
import json
import logging
from aio_pika import Message

logger = logging.getLogger(__name__)


class RabbitMQClient:

    def __init__(self, url: str):
        self.url = url
        self.connection = None
        self.channel = None
        self._connect_lock = asyncio.Lock()

    # -------------------
    # CONNECTION
    # -------------------
    async def connect(self):
        async with self._connect_lock:
            if self.connection and not self.connection.is_closed:
                if self.channel and not self.channel.is_closed:
                    return
                self.channel = await self.connection.channel()
                return

            self.connection = await aio_pika.connect_robust(self.url)
            self.channel = await self.connection.channel()

    async def close(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

        self.connection = None
        self.channel = None

    async def _ensure_connected(self):
        if self.connection and not self.connection.is_closed and self.channel and not self.channel.is_closed:
            return
        await self.connect()

    # -------------------
    # PUBLISHER
    # -------------------
    async def publish(self, queue_name: str, message: dict):
        await self._ensure_connected()

        await self.channel.default_exchange.publish(
            Message(
                body=json.dumps(message).encode(),
                delivery_mode=2
            ),
            routing_key=queue_name
        )

    # -------------------
    # CONSUMER
    # -------------------
    async def consume(self, queue_name: str, callback):
        await self._ensure_connected()

        queue = await self.channel.declare_queue(
            queue_name,
            passive=True  # App does not own the queue
        )

        async def wrapped_callback(message):
            async with message.process():
                try:
                    data = json.loads(message.body)
                    await callback(data)
                except Exception as e:
                    logger.error(f"Error processing RabbitMQ message from '{queue_name}': {type(e).__name__}: {str(e)}", exc_info=True)
                    # Don't re-raise - keep the consumer alive for subsequent messages

        return await queue.consume(wrapped_callback)