FROM python:3.11-slim

WORKDIR /app

# Install git for branch detection and build-essential for Chroma/Numpy
RUN apt-get update && apt-get install -y build-essential git && rm -rf /var/lib/apt/lists/*

# Install dependencies (cached)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create persistence directory
RUN mkdir -p /app/cortex_db

# Expose HTTP port for debug/Phase 2 endpoints (optional)
# Enable with: CORTEX_HTTP=true or --http flag
EXPOSE 8080

# Run the MCP server
# Optional flags:
#   --http          Enable HTTP server for debugging/Phase 2 features
# Optional env vars:
#   CORTEX_HTTP=true      Enable HTTP server
#   CORTEX_DEBUG=true     Enable debug logging
#   CORTEX_LOG_FILE=path  Log to file (e.g., /app/cortex_db/debug.log)
ENTRYPOINT ["python", "server.py"]
