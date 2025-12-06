"""
Consumer service for processing LLM prompts from RabbitMQ
and publishing results to Redis.
"""

import asyncio
import json
import logging
import os
import random
import time
from typing import AsyncGenerator

import aio_pika
import redis.asyncio as redis

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(message)s",
)
logger = logging.getLogger(__name__)


class Settings:
    """Configuration settings from environment variables."""

    rabbit_user = os.getenv("RABBITMQ_USER")
    rabbit_pass = os.getenv("RABBITMQ_PASS")
    rabbit_host = os.getenv("RABBITMQ_HOST", "rabbitmq")

    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    region = os.getenv("REGION", "unknown")


settings = Settings()


redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
)


TOTAL_PROCESSING_TIMEOUT = int(os.getenv("TIMEOUT_SECONDS"))  # seconds


async def simulate_llm(
    prompt: str, channel_id: str
) -> AsyncGenerator[str, None]:
    """Simulates token streaming."""
    words = (
        f"{prompt}: This is a simulated LLM stream. Channel ID: {channel_id}"
    ).split()
    is_timeout = bool(random.getrandbits(1))
    for w in words:
        await asyncio.sleep(TOTAL_PROCESSING_TIMEOUT if is_timeout else 0.25)
        yield w


async def stream_to_redis(channel_id: str, token: str):
    """Publishes token safely to Redis."""
    try:
        await redis_client.publish(
            channel_id,
            json.dumps({"event": "token", "data": token}),
        )
    except Exception as e:
        logger.error("Redis publish error: %s", e)


async def process_message(channel_id: str, prompt: str):
    """Handles the full LLM streaming pipeline."""
    async for token in simulate_llm(prompt, channel_id):
        await stream_to_redis(channel_id, token)

    await redis_client.publish(
        channel_id,
        json.dumps({"event": "done", "data": {}}),
    )


async def callback(message: aio_pika.IncomingMessage):
    """RabbitMQ message handler with total processing timeout."""
    logger.info("Message received (AWS region %s)", settings.region)

    try:
        async with message.process(ignore_processed=True):
            body = json.loads(message.body.decode())

            channel_id = body.get("uuid")
            prompt = body.get("query")
            expires_at = body.get("expires_at", 0)

            if not channel_id or not prompt:
                raise ValueError("Invalid message payload")

            # Discard expired messages before starting processing
            if expires_at < time.time():
                logger.warning("Message expired — discarding")
                await redis_client.publish(
                    channel_id,
                    json.dumps({"event": "expired", "data": {}}),
                )
                return

            try:
                # TOTAL message processing timeout
                await asyncio.wait_for(
                    process_message(channel_id, prompt),
                    timeout=TOTAL_PROCESSING_TIMEOUT,
                )
            except asyncio.TimeoutError:
                logger.error(
                    "Processing timeout reached for channel %s",
                    channel_id,
                )

                await redis_client.publish(
                    channel_id,
                    json.dumps({"event": "timeout", "data": {}}),
                )

    except Exception as e:
        logger.error("Error processing message: %s", e)
        await message.reject(requeue=False)


async def main():
    """Initialize RabbitMQ consumer and keep it alive."""

    rabbit_url = (
        f"amqp://{settings.rabbit_user}:{settings.rabbit_pass}"
        f"@{settings.rabbit_host}/"
    )

    connection = await aio_pika.connect_robust(rabbit_url)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)

    queue = await channel.declare_queue("llm_queue", durable=True)
    await queue.consume(callback)

    logger.info("Worker started and waiting for messages...")
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        logger.info("Shutting down gracefully...")
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
