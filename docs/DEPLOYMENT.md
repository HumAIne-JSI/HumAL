# Deployment Guide

This guide covers building and deploying HumAL using Docker.

## Prerequisites

- **Docker**: [Install Docker Desktop](https://www.docker.com/products/docker-desktop)
- **OpenAI API Key**: Required for ticket resolution and feedback features
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

### Frontend Docker Image

Build the frontend image with the following command:

```bash
docker build -t humal-frontend:latest ./frontend
```

This builds the frontend React + Vite application as a multi-stage Docker build. The image:
- **Stage 1**: Builds the optimized production bundle using Node.js
- **Stage 2**: Serves the built assets via **nginx**
- Exposes port 80 (served by nginx)

## Running Backend Container Separately

You can run the backend container independently by passing the OpenAI API key directly in the command:

```bash
docker run -d `
  --name humal-backend `
  -p 8000:8000 `
  -e OPENAI_API_KEY=your-openai-api-key-here `
  humal-backend:latest
```

**Parameters:**
- `-d`: Run in detached mode (background)
- `--name`: Container name for easy reference
- `-p 8000:8000`: Map container port 8000 to host port 8000
- `-e OPENAI_API_KEY=...`: Set OpenAI API key environment variable

**Verify the container is running:**

```bash
docker logs humal-backend
```

**Stop the container:**

```bash
docker stop humal-backend
```

## Using Docker Compose

Docker Compose simplifies running backend and frontend together.

### Prerequisites for Docker Compose

Create an `.env` file in the project root directory with your OpenAI API key:

```bash
# Windows PowerShell
copy .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=your-openai-api-key-here
```

The `.env` file is required for Docker Compose to work correctly.

### Starting Services with Docker Compose

Pull pre-built images and start all services:

```bash
docker-compose up
```

This command:
- Pulls pre-built images from a registry (if configured)
- Starts the backend container on port 8000
- Starts the frontend container on port 80
- Automatically loads the `.env` file for environment variables

**Run in background (detached mode):**

```bash
docker-compose up -d
```

### Accessing the Application

Once Docker Compose is running, access the services at:

- **Frontend Application**: http://localhost:80
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

View logs from a specific service:

```bash
docker-compose logs backend
docker-compose logs frontend
```