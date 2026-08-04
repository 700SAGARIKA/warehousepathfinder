# Warehouse Path Finder

A Streamlit-based application for finding optimal paths in warehouse floor plans. Upload SVG layouts, place waypoints and rack faces, and discover the shortest routes between any two locations.

## Quick Start

### Option 1: Docker Compose (Recommended)
```bash
# Clone/navigate to project
cd /home/vvdn/Documents/warehouse_arch

# Deploy in one command
docker-compose up -d

# Access at http://localhost:8010
```

### Option 2: Using Make
```bash
make deploy    # Full pipeline
make logs      # View logs
make stop      # Stop containers
```

### Option 3: Bash Script
```bash
./deploy.sh    # Automated deployment pipeline
```

### Option 4: Local Python Development
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

---

## Architecture

```
warehouse_arch/
├── streamlit_app.py        # Main application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container definition
├── docker-compose.yml     # Orchestration
├── Makefile              # Make commands
├── deploy.sh             # Bash deployment script
├── DEPLOYMENT.md         # Detailed deployment guide
├── .env.example          # Environment variables template
└── .github/workflows/
    └── deploy.yml        # GitHub Actions CI/CD pipeline
```

---

## Features

✅ **SVG Floor Plan Upload**  
✅ **Automatic Waypoint Detection**  
✅ **Grid-based Point Snapping**  
✅ **Multi-level Rack Support**  
✅ **Pathfinding Algorithm (A*)**  
✅ **Route Optimization**  
✅ **Dark Theme UI**  

---

## System Requirements

- **Docker & Docker Compose** (recommended)
- **Python 3.11+** (for local development)
- **Port 8010** available
- **2GB RAM** minimum

---

## Deployment Methods

### 1. Docker Compose (Simple Local Deployment)
```bash
docker-compose up -d
```
**Best for**: Local development, testing, quick demos

### 2. Make Commands
```bash
make deploy      # Full build + deploy
make build       # Just build image
make run         # Start with compose
make logs        # View logs
make stop        # Stop containers
make clean       # Remove all resources
```
**Best for**: Teams familiar with Make, reproducible builds

### 3. Bash Script
```bash
./deploy.sh
```
**Best for**: Automated deployment, CI/CD integration, one-click deploys

### 4. Local Python
```bash
source venv/bin/activate
streamlit run streamlit_app.py
```
**Best for**: Development, debugging, quick iterations

### 5. GitHub Actions (CI/CD)
Push to `main` or `deploy` branch to trigger automated pipeline:
- Build Docker image
- Run security scans
- Push to registry
- Deploy to local environment

---

## Configuration

### Environment Variables (.env)
```bash
cp .env.example .env
# Edit .env as needed
```

Key variables:
```env
STREAMLIT_SERVER_PORT=8010
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_LOGGER_LEVEL=info
```

---

## Monitoring & Management

### View Logs
```bash
# Real-time logs
docker-compose logs -f warehouse-app

# Last 50 lines
docker-compose logs -f --tail=50
```

### Container Status
```bash
docker-compose ps
docker stats warehouse-app
```

### Health Check
```bash
curl http://localhost:8010
docker-compose exec warehouse-app curl http://localhost:8010
```

### Access Container Shell
```bash
docker-compose exec warehouse-app /bin/bash
```

---

## Troubleshooting

### Port 8010 Already in Use
```bash
# Find and kill process
lsof -i :8010
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Container Won't Start
```bash
# Check logs
docker-compose logs warehouse-app

# Rebuild without cache
docker-compose build --no-cache warehouse-app
docker-compose up -d
```

### Application Slow/Unresponsive
```bash
# Restart containers
docker-compose restart

# Check resource usage
docker stats warehouse-app

# Increase allocated resources in docker-compose.yml
```

---

## Development

### Local Setup
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Dependencies
- **streamlit**: Web framework
- **numpy**: Numerical computing
- **pillow**: Image processing
- **scipy**: Scientific computing
- **cairosvg**: SVG rendering

### File Structure in App
- `uploads/`: User-uploaded SVG files
- `streamlit_app.py`: Main application logic
- `requirements.txt`: Python dependencies

---

## Production Deployment

### AWS ECS
```bash
# Build and push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI
docker tag warehouse-path-finder:latest $ECR_URI/warehouse-path-finder:latest
docker push $ECR_URI/warehouse-path-finder:latest
```

### Google Cloud Run
```bash
gcloud run deploy warehouse-path-finder \
  --source . \
  --platform managed \
  --port 8010 \
  --memory 512Mi \
  --cpu 1
```

### Kubernetes
```bash
kubectl apply -f k8s-deployment.yaml
kubectl port-forward svc/warehouse-path-finder 8010:8010
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production guides.

---

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/deploy.yml`):
1. **Test**: Build and test Docker image
2. **Scan**: Security and dependency scanning
3. **Build & Push**: Push to container registry
4. **Deploy**: Deploy to local environment

Triggered on:
- Push to `main`, `develop`, or `deploy` branches
- Pull requests to `main`
- Manual workflow dispatch

---

## Performance Tips

- **Local Development**: Use `make run` for hot-reloading
- **Production**: Use health checks and auto-restart
- **Scaling**: Run multiple containers with load balancer
- **Caching**: Docker layer caching for faster builds

---

## Security

- Container runs as non-root user
- No secrets in image
- Dependency scanning enabled
- Minimal base image (python:3.11-slim)

See security scans in GitHub Actions for details.

---

## Support & Documentation

- **Deployment Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Quick Commands**: See Makefile or `make help`
- **Docker Logs**: `docker-compose logs -f`
- **Health Status**: `curl http://localhost:8010`

---

## License

MIT

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `make deploy` | Full deployment |
| `make build` | Build Docker image |
| `make run` | Start containers |
| `make logs` | View logs |
| `make stop` | Stop containers |
| `make clean` | Remove all |
| `./deploy.sh` | Automated pipeline |
| `docker-compose up -d` | Start with compose |
| `docker-compose down` | Stop with compose |

---

## Getting Help

1. Check [DEPLOYMENT.md](DEPLOYMENT.md) for detailed guides
2. Review container logs: `docker-compose logs`
3. Test image: `docker build -t warehouse-path-finder:test .`
4. Access shell: `docker-compose exec warehouse-app bash`

Happy deploying! 🚀
