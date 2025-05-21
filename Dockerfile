FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create storage directory for Indian Kanoon cache
RUN mkdir -p ./indian_kanoon_cache

# Expose the port the app runs on
EXPOSE 8080

# Use environment variable PORT if provided, default to 8080
ENV PORT=8080

# Command to run the application
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT} 