FROM python:3.11-slim

WORKDIR /app

# Copy requirements and app
COPY requirements.txt .
COPY app.py .

# Install PyTorch CPU-only first (much smaller than CUDA version)
# Increase timeout for slow connections
RUN pip install --no-cache-dir --timeout=1000 torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Note: Model downloads at runtime on first use
# facebook/bart-large-mnli (~1.6GB) will be cached in container

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health', timeout=5)"

# Run application
CMD ["python", "app.py"]
