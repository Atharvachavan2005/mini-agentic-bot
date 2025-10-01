#!/bin/bash

# Mini Agentic Bot Deployment Script

set -e

echo "🚀 Deploying Mini Agentic Bot..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it with your GROQ_API_KEY"
    exit 1
fi

# Check if GROQ_API_KEY is set
if ! grep -q "GROQ_API_KEY=" .env || grep -q "your_groq_api_key_here" .env; then
    echo "❌ Please set your GROQ_API_KEY in the .env file"
    exit 1
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build new images
echo "🔨 Building Docker images..."
docker-compose build --no-cache

# Start services
echo "▶️  Starting services..."
docker-compose up -d frontend

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Health check
echo "🔍 Running health check..."
python health_check.py

echo "✅ Deployment completed successfully!"
echo "🌐 Access the application at: http://localhost:8501"
