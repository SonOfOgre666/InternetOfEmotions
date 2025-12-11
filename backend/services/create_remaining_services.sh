#!/bin/bash
# Auto-generate remaining microservices
# Run: bash services/create_remaining_services.sh

set -e

echo "🚀 Creating remaining microservices..."
echo "============================================"

cd "$(dirname "$0")"

# ============================================================================
# Cache Service (Redis)
# ============================================================================
echo "📦 Creating Cache Service..."

cat > cache_service/app.py << 'EOF'
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import redis
import json

app = Flask(__name__)
CORS(app)

redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://redis:6379/0').replace('redis://:','redis://:'))

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'cache_service'})

@app.route('/api/get/<key>')
def get_cache(key):
    try:
        value = redis_client.get(key)
        return jsonify({'key': key, 'value': json.loads(value) if value else None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/set', methods=['POST'])
def set_cache():
    try:
        data = request.get_json()
        redis_client.setex(data['key'], data.get('ttl', 30), json.dumps(data['value']))
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006)
EOF

cat > cache_service/requirements.txt << 'EOF'
flask==3.0.0
flask-cors==4.0.0
redis==5.0.1
python-dotenv==1.0.0
EOF

cat > cache_service/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5006
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 CMD python -c "import requests; requests.get('http://localhost:5006/api/health')" || exit 1
CMD ["python", "app.py"]
EOF

echo "✅ Cache Service created"

# ============================================================================
# Search Service (Elasticsearch)
# ============================================================================
echo "🔍 Creating Search Service..."

cat > search_service/app.py << 'EOF'
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return psycopg2.connect(os.getenv('DATABASE_URL'), cursor_factory=RealDictCursor)

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'search_service'})

@app.route('/api/search')
def search():
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 20))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Simple keyword search
    cursor.execute("""
        SELECT rp.*, ap.emotion, ap.confidence
        FROM raw_posts rp
        LEFT JOIN analyzed_posts ap ON rp.id = ap.post_id
        WHERE rp.text ILIKE %s OR rp.title ILIKE %s
        ORDER BY rp.reddit_created_at DESC
        LIMIT %s
    """, (f'%{query}%', f'%{query}%', limit))

    results = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()

    return jsonify({'results': results, 'query': query, 'count': len(results)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5007)
EOF

cat > search_service/requirements.txt << 'EOF'
flask==3.0.0
flask-cors==4.0.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
EOF

cat > search_service/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc postgresql-client && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5007
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 CMD python -c "import requests; requests.get('http://localhost:5007/api/health')" || exit 1
CMD ["python", "app.py"]
EOF

echo "✅ Search Service created"

# ============================================================================
# Stats Service
# ============================================================================
echo "📊 Creating Stats Service..."

cat > stats_service/app.py << 'EOF'
import os
from flask import Flask, jsonify, Response
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import time

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return psycopg2.connect(os.getenv('DATABASE_URL'), cursor_factory=RealDictCursor)

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'stats_service'})

@app.route('/api/stats')
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total posts
    cursor.execute("SELECT COUNT(*) as count FROM raw_posts")
    total_posts = cursor.fetchone()['count']

    # Total analyzed
    cursor.execute("SELECT COUNT(*) as count FROM analyzed_posts")
    analyzed_posts = cursor.fetchone()['count']

    # Emotion distribution
    cursor.execute("""
        SELECT emotion, COUNT(*) as count
        FROM analyzed_posts
        GROUP BY emotion
        ORDER BY count DESC
    """)
    emotions = {row['emotion']: row['count'] for row in cursor.fetchall()}

    # Top countries
    cursor.execute("""
        SELECT country, COUNT(*) as count
        FROM raw_posts
        GROUP BY country
        ORDER BY count DESC
        LIMIT 10
    """)
    top_countries = [dict(row) for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return jsonify({
        'total_posts': total_posts,
        'analyzed_posts': analyzed_posts,
        'emotion_distribution': emotions,
        'top_countries': top_countries
    })

@app.route('/api/stream')
def stream():
    def generate():
        while True:
            data = get_stats()
            yield f"data: {json.dumps(data.get_json())}\n\n"
            time.sleep(30)

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5008)
EOF

