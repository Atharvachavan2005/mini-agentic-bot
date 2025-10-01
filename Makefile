# Mini Agentic Bot - Makefile

.PHONY: help build up down logs clean dev test

# Default target
help:
	@echo "Mini Agentic Bot - Available Commands:"
	@echo ""
	@echo "  make build     - Build Docker images"
	@echo "  make up        - Start the application (frontend only)"
	@echo "  make up-api    - Start with API backend"
	@echo "  make down      - Stop all services"
	@echo "  make logs      - View logs"
	@echo "  make clean     - Clean up containers and images"
	@echo "  make dev       - Development mode with live reload"
	@echo "  make test      - Run tests"
	@echo "  make setup     - Initial setup"

# Build Docker images
build:
	docker-compose build

# Start frontend only
up:
	docker-compose up frontend

# Start with API backend
up-api:
	docker-compose --profile api up

# Stop all services
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Clean up
clean:
	docker-compose down -v
	docker system prune -f

# Development mode
dev:
	docker-compose -f docker-compose.yml -f docker-compose.override.yml up frontend

# Run tests
test:
	python -m pytest tests/ -v

# Initial setup
setup:
	@echo "Setting up Mini Agentic Bot..."
	@if [ ! -f .env ]; then \
		echo "Creating .env file..."; \
		echo "GROQ_API_KEY=your_groq_api_key_here" > .env; \
		echo "Please edit .env file with your actual Groq API key"; \
	fi
	@echo "Setup complete! Run 'make up' to start the application."
