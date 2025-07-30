# Unraid MCP Server Makefile
# Simple commands for building and managing the MCP server

.PHONY: help build start stop restart logs clean deploy health test

# Default target
help:
	@echo "Unraid MCP Server - Available Commands:"
	@echo ""
	@echo "  make build    - Build the Docker image"
	@echo "  make start    - Start the MCP server"
	@echo "  make stop     - Stop the MCP server" 
	@echo "  make restart  - Restart the MCP server"
	@echo "  make logs     - Show container logs"
	@echo "  make health   - Check server health"
	@echo "  make clean    - Remove containers and images"
	@echo "  make deploy   - Run deployment script"
	@echo "  make test     - Test the server functionality"
	@echo ""

# Build the Docker image
build:
	@echo "🔨 Building Unraid MCP Server..."
	docker-compose build

# Start the server
start:
	@echo "🚀 Starting Unraid MCP Server..."
	docker-compose up -d
	@echo "✅ Server started!"

# Stop the server
stop:
	@echo "🛑 Stopping Unraid MCP Server..."
	docker-compose down
	@echo "✅ Server stopped!"

# Restart the server
restart:
	@echo "🔄 Restarting Unraid MCP Server..."
	docker-compose restart
	@echo "✅ Server restarted!"

# Show logs
logs:
	@echo "📋 Showing logs..."
	docker-compose logs -f

# Check health
health:
	@echo "🏥 Checking server health..."
	@docker-compose ps
	@echo ""
	@if docker-compose ps | grep -q "Up"; then \
		echo "✅ Server is running"; \
		PORT=$$(grep "UNRAID_MCP_PORT" .env 2>/dev/null | cut -d '=' -f2 | tr -d ' ' || echo "6970"); \
		echo "🌐 Access at: http://localhost:$$PORT"; \
	else \
		echo "❌ Server is not running"; \
	fi

# Clean up containers and images
clean:
	@echo "🧹 Cleaning up..."
	docker-compose down --rmi all --volumes --remove-orphans
	@echo "✅ Cleanup complete!"

# Run deployment script
deploy:
	@echo "🚀 Running deployment script..."
	./deploy.sh

# Test server functionality
test:
	@echo "🧪 Testing server functionality..."
	@if ! docker-compose ps | grep -q "Up"; then \
		echo "❌ Server is not running. Start with 'make start'"; \
		exit 1; \
	fi
	@PORT=$$(grep "UNRAID_MCP_PORT" .env 2>/dev/null | cut -d '=' -f2 | tr -d ' ' || echo "6970"); \
	echo "Testing health endpoint..."; \
	if curl -s -f "http://localhost:$$PORT/health" | grep -q "healthy"; then \
		echo "✅ Health check passed"; \
	else \
		echo "❌ Health check failed"; \
		exit 1; \
	fi; \
	echo "Testing system info endpoint..."; \
	if curl -s -f "http://localhost:$$PORT/system-info" > /dev/null; then \
		echo "✅ System info endpoint working"; \
	else \
		echo "⚠️  System info endpoint failed (may be due to API configuration)"; \
	fi