#!/usr/bin/env python3
"""
HTTP-based MCP Server for Unraid API
Works properly in Docker containers with HTTP transport.
"""
import os
import sys
import json
import logging
import httpx
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Load environment variables
load_dotenv()

# Configuration
UNRAID_API_URL = os.getenv("UNRAID_API_URL")
UNRAID_API_KEY = os.getenv("UNRAID_API_KEY")
PORT = int(os.getenv("UNRAID_MCP_PORT", "6970"))
HOST = os.getenv("UNRAID_MCP_HOST", "0.0.0.0")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("UnraidMCPServer")

if not UNRAID_API_URL or not UNRAID_API_KEY:
    logger.error("UNRAID_API_URL and UNRAID_API_KEY must be set")
    sys.exit(1)

# Initialize FastAPI app
app = FastAPI(
    title="Unraid MCP Server",
    description="HTTP-based MCP Server for Unraid API",
    version="1.0.0"
)

async def make_graphql_request(query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Helper function to make GraphQL requests to the Unraid API."""
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": UNRAID_API_KEY,
    }
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    logger.debug(f"Making GraphQL request to {UNRAID_API_URL}")
    
    verify_ssl = os.getenv("UNRAID_VERIFY_SSL", "true").lower() not in ["false", "0", "no"]
    
    async with httpx.AsyncClient(verify=verify_ssl, timeout=30.0) as client:
        response = await client.post(UNRAID_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        response_data = response.json()
        if "errors" in response_data and response_data["errors"]:
            error_details = "; ".join([err.get("message", str(err)) for err in response_data["errors"]])
            raise Exception(f"GraphQL API error: {error_details}")
        
        return response_data.get("data", {})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test connection to Unraid API
        query = """
        query HealthCheck {
          info {
            machineId
            time
          }
        }
        """
        
        response_data = await make_graphql_request(query)
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "server": "Unraid MCP Server HTTP",
            "version": "1.0.0",
            "api_connection": "ok",
            "unraid_system": {
                "machine_id": response_data.get("info", {}).get("machineId"),
                "time": response_data.get("info", {}).get("time")
            }
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )

@app.get("/")
async def root():
    """Root endpoint with server info"""
    return {
        "name": "Unraid MCP Server",
        "version": "1.0.0",
        "transport": "HTTP",
        "endpoints": {
            "/health": "Health check",
            "/system-info": "Get system information",
            "/array-status": "Get array status",
            "/docker/containers": "List Docker containers",
            "/tools": "List available tools"
        }
    }

@app.get("/tools")
async def list_tools():
    """List available MCP tools"""
    return {
        "tools": [
            {
                "name": "get_system_info",
                "description": "Get comprehensive Unraid system information including OS, CPU, and memory details"
            },
            {
                "name": "get_array_status", 
                "description": "Get current status of the Unraid storage array including capacity and disk health"
            },
            {
                "name": "list_docker_containers",
                "description": "List all Docker containers running on the Unraid system"
            },
            {
                "name": "health_check",
                "description": "Check the health status of the Unraid MCP server and system"
            }
        ]
    }

@app.get("/system-info")
async def get_system_info():
    """Get comprehensive system information"""
    query = """
    query GetSystemInfo {
      info {
        os { platform distro release hostname uptime }
        cpu { manufacturer brand cores threads }
        time
        machineId
        versions { unraid }
      }
    }
    """
    
    try:
        logger.info("Getting system information")
        response_data = await make_graphql_request(query)
        raw_info = response_data.get("info", {})
        
        if not raw_info:
            raise HTTPException(status_code=404, detail="No system info returned from Unraid API")

        # Process for human-readable output
        summary = {}
        if raw_info.get('os'):
            os_info = raw_info['os']
            summary['os'] = f"{os_info.get('distro', '')} {os_info.get('release', '')} ({os_info.get('platform', '')})"
            summary['hostname'] = os_info.get('hostname')
            summary['uptime'] = os_info.get('uptime')
        
        if raw_info.get('cpu'):
            cpu_info = raw_info['cpu']
            summary['cpu'] = f"{cpu_info.get('manufacturer', '')} {cpu_info.get('brand', '')} ({cpu_info.get('cores')} cores, {cpu_info.get('threads')} threads)"

        if raw_info.get('versions'):
            summary['unraid_version'] = raw_info['versions'].get('unraid')

        return {"summary": summary, "details": raw_info}

    except Exception as e:
        logger.error(f"Error in get_system_info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve system information: {str(e)}")

@app.get("/array-status")
async def get_array_status():
    """Get array status information"""
    query = """
    query GetArrayStatus {
      array {
        state
        capacity {
          kilobytes { free used total }
        }
        disks { id name status }
        parities { id name status }
      }
    }
    """
    
    try:
        logger.info("Getting array status")
        response_data = await make_graphql_request(query)
        raw_array_info = response_data.get("array", {})
        
        if not raw_array_info:
            raise HTTPException(status_code=404, detail="No array information returned from Unraid API")

        summary = {
            'state': raw_array_info.get('state'),
            'num_data_disks': len(raw_array_info.get('disks', [])),
            'num_parity_disks': len(raw_array_info.get('parities', []))
        }

        # Add capacity info if available
        if raw_array_info.get('capacity') and raw_array_info['capacity'].get('kilobytes'):
            kb_cap = raw_array_info['capacity']['kilobytes']
            def format_kb(k):
                if k is None: return "N/A"
                k = int(k)
                if k >= 1024*1024*1024: return f"{k / (1024*1024*1024):.2f} TB"
                if k >= 1024*1024: return f"{k / (1024*1024):.2f} GB"
                if k >= 1024: return f"{k / 1024:.2f} MB"
                return f"{k} KB"

            summary['capacity'] = {
                'total': format_kb(kb_cap.get('total')),
                'used': format_kb(kb_cap.get('used')),
                'free': format_kb(kb_cap.get('free'))
            }

        return {"summary": summary, "details": raw_array_info}

    except Exception as e:
        logger.error(f"Error in get_array_status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve array status: {str(e)}")

@app.get("/docker/containers")
async def list_docker_containers():
    """List Docker containers"""
    query = """
    query ListDockerContainers {
      docker {
        containers(skipCache: false) {
          id
          names
          image
          state
          status
          ports { privatePort publicPort type }
        }
      }
    }
    """
    
    try:
        logger.info("Listing Docker containers")
        response_data = await make_graphql_request(query)
        
        if response_data.get("docker"):
            containers = response_data["docker"].get("containers", [])
            
            # Add summary
            running = len([c for c in containers if c.get("state") == "running"])
            stopped = len([c for c in containers if c.get("state") == "exited"])
            
            return {
                "summary": {
                    "total": len(containers),
                    "running": running,
                    "stopped": stopped
                },
                "containers": containers
            }
        
        return {"summary": {"total": 0, "running": 0, "stopped": 0}, "containers": []}

    except Exception as e:
        logger.error(f"Error in list_docker_containers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list Docker containers: {str(e)}")

# Add startup event
@app.on_event("startup")
async def startup_event():
    logger.info(f"Unraid MCP Server starting on {HOST}:{PORT}")
    logger.info(f"API URL: {UNRAID_API_URL}")
    logger.info("Server ready!")

def main():
    """Main function to run the HTTP server"""
    logger.info("Starting Unraid MCP HTTP Server...")
    
    # Run the server
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()