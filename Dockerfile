# Course Assistant Sample
# Dockerfile for running the Course Assistant system

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
# (chỉ pytest — runtime không cần thư viện ngoài)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY data/ ./data/
COPY models/ ./models/
COPY input/ ./input/
COPY output/ ./output/

# Set Python path
ENV PYTHONPATH=/app

# Default command - run demo
CMD ["python", "-m", "src.main", "--mode", "demo"]
