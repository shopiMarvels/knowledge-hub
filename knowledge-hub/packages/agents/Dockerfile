FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY packages/agents/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire repository for package access
COPY . .

# Copy worker.py and jobs to root for the CMD to find them
COPY packages/agents/worker.py .
COPY packages/agents/jobs ./jobs

# Create directories for MCP tools and data
RUN mkdir -p /app/mcp_tools /app/data /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the worker
CMD ["python", "worker.py"]
