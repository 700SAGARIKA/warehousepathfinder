# Warehouse Path Finder - Local Deployment Pipeline Guide

## Project Overview
- **Application Type**: Streamlit Web Application
- **Language**: Python 3.11
- **Primary Port**: 8010
- **Container Runtime**: Docker
- **Key Dependencies**: streamlit, numpy, pillow, scipy, cairosvg

---

## 1. LOCAL DEVELOPMENT SETUP

### Prerequisites
- Docker & Docker Compose installed
- Python 3.11+ (for local testing)
- Git
- Terminal/Shell access

### Quick Start (Local Development)

```bash
# Clone/navigate to project
cd /home/vvdn/Documents/warehouse_arch

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Streamlit app locally
streamlit run streamlit_app.py
```

The app will be available at `http://localhost:8501` (default Streamlit port)

---

## 2. DOCKER BUILD & RUN

### Build Docker Image

```bash
# Build the image
docker build -t warehouse-path-finder:latest .

# Or with version tag
docker build -t warehouse-path-finder:1.0.0 .
```

### Run Container Manually

```bash
# Basic run
docker run -p 8010:8010 warehouse-path-finder:latest

# With volume mounting (for persistent uploads)
docker run -p 8010:8010 \
  -v $(pwd)/uploads:/app/uploads \
  warehouse-path-finder:latest

# With environment variables
docker run -p 8010:8010 \
  -e STREAMLIT_SERVER_HEADLESS=true \
  warehouse-path-finder:latest
```

Access at: `http://localhost:8010`

---

## 3. DOCKER COMPOSE (RECOMMENDED FOR LOCAL)

### Quick Deploy

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f warehouse-app

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Features of docker-compose.yml:
- ✅ Auto-build from Dockerfile
- ✅ Volume mounting for live code updates
- ✅ Health checks
- ✅ Auto-restart policy
- ✅ Port mapping (8010)
- ✅ Persistent upload directory

---

## 4. LOCAL CI/CD PIPELINE OPTIONS

### Option A: Using GitHub Actions (for local testing)
Create `.github/workflows/deploy-local.yml`:

```yaml
name: Local Deployment Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker Image
        run: docker build -t warehouse-path-finder:${{ github.sha }} .
      
      - name: Run Container Tests
        run: |
          docker run --rm warehouse-path-finder:${{ github.sha }} \
            pip list | grep streamlit
      
      - name: Build Final Image
        run: docker build -t warehouse-path-finder:latest .
```

### Option B: Using Make (Simple Local Pipeline)
Create `Makefile`:

```makefile
.PHONY: help build run test clean deploy

help:
	@echo "Warehouse Path Finder - Local Pipeline"
	@echo "========================================"
	@echo "make build    - Build Docker image"
	@echo "make run      - Run with Docker Compose"
	@echo "make test     - Test the application"
	@echo "make logs     - View container logs"
	@echo "make stop     - Stop containers"
	@echo "make clean    - Remove containers & images"
	@echo "make deploy   - Full deployment pipeline"

build:
	docker build -t warehouse-path-finder:latest .
	@echo "✓ Image built: warehouse-path-finder:latest"

run: build
	docker-compose up -d
	@echo "✓ Application started at http://localhost:8010"

test: build
	docker run --rm warehouse-path-finder:latest python -m pip list

logs:
	docker-compose logs -f warehouse-app

stop:
	docker-compose down
	@echo "✓ Containers stopped"

clean: stop
	docker rmi warehouse-path-finder:latest
	rm -rf uploads/*
	@echo "✓ Cleanup complete"

deploy: clean build run
	@echo "✓ Full deployment pipeline complete"
	@echo "App available at: http://localhost:8010"
```

Run pipeline:
```bash
make deploy      # Full pipeline
make build       # Just build
make run         # Start containers
make logs        # View logs
make stop        # Stop
```

### Option C: Bash Script Pipeline
Create `deploy.sh`:

