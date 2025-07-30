#!/usr/bin/env python3
"""
Simple MCP Server for Unraid API
A working implementation using the standard MCP library.
"""
import os
import sys
import json
import logging
import httpx
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

# Load environment variables
load_dotenv()

# Configuration
UNRAID_API_URL = os.getenv("UNRAID_API_URL")
UNRAID_API_KEY = os.getenv("UNRAID_API_KEY")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("UnraidMCPServer")

if not UNRAID_API_URL or not UNRAID_API_KEY:
    logger.error("UNRAID_API_URL and UNRAID_API_KEY must be set")
    sys.exit(1)

# Initialize MCP Server
server = Server("unraid-mcp")

async def make_graphql_request(query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Helper function to make GraphQL requests to the Unraid API."""
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": UNRAID_API_KEY,
    }
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(UNRAID_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        response_data = response.json()
        if "errors" in response_data and response_data["errors"]:
            error_details = "; ".join([err.get("message", str(err)) for err in response_data["errors"]])
            raise Exception(f"GraphQL API error: {error_details}")
        
        return response_data.get("data", {})

@server.list_tools()
async def list_tools():
    """List available tools"""
    return [
        Tool(
            name="get_system_info",
            description="Get comprehensive Unraid system information including OS, CPU, and memory details"
        ),
        Tool(
            name="get_array_status", 
            description="Get current status of the Unraid storage array including capacity and disk health"
        ),
        Tool(
            name="list_docker_containers",
            description="List all Docker containers running on the Unraid system"
        ),
        Tool(
            name="health_check",
            description="Check the health status of the Unraid MCP server and system"
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls"""
    try:
        if name == "get_system_info":
            result = await get_system_info()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_array_status":
            result = await get_array_status()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "list_docker_containers":
            result = await list_docker_containers()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "health_check":
            result = await health_check()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        else:
            raise Exception(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_system_info() -> Dict[str, Any]:
    """Get comprehensive system information"""
    query = """
    query GetSystemInfo {
      info {
        os { platform distro release hostname uptime }
        cpu { manufacturer brand cores threads }
        time
        machineId
      }
    }
    """
    
    try:
        response_data = await make_graphql_request(query)
        raw_info = response_data.get("info", {})
        
        if not raw_info:
            raise Exception("No system info returned from Unraid API")

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

        return {"summary": summary, "details": raw_info}

    except Exception as e:
        logger.error(f"Error in get_system_info: {e}")
        raise Exception(f"Failed to retrieve system information: {str(e)}")

async def get_array_status() -> Dict[str, Any]:
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
        response_data = await make_graphql_request(query)
        raw_array_info = response_data.get("array", {})
        
        if not raw_array_info:
            raise Exception("No array information returned from Unraid API")

        summary = {
            'state': raw_array_info.get('state'),
            'num_data_disks': len(raw_array_info.get('disks', [])),
            'num_parity_disks': len(raw_array_info.get('parities', []))
        }

        return {"summary": summary, "details": raw_array_info}

    except Exception as e:
        logger.error(f"Error in get_array_status: {e}")
        raise Exception(f"Failed to retrieve array status: {str(e)}")

async def list_docker_containers() -> List[Dict[str, Any]]:
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
        }
      }
    }
    """
    
    try:
        response_data = await make_graphql_request(query)
        if response_data.get("docker"):
            return response_data["docker"].get("containers", [])
        return []

    except Exception as e:
        logger.error(f"Error in list_docker_containers: {e}")
        raise Exception(f"Failed to list Docker containers: {str(e)}")

async def health_check() -> Dict[str, Any]:
    """Check system health"""
    try:
        # Simple health check - try to get system info
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
            "server": "Unraid MCP Server",
            "api_connection": "ok",
            "unraid_system": response_data.get("info", {})
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

async def main():
    """Main function to run the server"""
    logger.info("Starting Unraid MCP Server...")
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())