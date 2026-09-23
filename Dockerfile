# Course Assistant Sample
# Dockerfile for running the Course Assistant system

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"

# Copy application code
COPY src/ ./src/
COPY data/ ./data/
COPY input/ ./input/
COPY output/ ./output/

# Set Python path
ENV PYTHONPATH=/app

# Default command - run demo
CMD ["python", "-m", "src.main", "--mode", "demo"]
