#!/bin/bash

# Unraid MCP Server Deployment Script
# This script makes it easy to deploy the MCP server on your Unraid system

set -e

echo "🚀 Unraid MCP Server Deployment"
echo "================================"

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

# Check if running on Unraid
if [ ! -f /etc/unraid-version ]; then
    print_warning "This script is designed for Unraid systems, but can work on other Docker-enabled systems."
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH!"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed or not in PATH!"
    print_status "Installing docker-compose..."
    
    # Try to install docker-compose
    if command -v pip3 &> /dev/null; then
        pip3 install docker-compose
    else
        print_error "Cannot install docker-compose. Please install it manually."
        exit 1
    fi
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file from template..."
    cp .env.example .env
    
    print_warning "Please edit .env file with your Unraid server details:"
    print_status "  - UNRAID_API_URL: Your Unraid server's GraphQL API URL"
    print_status "  - UNRAID_API_KEY: Your Unraid API key"
    print_status ""
    print_status "Example:"
    print_status "  UNRAID_API_URL=https://192.168.1.100/api/graphql"
    print_status "  UNRAID_API_KEY=your-api-key-here"
    print_status ""
    
    read -p "Press Enter after configuring .env file, or Ctrl+C to exit..."
fi

# Create logs directory
print_status "Creating logs directory..."
mkdir -p logs

# Check if .env file has required variables
if ! grep -q "UNRAID_API_URL=.*[^=]" .env || ! grep -q "UNRAID_API_KEY=.*[^=]" .env; then
    print_error "Please configure UNRAID_API_URL and UNRAID_API_KEY in .env file"
    exit 1
fi

# Build and start the container
print_status "Building and starting Unraid MCP Server..."
docker-compose up -d --build

# Wait for container to be ready
print_status "Waiting for container to be ready..."
sleep 10

# Check container status
if docker-compose ps | grep -q "Up"; then
    print_success "Unraid MCP Server is running!"
    
    # Get the port from .env or use default
    PORT=$(grep "UNRAID_MCP_PORT" .env | cut -d '=' -f2 | tr -d ' ' || echo "6970")
    
    print_status "Server is accessible at:"
    print_status "  - Local: http://localhost:${PORT}"
    print_status "  - Network: http://$(hostname -I | awk '{print $1}'):${PORT}"
    print_status ""
    print_status "Logs: docker-compose logs -f"
    print_status "Stop: docker-compose down"
    print_status "Restart: docker-compose restart"
else
    print_error "Failed to start Unraid MCP Server"
    print_status "Check logs with: docker-compose logs"
    exit 1
fi

print_success "Deployment complete! 🎉"