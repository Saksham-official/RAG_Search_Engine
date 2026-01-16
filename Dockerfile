FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads data

# Expose port 7860 (Hugging Face Spaces requirement)
EXPOSE 7860

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
