FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install PyTorch CPU-only first (much smaller than CUDA version)
# Increase timeout for slow connections
RUN pip install --no-cache-dir --timeout=1000 torch==2.1.1 --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download models at build time (optional - reduces startup time)
# NOTE: Commented out to avoid timeout during build - models will be downloaded on first use
# RUN python -c "from transformers import pipeline; \
#     pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base'); \
#     pipeline('zero-shot-classification', model='facebook/bart-large-mnli'); \
#     pipeline('ner', model='dslim/bert-base-NER')"

# Copy application code
COPY app.py .

# Expose service port
EXPOSE 5003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5003/api/health')" || exit 1

# Run the service
CMD ["python", "app.py"]
