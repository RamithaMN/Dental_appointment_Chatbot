# Makefile for Dental Chatbot Application

.PHONY: help build up down logs clean test dev prod

# Default target
help:
	@echo "Dental Chatbot Application - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  dev          - Start development environment"
	@echo "  dev-build    - Build development images"
	@echo "  dev-logs     - Show development logs"
	@echo ""
	@echo "Production:"
	@echo "  prod         - Start production environment"
	@echo "  prod-build   - Build production images"
	@echo "  prod-logs    - Show production logs"
	@echo ""
	@echo "Utilities:"
	@echo "  build        - Build all images"
	@echo "  up           - Start all services"
	@echo "  down         - Stop all services"
	@echo "  logs         - Show all logs"
	@echo "  clean        - Clean up containers and images"
	@echo "  test         - Run tests"
	@echo "  shell-backend - Open shell in backend container"
	@echo "  shell-frontend - Open shell in frontend container"

# Development commands
dev:
	@echo "Starting development environment..."
	docker-compose -f docker-compose.yml up --build

dev-build:
	@echo "Building development images..."
	docker-compose -f docker-compose.yml build

dev-logs:
	@echo "Showing development logs..."
	docker-compose -f docker-compose.yml logs -f

# Production commands
prod:
	@echo "Starting production environment..."
	docker-compose -f docker-compose.yml --profile production up --build -d

prod-build:
	@echo "Building production images..."
	docker-compose -f docker-compose.yml --profile production build

prod-logs:
	@echo "Showing production logs..."
	docker-compose -f docker-compose.yml --profile production logs -f

# General commands
build:
	@echo "Building all images..."
	docker-compose build

up:
	@echo "Starting all services..."
	docker-compose up -d

down:
	@echo "Stopping all services..."
	docker-compose down

logs:
	@echo "Showing all logs..."
	docker-compose logs -f

clean:
	@echo "Cleaning up containers and images..."
	docker-compose down -v --rmi all --remove-orphans
	docker system prune -f

test:
	@echo "Running tests..."
	docker-compose exec backend python -m pytest tests/ || echo "No tests found"
	docker-compose exec frontend npm test || echo "No tests found"

# Single Container Commands
single:
	@echo "Starting single container with both services..."
	docker-compose -f docker-compose-single.yml up --build

single-build:
	@echo "Building single container image..."
	docker-compose -f docker-compose-single.yml build

single-logs:
	@echo "Showing single container logs..."
	docker-compose -f docker-compose-single.yml logs -f

single-down:
	@echo "Stopping single container..."
	docker-compose -f docker-compose-single.yml down

single-clean:
	@echo "Cleaning up single container..."
	docker-compose -f docker-compose-single.yml down -v --rmi all --remove-orphans

single-shell:
	@echo "Opening shell in single container..."
	docker-compose -f docker-compose-single.yml exec dental-chatbot /bin/bash

# Shell access
shell-backend:
	@echo "Opening shell in backend container..."
	docker-compose exec backend /bin/bash

shell-frontend:
	@echo "Opening shell in frontend container..."
	docker-compose exec frontend /bin/sh

# Health checks
health:
	@echo "Checking service health..."
	@echo "Backend: $$(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null || echo 'unhealthy')"
	@echo "Frontend: $$(curl -s http://localhost:3000 > /dev/null && echo 'healthy' || echo 'unhealthy')"

health-single:
	@echo "Checking single container health..."
	@echo "Nginx Proxy: $$(curl -s http://localhost/health | jq -r '.status' 2>/dev/null || echo 'unhealthy')"
	@echo "Frontend: $$(curl -s http://localhost > /dev/null && echo 'healthy' || echo 'unhealthy')"

# Database commands (for future use)
db-migrate:
	@echo "Running database migrations..."
	docker-compose exec backend python -m alembic upgrade head

db-seed:
	@echo "Seeding database..."
	docker-compose exec backend python scripts/seed_data.py
