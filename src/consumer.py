"""
Consumer service for processing LLM prompts from RabbitMQ
and publishing results to Redis.
"""

import asyncio
import json
import os
import random

import aio_pika
import redis.asyncio as redis

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    decode_responses=True,
)


async def simulate_llm(prompt: str, channel_id: str):
    """Simulates streaming LLM responses by yielding tokens with delays."""

    is_timeout = random.choice([True, False])
    words = (
        f"{prompt}: This is a simulated LLM stream. Channel ID: {channel_id}"
    ).split()
    for w in words:
        await asyncio.sleep(0.25 if not is_timeout else 60)
        yield w


async def callback(message: aio_pika.IncomingMessage):
    """Callback function to process messages from RabbitMQ."""

    async with message.process():
        data = json.loads(message.body.decode())
        channel_id = data.get("uuid", "")
        prompt = data.get("query", "")

        async for chunk in simulate_llm(prompt, channel_id):
            await redis_client.publish(
                channel_id, json.dumps({"event": "token", "data": chunk})
            )

        await redis_client.publish(
            channel_id,
            json.dumps(
                {
                    "event": "done",
                    "data": {},
                }
            ),
        )


async def main():
    """Main function to set up RabbitMQ consumer."""

    connection = await aio_pika.connect_robust("amqp://admin:admin@rabbitmq/")
    channel = await connection.channel()
    queue = await channel.declare_queue("llm_queue", durable=True)
    await queue.consume(callback)
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
