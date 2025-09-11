# Fashion-CLIP Cloud Run Dockerfile for production deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from backend (includes all dependencies)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Fashion-CLIP server
COPY fashion_clip_server.py .

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the Fashion-CLIP server
CMD ["python", "fashion_clip_server.py"]
