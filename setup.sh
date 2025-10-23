#!/bin/bash

# Dental Chatbot Application Setup Script
# This script sets up the complete dockerized application

set -e

echo "🦷 Dental Chatbot Application Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    print_status "Checking Docker daemon..."
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker daemon is not running. Please start Docker Desktop."
        print_status "On macOS: Open Docker Desktop application"
        print_status "On Linux: sudo systemctl start docker"
        exit 1
    fi
    print_success "Docker daemon is running"
}

# Check if Docker Compose is available
check_docker_compose() {
    print_status "Checking Docker Compose..."
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    print_success "Docker Compose is available"
}

# Create environment file if it doesn't exist
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        print_status "Creating .env file from template..."
        cp .env.example .env
        print_success "Environment file created"
    else
        print_warning "Environment file already exists"
    fi
}

# Build Docker images
build_images() {
    print_status "Building Docker images..."
    
    print_status "Building backend image..."
    docker-compose build backend
    
    print_status "Building frontend image..."
    docker-compose build frontend
    
    print_success "All images built successfully"
}

# Start services
start_services() {
    print_status "Starting services..."
    
    # Start backend first
    print_status "Starting backend service..."
    docker-compose up -d backend
    
    # Wait for backend to be healthy
    print_status "Waiting for backend to be ready..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Backend is ready"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        print_error "Backend failed to start within 60 seconds"
        exit 1
    fi
    
    # Start frontend
    print_status "Starting frontend service..."
    docker-compose up -d frontend
    
    print_success "All services started"
}

# Test the application
test_application() {
    print_status "Testing application..."
    
    # Test backend
    print_status "Testing backend API..."
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend API is responding"
    else
        print_error "Backend API is not responding"
        return 1
    fi
    
    # Test frontend
    print_status "Testing frontend..."
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend is responding"
    else
        print_error "Frontend is not responding"
        return 1
    fi
    
    # Test API token generation
    print_status "Testing API token generation..."
    response=$(curl -s -X POST http://localhost:8000/api/chatbot/token \
        -H "Content-Type: application/json" \
        -d '{"api_key": "dental-chatbot-api-key-2025"}' 2>/dev/null)
    
    if echo "$response" | grep -q "access_token"; then
        print_success "API token generation is working"
    else
        print_error "API token generation failed"
        return 1
    fi
}

# Show application URLs
show_urls() {
    echo ""
    print_success "🎉 Application is ready!"
    echo ""
    echo "📱 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📚 API Documentation: http://localhost:8000/docs"
    echo ""
    echo "🔑 Demo API Key: dental-chatbot-api-key-2025"
    echo ""
    echo "📋 Available commands:"
    echo "  make logs     - View application logs"
    echo "  make down     - Stop all services"
    echo "  make clean    - Clean up containers and images"
    echo "  make health   - Check service health"
    echo ""
}

# Main setup function
main() {
    echo "Starting setup process..."
    echo ""
    
    # Pre-flight checks
    check_docker
    check_docker_compose
    
    # Setup
    setup_environment
    build_images
    start_services
    
    # Test
    if test_application; then
        show_urls
    else
        print_error "Application testing failed"
        print_status "Check logs with: make logs"
        exit 1
    fi
}

# Run main function
main "$@"
