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
    'stats': os.getenv('STATS_SERVICE_URL', 'http://stats_service:5008'),
    'scheduler': os.getenv('SCHEDULER_URL', 'http://scheduler:5010'),
    'collective_analyzer': os.getenv('COLLECTIVE_ANALYZER_URL', 'http://collective_analyzer:5011'),
    'cross_country_detector': os.getenv('CROSS_COUNTRY_DETECTOR_URL', 'http://cross_country_detector:5012')
}

@app.route('/health')
@app.route('/api/health')
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
        # Check if this is a streaming request
        is_stream = 'stream' in path or 'stream' in request.args
        
        resp = requests.request(
            method=request.method,
            url=url,
            headers={key: value for key, value in request.headers if key != 'Host'},
            data=request.get_data(),
            params=request.args,
            timeout=None if is_stream else 30,
            allow_redirects=False,
            stream=is_stream
        )

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for name, value in resp.raw.headers.items() if name.lower() not in excluded_headers]

        if is_stream:
            def generate():
                for line in resp.iter_lines():
                    if line:
                        yield line + b'\n'
            return Response(generate(), resp.status_code, headers)

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

@app.route('/api/posts/stream')  # ✓ Added: missing SSE endpoint
def posts_stream():
    return proxy('stats', 'stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
