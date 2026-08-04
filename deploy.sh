#!/bin/bash

#############################################
# Warehouse Path Finder - Deployment Script
# Local Pipeline Automation
#############################################

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="warehouse-path-finder"
IMAGE_TAG="latest"
CONTAINER_PORT="8010"
DOCKER_PORT="8010"

# Functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_prerequisites() {
    print_header "Step 1: Checking Prerequisites"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker installed"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    print_success "Docker Compose installed"

    # Check port availability
    if lsof -Pi :$CONTAINER_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        print_warning "Port $CONTAINER_PORT is already in use. Trying to use it anyway..."
    else
        print_success "Port $CONTAINER_PORT is available"
    fi
}

setup_directories() {
    print_header "Step 2: Setting Up Directories"

    if [ ! -d "uploads" ]; then
        mkdir -p uploads
        print_success "Created uploads directory"
    else
        print_success "Uploads directory exists"
    fi
}

build_image() {
    print_header "Step 3: Building Docker Image"

    if docker build -t $PROJECT_NAME:$IMAGE_TAG . ; then
        print_success "Docker image built: $PROJECT_NAME:$IMAGE_TAG"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

test_image() {
    print_header "Step 4: Testing Image"

    if docker run --rm $PROJECT_NAME:$IMAGE_TAG python -c \
        "import streamlit, numpy, PIL, scipy, cairosvg; print('✓ Dependencies verified')" ; then
        print_success "All dependencies verified"
    else
        print_error "Dependency test failed"
        exit 1
    fi
}

stop_existing() {
    print_header "Step 5: Stopping Existing Containers"

    if docker-compose down 2>/dev/null; then
        print_success "Stopped existing containers"
    else
        print_warning "No existing containers to stop"
    fi
}

start_application() {
    print_header "Step 6: Starting Application"

    if docker-compose up -d ; then
        print_success "Containers started"
    else
        print_error "Failed to start containers"
        exit 1
    fi
}

health_check() {
    print_header "Step 7: Health Check"

    max_retries=10
    retry_count=0

    while [ $retry_count -lt $max_retries ]; do
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:$CONTAINER_PORT | grep -q "200"; then
            print_success "Application is healthy"
            return 0
        fi

        retry_count=$((retry_count + 1))
        echo "Waiting for application to be ready... ($retry_count/$max_retries)"
        sleep 2
    done

    print_warning "Health check timed out after ${max_retries} retries"
    print_warning "Container may still be starting. Check logs with: docker-compose logs warehouse-app"
}

show_status() {
    print_header "Deployment Status"

    echo "Container Status:"
    docker-compose ps

    echo -e "\n${GREEN}Application Details:${NC}"
    echo "  URL:       http://localhost:$CONTAINER_PORT"
    echo "  Container: warehouse-app"
    echo "  Image:     $PROJECT_NAME:$IMAGE_TAG"

    echo -e "\n${BLUE}Useful Commands:${NC}"
    echo "  View logs:     docker-compose logs -f warehouse-app"
    echo "  Stop app:      docker-compose down"
    echo "  Restart app:   docker-compose restart"
    echo "  Shell access:  docker-compose exec warehouse-app /bin/bash"
}

show_deployment_summary() {
    print_header "Deployment Complete!"

    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ Warehouse Path Finder is running!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "📱 Access the application at:"
    echo "   ${BLUE}http://localhost:$CONTAINER_PORT${NC}"
    echo ""
    echo "📋 Deployment Details:"
    echo "   Project:      $PROJECT_NAME"
    echo "   Image Tag:    $IMAGE_TAG"
    echo "   Container:    warehouse-app"
    echo "   Port:         $CONTAINER_PORT"
    echo ""
    echo "🔍 Monitor & Manage:"
    echo "   View logs:     ${YELLOW}docker-compose logs -f${NC}"
    echo "   Stop:          ${YELLOW}docker-compose down${NC}"
    echo "   Restart:       ${YELLOW}docker-compose restart${NC}"
    echo "   Shell access:  ${YELLOW}docker-compose exec warehouse-app bash${NC}"
    echo ""
}

# Main execution
main() {
    print_header "Warehouse Path Finder - Local Deployment"

    check_prerequisites
    setup_directories
    build_image
    test_image
    stop_existing
    start_application
    health_check
    show_status
    show_deployment_summary
}

# Run main function
main

exit 0
