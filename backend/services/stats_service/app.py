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

@app.route('/health')
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
    by_emotion = {row['emotion']: row['count'] for row in cursor.fetchall()}  # ✓ Fixed: renamed

    # Top countries as object (frontend expects object not array)
    cursor.execute("""
        SELECT country, COUNT(*) as count
        FROM raw_posts
        GROUP BY country
        ORDER BY count DESC
        LIMIT 10
    """)
    by_country = {row['country']: row['count'] for row in cursor.fetchall()}  # ✓ Fixed: object format

    cursor.close()
    conn.close()

    return jsonify({
        'total': total_posts,  # ✓ Fixed: renamed from 'total_posts'
        'by_emotion': by_emotion,  # ✓ Fixed: renamed from 'emotion_distribution'
        'by_country': by_country  # ✓ Fixed: object instead of array
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
