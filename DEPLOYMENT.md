# Unraid MCP Server Deployment Guide

This guide will help you easily deploy the Unraid MCP Server on your Unraid system.

## Quick Start

### Option 1: Automated Deployment (Recommended)

1. **Clone the repository:**
   ```bash
   cd /mnt/user/appdata
   git clone https://github.com/andrewgari/unraid-mcp.git
   cd unraid-mcp
   ```

2. **Run the deployment script:**
   ```bash
   ./deploy.sh
   ```

3. **Configure your settings** when prompted:
   - Edit the `.env` file with your Unraid server details
   - Set `UNRAID_API_URL` to your server's GraphQL endpoint
   - Set `UNRAID_API_KEY` to your API key

### Option 2: Manual Deployment

1. **Create environment file:**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your settings
   ```

2. **Build and start:**
   ```bash
   docker-compose up -d --build
   ```

### Option 3: Using Makefile

```bash
make deploy    # Run automated deployment
# or
make build     # Build the image
make start     # Start the server
```

## Configuration

### Required Settings

Edit `.env` file with these required values:

```bash
# Your Unraid server's GraphQL API endpoint
UNRAID_API_URL=https://your-unraid-server.local/api/graphql

# Your Unraid API key (generate from Unraid web interface)
UNRAID_API_KEY=your-api-key-here
```

### Optional Settings

```bash
# Server configuration
UNRAID_MCP_PORT=6970
UNRAID_MCP_HOST=0.0.0.0
UNRAID_MCP_TRANSPORT=streamable-http

# SSL verification
UNRAID_VERIFY_SSL=true

# Logging
UNRAID_MCP_LOG_LEVEL=INFO
UNRAID_MCP_LOG_FILE=unraid-mcp.log
```

## Obtaining Your API Key

1. Open your Unraid web interface
2. Go to **Settings** → **Management** → **API**
3. Click **Generate API Key** 
4. Copy the generated key to your `.env` file

## Directory Structure

```
/mnt/user/appdata/unraid-mcp/
├── .env                    # Your configuration
├── docker-compose.yml     # Docker service definition
├── logs/                  # Log files
├── unraid-mcp-server.py   # Main server code
└── deploy.sh             # Deployment script
```

## Management Commands

### Using Make Commands
```bash
make start     # Start the server
make stop      # Stop the server
make restart   # Restart the server
make logs      # View logs
make health    # Check server status
make clean     # Remove all containers/images
```

### Using Docker Compose
```bash
docker-compose up -d       # Start in background
docker-compose down        # Stop and remove
docker-compose logs -f     # Follow logs
docker-compose restart     # Restart service
```

### Using Docker Commands
```bash
docker ps                          # List running containers
docker logs unraid-mcp-server     # View logs
docker restart unraid-mcp-server  # Restart container
```

## Accessing the Server

Once deployed, the server will be available at:
- **Local:** `http://localhost:6970`
- **Network:** `http://YOUR_UNRAID_IP:6970`

## Health Check

The container includes automatic health checks. Check status with:
```bash
docker ps                    # Shows health status
make health                  # Custom health check
curl http://localhost:6970/health  # Direct health endpoint
```

## Logs

View logs in several ways:
```bash
make logs                    # Follow live logs
docker-compose logs         # View all logs
cat logs/unraid-mcp.log     # View log file
```

## Troubleshooting

### Container Won't Start
1. Check your `.env` configuration
2. Verify API URL is accessible
3. Check logs: `make logs`
4. Ensure port 6970 isn't in use

### Connection Issues
1. Verify Unraid API is enabled
2. Check firewall settings
3. Confirm API key is valid
4. Test API URL in browser

### Permission Issues
1. Check file permissions: `chmod +x deploy.sh`
2. Ensure Docker has access to directories
3. Run with proper user permissions

## Unraid Integration

### Community Applications (CA)

To make this available through Community Applications:

1. Create template in `/boot/config/plugins/dockerMan/templates-user/`
2. Use the provided docker-compose configuration
3. Set WebUI to `http://[IP]:[PORT:6970]`

### User Scripts

Add to User Scripts plugin for automatic management:
```bash
#!/bin/bash
cd /mnt/user/appdata/unraid-mcp
make start
```

## Security Notes

- The container runs as non-root user for security
- API keys are passed via environment variables
- Logs are stored in mounted volume
- Health checks ensure service availability

## Updates

To update to the latest version:
```bash
cd /mnt/user/appdata/unraid-mcp
git pull
make stop
make build
make start
```

## Support

If you encounter issues:
1. Check the logs: `make logs`
2. Verify configuration in `.env`
3. Test network connectivity to Unraid API
4. Open an issue on GitHub with log details