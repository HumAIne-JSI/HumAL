# Deployment Guide

This guide covers building and deploying HumAL using Docker.

## Prerequisites

- **Docker**: [Install Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Local dev setup**: Required for building the images (but not for only deploying them)

## Building Docker Images

### Backend Docker Image

Build the backend image with the following command:

```bash
docker build -t humal-backend:latest ./backend
```

This builds the backend FastAPI application with all Python dependencies installed. The image:
- Uses Python 3.11 as the base
- Installs dependencies from `backend/requirements.txt`
- Exposes port 8000

## Running Backend Container Separately

You can run the backend container independently by passing any required environment variables in the command:

```bash
docker run -d `
  --name humal-backend `
  -p 8000:8000 `
  humal-backend:latest
```

**Parameters:**
- `-d`: Run in detached mode (background)
- `--name`: Container name for easy reference
- `-p 8000:8000`: Map container port 8000 to host port 8000

**Verify the container is running:**

```bash
docker logs humal-backend
```

**Stop the container:**

```bash
docker stop humal-backend
```

## Using Docker Compose

Docker Compose simplifies running the backend application.

### Prerequisites for Docker Compose

Create an `.env` file in the project root directory with any required environment variables:

```bash
# Windows PowerShell
copy .env.example .env
```

### Starting Services with Docker Compose

Pull pre-built images and start the backend:

```bash
docker-compose up
```

This command:
- Pulls pre-built images from a registry (if configured)
- Starts the backend container on port 8000
- Automatically loads the `.env` file for environment variables

**Run in background (detached mode):**

```bash
docker-compose up -d
```

### Accessing the Application

Once Docker Compose is running, access the services at:

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Stopping Services

Stop all running services:

```bash
docker-compose down
```

This stops and removes all containers.

### Viewing Logs

View logs from all services:

```bash
docker-compose logs
```

View logs from the backend service:

```bash
docker-compose logs backend
```