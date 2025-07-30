# Multi-stage build for smaller final image
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final runtime stage
FROM python:3.11-slim

# Create non-root user for security
RUN groupadd -r unraid && useradd -r -g unraid unraid

# Set the working directory in the container
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/unraid/.local

# Copy application code
COPY unraid-mcp-server-simple.py ./unraid-mcp-server.py
COPY .env.example .

# Create logs directory and set permissions
RUN mkdir -p /app/logs && chown -R unraid:unraid /app

# Switch to non-root user
USER unraid

# Add local Python packages to PATH
ENV PATH=/home/unraid/.local/bin:$PATH

# Define environment variables (defaults, can be overridden at runtime)
ENV UNRAID_MCP_PORT=6970
ENV UNRAID_MCP_HOST="0.0.0.0"
ENV UNRAID_MCP_TRANSPORT="streamable-http"
ENV UNRAID_API_URL=""
ENV UNRAID_API_KEY=""
ENV UNRAID_VERIFY_SSL="true"
ENV UNRAID_MCP_LOG_LEVEL="INFO"
ENV UNRAID_MCP_LOG_FILE="/app/logs/unraid-mcp.log"

# Expose port (MCP typically runs on stdio, but we may add HTTP later)
EXPOSE 6970

# Run unraid-mcp-server.py when the container launches
CMD ["python", "unraid-mcp-server.py"]