```bash
#!/bin/bash

set -e

PROJECT_NAME="warehouse-path-finder"
IMAGE_TAG="latest"
CONTAINER_NAME="warehouse-app"

echo "=========================================="
echo "Warehouse Path Finder - Deployment Pipeline"
echo "=========================================="

# Step 1: Build
echo "[1/4] Building Docker image..."
docker build -t $PROJECT_NAME:$IMAGE_TAG .

# Step 2: Test
echo "[2/4] Testing image..."
docker run --rm $PROJECT_NAME:$IMAGE_TAG python -c "import streamlit; print('✓ Streamlit OK')"

# Step 3: Stop existing container
echo "[3/4] Stopping existing containers..."
docker-compose down || true

# Step 4: Start new deployment
echo "[4/4] Starting deployment..."
docker-compose up -d

# Verify
sleep 5
if curl -f http://localhost:8010 > /dev/null 2>&1; then
    echo "✓ Deployment successful!"
    echo "✓ App available at: http://localhost:8010"
else
    echo "✗ Health check failed"
    docker-compose logs warehouse-app
    exit 1
fi
```

Usage:
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 5. COMPLETE LOCAL DEPLOYMENT CHECKLIST

### Pre-Deployment
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Docker/Docker Compose installed
- [ ] Port 8010 is available (`lsof -i :8010`)
- [ ] Git repository initialized (optional)

### Deployment Steps
```bash
# Step 1: Navigate to project
cd /home/vvdn/Documents/warehouse_arch

# Step 2: Create uploads directory
mkdir -p uploads

# Step 3: Build and deploy
docker-compose up -d --build

# Step 4: Verify
curl -I http://localhost:8010

# Step 5: View logs
docker-compose logs warehouse-app
```

### Post-Deployment
- [ ] App accessible at `http://localhost:8010`
- [ ] Upload SVG files work
- [ ] No errors in logs
- [ ] Health checks passing

---

## 6. ENVIRONMENT VARIABLES

Create `.env` file for custom configuration:

```env
# Streamlit Configuration
STREAMLIT_SERVER_PORT=8010
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_LOGGER_LEVEL=info

# Docker Configuration
DOCKER_BUILDKIT=1
COMPOSE_DOCKER_CLI_BUILD=1
```

---

## 7. TROUBLESHOOTING

### Port 8010 already in use
```bash
# Find process using port
lsof -i :8010

# Kill process
kill -9 <PID>

# Or use different port
docker-compose --env-file .env up -d
# Update .env: STREAMLIT_SERVER_PORT=8011
```

### Container won't start
```bash
# Check logs
docker-compose logs warehouse-app

# Rebuild without cache
docker-compose build --no-cache

# Verify dependencies
docker run -it warehouse-path-finder:latest pip list
```

### Health check failing
```bash
# Manually test
docker exec warehouse-app curl -f http://localhost:8010

# Check port binding
docker port warehouse-app
```

---

## 8. SCALING TO PRODUCTION

When ready to deploy to cloud:

### AWS ECS
```bash
# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI
docker tag warehouse-path-finder:latest $ECR_URI/warehouse-path-finder:latest
docker push $ECR_URI/warehouse-path-finder:latest
```

### Google Cloud Run
```bash
# Build and deploy
gcloud run deploy warehouse-path-finder \
  --source . \
  --platform managed \
  --port 8010
```

### Kubernetes
Create `k8s-deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: warehouse-path-finder
spec:
  replicas: 1
  selector:
    matchLabels:
      app: warehouse-path-finder
  template:
    metadata:
      labels:
        app: warehouse-path-finder
    spec:
      containers:
      - name: warehouse-app
        image: warehouse-path-finder:latest
        ports:
        - containerPort: 8010
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

---

## 9. MONITORING & LOGGING

### Local Monitoring
```bash
# Real-time logs
docker-compose logs -f --tail=50

# Container stats
docker stats warehouse-app

# Health status
docker-compose ps
```

### Log Rotation (docker-compose.yml)
```yaml
services:
  warehouse-app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 10. QUICK REFERENCE

| Task | Command |
|------|---------|
| Deploy | `docker-compose up -d --build` |
| View Logs | `docker-compose logs -f` |
| Stop | `docker-compose down` |
| Rebuild | `docker-compose build --no-cache` |
| Shell Access | `docker-compose exec warehouse-app /bin/bash` |
| Check Status | `docker-compose ps` |
| Remove All | `docker-compose down -v` |
| Test Build | `docker build -t warehouse-path-finder:test .` |

---

## Summary

This deployment pipeline provides:
✅ **Local Development**: Python venv setup  
✅ **Containerization**: Docker with optimized dependencies  
✅ **Orchestration**: Docker Compose for easy management  
✅ **CI/CD Options**: Make, Bash scripts, GitHub Actions  
✅ **Health Checks**: Auto-restart & verification  
✅ **Production Ready**: Easily scales to cloud platforms  

Choose the deployment method that best fits your workflow!
