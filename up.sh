# #!/bin/bash

# docker rm -f redis-server 2>/dev/null || true
# docker rm -f mqtt-broker 2>/dev/null || true
# docker rm -f fastapi-sse 2>/dev/null || true
# docker network rm local_network 2>/dev/null || true

# docker build -t fastapi-sse .

# docker network create local_network

# docker run -d --name redis-server --network local_network -p 6379:6379 redis:latest
# docker run -d --name mqtt-broker --network local_network -p 1883:1883 eclipse-mosquitto:latest
# docker run -d --name fastapi-sse --network local_network --env-file .env -p 8000:8000 fastapi-sse

# docker logs -f fastapi-sse

#!/bin/bash
function trap_ctrlc ()
{
    # perform cleanup here
    docker compose -f docker-compose.yml down
 
    # exit shell script with error code 2
    # if omitted, shell script will continue execution
    exit 2
}

trap "trap_ctrlc" 2
docker compose -f docker-compose.dev.yml --env-file .env.dev up -d --build --remove-orphans
docker compose -f docker-compose.dev.yml logs -f --tail=15 api consumer