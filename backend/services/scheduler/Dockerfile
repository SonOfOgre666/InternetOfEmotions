FROM python:3.11-slim

WORKDIR /app

# Copy requirements and app
COPY requirements.txt .
COPY app.py .

# Check if venv exists in host, otherwise create new one
RUN if [ -d "/backend/.venv" ]; then \
        echo "Using existing venv from backend"; \
        cp -r /backend/.venv /app/.venv; \
    else \
        echo "Creating new venv"; \
        python -m venv /app/.venv; \
    fi && \
    /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /app/.venv/bin/python -c "import requests; requests.get('http://localhost:5000/health', timeout=5)"

# Run application
CMD ["/app/.venv/bin/python", "app.py"]
