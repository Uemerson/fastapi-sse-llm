# FastAPI SSE LLM

A demonstration project that integrates **FastAPI**, **Server-Sent Events (SSE)**, **RabbitMQ**, and **Redis** to create a real-time LLM response streaming system.

## 📋 Features

- **FastAPI** as a high-performance web server
- **SSE (Server-Sent Events)** for real-time bidirectional communication
- **RabbitMQ** as a message broker for asynchronous processing
- **Redis** for pub/sub and caching
- **Interactive web interface** with HTML/JavaScript
- **Docker Compose** to facilitate local development

## 🏗️ Architecture

```
┌─────────────────┐
│   Web Client    │
│  (index.html)   │
└────────┬────────┘
         │ SSE
         ▼
┌─────────────────────┐
│   FastAPI Server    │
│    (main.py)        │
└────────┬────────────┘
         │
    ┌────┴────┐
    │          │
    ▼          ▼
 Redis     RabbitMQ
    │          │
    ▼          ▼
 Pub/Sub   Consumer
           (consumer.py)
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.9+
- pip

### 1. Clone the repository

```bash
git clone https://github.com/Uemerson/fastapi-sse-llm.git
cd fastapi-sse-llm
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables

Create an `.env` file with the necessary configurations:

```env
REDIS_HOST=localhost
REDIS_PORT=6379
RABBITMQ_USER=guest
RABBITMQ_PASS=guest
```

### 4. Start services with Docker Compose

```bash
./up.sh
```

Or manually:

```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 5. Access the application

Open your browser and navigate to: **http://localhost:8000**

## 📁 Project Structure

```
.
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── Dockerfile.dev            # Dockerfile for development
├── docker-compose.dev.yml    # Docker Compose configuration
├── docker.clean.sh           # Script to clean containers
├── up.sh                      # Script to start the application
├── api.http                   # HTTP test requests
├── index.html                 # Frontend web interface
└── src/
    ├── main.py              # FastAPI server
    └── consumer.py          # RabbitMQ consumer
```

## 🔧 Components

### `src/main.py` - FastAPI Server

- Manages application lifecycle (lifespan)
- Configures Redis and RabbitMQ connections
- Implements SSE endpoints for response streaming
- Provides CORS middleware for cross-origin requests

### `src/consumer.py` - RabbitMQ Consumer

- Processes messages from the RabbitMQ queue
- Simulates LLM responses with token streaming
- Publishes results to Redis for client to receive via SSE

### `index.html` - Web Interface

- Interactive interface to send prompts
- Receives response streams via SSE
- Displays tokens in real-time
- Controls to start and stop requests

## 📡 Data Flow

1. **Client** sends a prompt via POST to `/ask`
2. **FastAPI** queues the message in RabbitMQ with a unique UUID
3. **Consumer** processes the RabbitMQ queue and simulates LLM responses
4. **Consumer** publishes tokens to Redis on a specific channel
5. **FastAPI** maintains an open SSE connection with the client
6. **Client** receives tokens in real-time and displays on the interface

## 🧪 Testing

### Using the web interface

1. Open the [index.html](index.html) in your browser
2. Enter a prompt in the input field
3. Click "Start" to begin streaming
4. Watch responses arrive in real-time

### Using curl

```bash
curl -N http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello world", "uuid": "'$(uuidgen)'"}'
```

### Using the api.http file

If you're using VSCode with the REST Client extension, open `api.http` and execute the requests.

## 🐳 Docker Compose

### Included services

- **FastAPI** on port 8000
- **RabbitMQ** on port 5672 (with web interface on 15672)
- **Redis** on port 6379

### Manage containers

```bash
# Start
docker-compose -f docker-compose.dev.yml up -d

# Stop
docker-compose -f docker-compose.dev.yml down

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Clean everything
./docker.clean.sh
```

## 🔑 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | localhost | Redis host |
| `REDIS_PORT` | 6379 | Redis port |
| `RABBITMQ_USER` | guest | RabbitMQ user |
| `RABBITMQ_PASS` | guest | RabbitMQ password |

## 📚 Main Dependencies

- **fastapi** - Asynchronous web framework
- **uvicorn** - ASGI server
- **aio-pika** - AMQP client for RabbitMQ
- **redis** - Asynchronous Redis client
- **python-dotenv** - Environment variable management

## 🛠️ Development

### Development structure

The project is configured to facilitate local development with:
- Automatic hot reload via uvicorn
- Docker Compose for external dependencies
- Environment variables via `.env`

### Adding new features

1. Modify `src/main.py` for new endpoints
2. Update `src/consumer.py` for new processing logic
3. Modify `index.html` for UI updates
4. Reinstall dependencies if necessary: `pip install -r requirements.txt`

## 🐛 Troubleshooting

### RabbitMQ connection error

Make sure the container is running:
```bash
docker-compose -f docker-compose.dev.yml ps
```

### Redis connection error

Check if Redis is accessible:
```bash
redis-cli ping
```

### SSE not working

Confirm that CORS is enabled and port 8000 is accessible.

## 📝 License

This project is licensed under the [LICENSE](./LICENSE).

## 👤 Author

Developed by [Uemerson](https://github.com/Uemerson)

## 🤝 Contributing

Contributions are welcome! Feel free to open issues and pull requests.

---

**Last updated:** December 4, 2025
