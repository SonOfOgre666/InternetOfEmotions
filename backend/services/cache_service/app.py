import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import redis
import json

app = Flask(__name__)
CORS(app)

redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://redis:6379/0').replace('redis://:','redis://:'))

@app.route('/health')
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
