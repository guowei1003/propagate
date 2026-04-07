FROM python:3.11-slim

# Install Docker CLI so the API can manage containers
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    docker-cli \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# The runner is a minimal execution environment.
# Actual script execution is delegated to the task container via docker API.
CMD ["python3", "-c", "print('Propagate runner ready')"]