cat > stats_service/requirements.txt << 'EOF'
flask==3.0.0
flask-cors==4.0.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
EOF

cat > stats_service/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc postgresql-client && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5008
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 CMD python -c "import requests; requests.get('http://localhost:5008/api/health')" || exit 1
CMD ["python", "app.py"]
EOF

echo "✅ Stats Service created"

# ============================================================================
# API Gateway
# ============================================================================
echo "🌐 Creating API Gateway..."

cat > api_gateway/app.py << 'EOF'
import os
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)

SERVICES = {
    'post_fetcher': os.getenv('POST_FETCHER_URL', 'http://post_fetcher:5001'),
    'url_extractor': os.getenv('URL_EXTRACTOR_URL', 'http://url_extractor:5002'),
    'ml_analyzer': os.getenv('ML_ANALYZER_URL', 'http://ml_analyzer:5003'),
    'db_cleanup': os.getenv('DB_CLEANUP_URL', 'http://db_cleanup:5004'),
    'country_aggregation': os.getenv('COUNTRY_AGGREGATION_URL', 'http://country_aggregation:5005'),
    'cache': os.getenv('CACHE_SERVICE_URL', 'http://cache_service:5006'),
    'search': os.getenv('SEARCH_SERVICE_URL', 'http://search_service:5007'),
    'stats': os.getenv('STATS_SERVICE_URL', 'http://stats_service:5008')
}

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'api_gateway',
        'timestamp': datetime.now().isoformat(),
        'services': list(SERVICES.keys())
    })

@app.route('/api/<service_name>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(service_name, path):
    if service_name not in SERVICES:
        return jsonify({'error': 'Service not found', 'available': list(SERVICES.keys())}), 404

    url = f"{SERVICES[service_name]}/api/{path}"

    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers={key: value for key, value in request.headers if key != 'Host'},
            data=request.get_data(),
            params=request.args,
            timeout=30,
            allow_redirects=False
        )

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for name, value in resp.raw.headers.items() if name.lower() not in excluded_headers]

        return Response(resp.content, resp.status_code, headers)

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Service timeout', 'service': service_name}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Service unavailable', 'service': service_name}), 503
    except Exception as e:
        return jsonify({'error': str(e), 'service': service_name}), 500

# Direct routes for convenience
@app.route('/api/emotions')
def get_emotions():
    return proxy('country_aggregation', 'countries')

@app.route('/api/stats')
def get_stats():
    return proxy('stats', 'stats')

@app.route('/api/search')
def search():
    return proxy('search', 'search')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
EOF

cat > api_gateway/requirements.txt << 'EOF'
flask==3.0.0
flask-cors==4.0.0
requests==2.31.0
python-dotenv==1.0.0
EOF

cat > api_gateway/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1
CMD ["python", "app.py"]
EOF

echo "✅ API Gateway created"

echo ""
echo "============================================"
echo "✅ ALL SERVICES CREATED SUCCESSFULLY!"
echo "============================================"
echo ""
echo "Services created:"
echo "  ✅ Post Fetcher (5001)"
echo "  ✅ URL Extractor (5002)"
echo "  ✅ ML Analyzer (5003)"
echo "  ✅ DB Cleanup (5004)"
echo "  ✅ Country Aggregation (5005)"
echo "  ✅ Cache Service (5006)"
echo "  ✅ Search Service (5007)"
echo "  ✅ Stats Service (5008)"
echo "  ✅ API Gateway (8000)"
echo ""
echo "Next steps:"
echo "  1. cd .."
echo "  2. docker compose -f docker-compose.microservices.yml build"
echo "  3. docker compose -f docker-compose.microservices.yml up -d"
echo "  4. docker compose -f docker-compose.microservices.yml logs -f"
echo ""
