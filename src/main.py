"""
Main application file for FastAPI with SSE, RabbitMQ,
and Redis integration.
"""

import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager

import aio_pika
import redis.asyncio as redis
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager:
    initializes and cleanly shuts down
    RabbitMQ (aio-pika) and Redis.
    """

    app.state.redis = redis.Redis(
        host=os.getenv("REDIS_HOST"),
        port=int(os.getenv("REDIS_PORT")),
        decode_responses=True,
    )
    app.state.rabbitmq = await aio_pika.connect_robust(
        f"amqp://{os.getenv('RABBITMQ_USER')}:"
        f"{os.getenv('RABBITMQ_PASS')}@rabbitmq/"
    )

    yield

    await app.state.rabbitmq.close()
    await app.state.redis.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def event_generator(channel_id: str, max_timeout: int = 60):
    """
    Generator that listens to Redis Pub/Sub channel
    and yields Server-Sent Events.

    Args:
        channel_id: Redis channel to subscribe to
        max_timeout: Maximum time in seconds to keep
                     connection open (default: 1 min)
    """

    pubsub = app.state.redis.pubsub()
    await pubsub.subscribe(channel_id)

    try:
        async with asyncio.timeout(max_timeout):
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue

                data = json.loads(message["data"])

                if data.get("event") != "token":
                    yield f"event: {data.get('event')}"
                    break

                if data.get("event") == "token":
                    yield (
                        f"data: {json.dumps({'token': data.get('data')})}\n\n"
                    )
    except asyncio.TimeoutError:
        yield "event: timeout"
    except Exception as e:
        print(f"Error in event_generator: {e}")
        yield "event: error"
    finally:
        await pubsub.unsubscribe(channel_id)
        await pubsub.close()


@app.post("/ask")
async def ask(request: Request):
    """
    Receive a prompt and enqueue it in RabbitMQ.
    """

    data = await request.json()
    prompt = data.get("query", "")

    channel_id = str(uuid.uuid4())
    payload = {"uuid": channel_id, "query": prompt}

    # Open a channel (async)
    connection = app.state.rabbitmq
    channel = await connection.channel()

    # Declare a durable queue
    await channel.declare_queue("llm_queue", durable=True)

    # Publish the message
    await channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(payload).encode(),
            # persistent message
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key="llm_queue",
    )

    return StreamingResponse(
        event_generator(channel_id=channel_id), media_type="text/event-stream"
    )
