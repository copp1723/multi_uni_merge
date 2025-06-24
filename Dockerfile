# 🐳 Dockerfile for Swarm Multi-Agent System v3.0
# Optimized for Render deployment with frontend build

FROM node:18-slim AS frontend-builder

# Set working directory for frontend build
WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm ci --only=production

# Copy frontend source
COPY frontend/ ./

# Build frontend
RUN npm run build

# Python runtime stage
FROM python:3.11-slim

# Install system dependencies including curl for health check
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY config/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create necessary directories
RUN mkdir -p /tmp/swarm_workspace && \
    chmod 755 /tmp/swarm_workspace

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=backend/main.py
ENV FLASK_ENV=production
ENV HOST=0.0.0.0
ENV PORT=10000

# Expose port (Render uses 10000)
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:10000/api/health || exit 1

# Start the application
CMD ["python", "backend/main.py"]

