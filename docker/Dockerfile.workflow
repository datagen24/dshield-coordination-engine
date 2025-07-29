# DShield Coordination Engine - Workflow Engine
# LangGraph-based analysis orchestration

FROM python:3.11-slim

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Create non-root user for security
RUN groupadd -r coordinator && \
    useradd -r -g coordinator -u 1000 coordinator && \
    mkdir -p /app && \
    chown coordinator:coordinator /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        gcc \
        g++ \
        libpq-dev \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Switch to non-root user
USER coordinator
WORKDIR /app

# Copy requirements first for better caching
COPY --chown=coordinator:coordinator requirements/ requirements/
COPY --chown=coordinator:coordinator pyproject.toml .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements/base.txt

# Copy application code
COPY --chown=coordinator:coordinator services/ services/
COPY --chown=coordinator:coordinator agents/ agents/
COPY --chown=coordinator:coordinator tools/ tools/

# Create necessary directories
RUN mkdir -p /app/logs /app/config

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health')" || exit 1

# Run the workflow engine
CMD ["python", "-m", "services.workflow.main"] 