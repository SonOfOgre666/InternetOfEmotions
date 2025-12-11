import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return psycopg2.connect(os.getenv('DATABASE_URL'), cursor_factory=RealDictCursor)

@app.route('/health')
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
