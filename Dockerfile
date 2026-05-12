# Use a slim Python image for efficiency
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Default root build should match the production backend API
CMD ["uvicorn", "Backend.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
