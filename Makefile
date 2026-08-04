.PHONY: help build run test clean deploy logs stop shell

help:
	@echo ""
	@echo "Warehouse Path Finder - Local Pipeline"
	@echo "========================================"
	@echo ""
	@echo "Usage: make [command]"
	@echo ""
	@echo "Commands:"
	@echo "  make build       - Build Docker image"
	@echo "  make run         - Start application with Docker Compose"
	@echo "  make deploy      - Full pipeline: build + run"
	@echo "  make test        - Build and verify dependencies"
	@echo "  make logs        - View container logs (follow mode)"
	@echo "  make stop        - Stop running containers"
	@echo "  make shell       - Access container shell"
	@echo "  make clean       - Remove containers and images"
	@echo "  make status      - Show container status"
	@echo ""
	@echo "App URL: http://localhost:8010"
	@echo ""

build:
	@echo "[1/3] Building Docker image..."
	docker build -t warehouse-path-finder:latest .
	@echo "✓ Image built: warehouse-path-finder:latest"

run: build
	@echo "[2/3] Creating uploads directory..."
	@mkdir -p uploads
	@echo "[3/3] Starting application..."
	docker-compose up -d
	@sleep 3
	@echo "✓ Application started"
	@echo "✓ Access at: http://localhost:8010"

deploy: clean build run
	@echo ""
	@echo "=========================================="
	@echo "✓ Full deployment complete!"
	@echo "=========================================="
	@echo ""
	@echo "Application: http://localhost:8010"
	@echo "View logs:   make logs"
	@echo "Stop app:    make stop"
	@echo ""

test: build
	@echo "Testing Docker image..."
	@docker run --rm warehouse-path-finder:latest python -c "import streamlit, numpy, PIL, scipy, cairosvg; print('✓ All dependencies OK')"

logs:
	docker-compose logs -f --tail=50 warehouse-app

status:
	@echo "Container Status:"
	@docker-compose ps
	@echo ""
	@echo "Health Check:"
	@curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8010 || echo "App not responding"

stop:
	@echo "Stopping containers..."
	docker-compose down
	@echo "✓ Containers stopped"

shell:
	docker-compose exec warehouse-app /bin/bash

clean: stop
	@echo "Removing Docker image..."
	docker rmi -f warehouse-path-finder:latest || true
	@echo "Cleaning uploads..."
	@rm -rf uploads/*
	@echo "✓ Cleanup complete"

dev-install:
	python3.11 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✓ Development environment ready"
	@echo "Run: source venv/bin/activate && streamlit run streamlit_app.py"

.DEFAULT_GOAL := help
