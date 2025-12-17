"""
Aggregator Microservice
Aggregates country-level emotion data
"""
"""
Aggregator Microservice
Aggregates country-level emotion data
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import os
import sys
import json
from collections import defaultdict, Counter
import re

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from database import SharedDatabase
from config import DB_PATH

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize database
db = SharedDatabase(DB_PATH)


class CountryEmotionAggregator:
    """Aggregates emotions at country level from events"""

    def aggregate_country(self, country):
        """Aggregate emotions for a specific country from events"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Normalize country name to lowercase for consistent lookup
        country_normalized = country.lower()
        
        cursor.execute('''
            SELECT emotion, confidence, post_ids
            FROM events
            WHERE LOWER(country) = ? AND is_analyzed = 1
        ''', (country_normalized,))
        
        rows = cursor.fetchall()

        if not rows:
            return None

        # Aggregate emotions and count total posts
        emotion_totals = defaultdict(float)
        event_count = 0
        total_post_count = 0

        for emotion, confidence, post_ids_json in rows:
            if emotion:
                emotion_totals[emotion] += confidence
                event_count += 1
                # Count actual posts in this event
                try:
                    post_ids = json.loads(post_ids_json)
                    total_post_count += len(post_ids)
                except (json.JSONDecodeError, TypeError):
                    pass  # Skip malformed post_ids

        if event_count == 0:
            return None
        
        # Check if we have any emotions (events might not have emotion set yet)
        if not emotion_totals:
            return None

        # Average emotions across events
        avg_emotions = {k: v/event_count for k, v in emotion_totals.items()}
        top_emotion = max(avg_emotions.items(), key=lambda x: x[1])[0]

        return {
            'country': country_normalized,
            'emotions': avg_emotions,
            'top_emotion': top_emotion,
            'total_posts': total_post_count  # Total posts across all events
        }

    def aggregate_all_countries(self):
        """Aggregate emotions for all countries from events"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT country
            FROM events
            WHERE is_analyzed = 1
        ''')
        
        countries = cursor.fetchall()

        results = []
        for (country,) in countries:
            agg = self.aggregate_country(country)
            if agg:
                results.append(agg)

        return results


# Initialize aggregator
aggregator = CountryEmotionAggregator()


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'aggregator'})


@app.route('/aggregate/country/<country>', methods=['POST'])
def aggregate_country(country):
    """Aggregate emotions for a specific country"""
    result = aggregator.aggregate_country(country)
    
    if result:
        # Store in database
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO country_emotions
                (country, emotions, top_emotion, total_posts)
                VALUES (?, ?, ?, ?)
            ''', (
                result['country'],
                json.dumps(result['emotions']),
                result['top_emotion'],
                result['total_posts']
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"Error storing aggregation: {e}")

        return jsonify(result)
    
    return jsonify({'error': 'No data for country'}), 404


@app.route('/aggregate/all', methods=['POST'])
def aggregate_all():
    """Aggregate emotions for all countries"""
    results = aggregator.aggregate_all_countries()
    
    # Store in database with updated timestamp
    conn = db.get_connection()
    cursor = conn.cursor()
    
    from datetime import datetime
    current_time = datetime.now().isoformat()
    
    for result in results:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO country_emotions
                (country, emotions, top_emotion, total_posts, last_updated)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                result['country'],
                json.dumps(result['emotions']),
                result['top_emotion'],
                result['total_posts'],
                current_time
            ))
        except Exception as e:
            logger.error(f"Error storing aggregation: {e}")
    
    conn.commit()

    return jsonify({
        'aggregated_countries': len(results),
        'results': results
    })


@app.route('/country/<country>', methods=['GET'])
def get_country_emotions(country):
    """Get aggregated emotions for a country with recent events"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Normalize country name for case-insensitive lookup
    country_normalized = country.lower()
    
    cursor.execute('''
        SELECT country, emotions, top_emotion, total_posts, last_updated
        FROM country_emotions
        WHERE LOWER(country) = ?
    ''', (country_normalized,))

    row = cursor.fetchone()
    if row:
        # Get all analyzed posts/events for this country (for topics)
        cursor.execute('''
            SELECT id, title, description, post_ids, event_date, post_count
            FROM events
            WHERE LOWER(country) = ? AND is_analyzed = 1
            ORDER BY event_date DESC
            LIMIT 20
        ''', (country_normalized,))
        
        all_items = []
        clustered_events = []  # Only events with 2+ posts
        
        for event_row in cursor.fetchall():
            post_ids = json.loads(event_row[3])
            # post_count is column 6 (index 5) - guaranteed to exist in query
            post_count = event_row[5]
            
            # Get URLs from posts - use proper parameterized query and deduplicate
            placeholders = ','.join('?' * len(post_ids))
            query = f'SELECT url FROM raw_posts WHERE id IN ({placeholders})'
            cursor.execute(query, post_ids)
            # Deduplicate URLs while preserving order
            urls = []
            seen = set()
            for r in cursor.fetchall():
                if r[0] and r[0] not in seen:
                    urls.append(r[0])
                    seen.add(r[0])
            
            item = {
                'title': event_row[1],
                'description': event_row[2],
                'event_date': event_row[4],
                'urls': urls,
                'post_count': post_count
            }
            
            all_items.append(item)
            
            # Only add to clustered_events if it has 2+ posts (actual event)
            if post_count >= 2:
                clustered_events.append(item)
        
        # Top topics: All items (including single posts)
        top_topics = [
            {
                'topic': item['title'],
                'count': item['post_count'],
                'description': item['description'],
                'urls': item['urls'][:1]
            }
            for item in all_items[:10]
        ]
        
        # Recent events: Only clustered events (2+ posts)
        recent_events = clustered_events[:10]
        
        return jsonify({
            'country': row[0],
            'emotions': json.loads(row[1]),
            'top_emotion': row[2],
            'total_posts': row[3],
            'last_updated': row[4],
            'recent_events': recent_events,  # Only clustered events (2+ posts)
            'top_topics': top_topics  # All items including single posts
        })
    
    return jsonify({'error': 'Country not found'}), 404


@app.route('/countries', methods=['GET'])
def get_all_countries():
    """Get all aggregated country emotions"""
    rows = db.execute_query('''
        SELECT country, emotions, top_emotion, total_posts, last_updated
        FROM country_emotions
    ''')

    results = []
    for row in rows:
        results.append({
            'country': row[0],
            'emotions': json.loads(row[1]),
            'top_emotion': row[2],
            'total_posts': row[3],
            'last_updated': row[4]
        })

    return jsonify({'countries': results, 'total': len(results)})


@app.route('/timeline/<country>', methods=['GET'])
def get_country_timeline(country):
    """Get emotion timeline for a country (last 7 days)"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    country_normalized = country.lower()
    
    # Get events grouped by day for the last 7 days
    cursor.execute('''
        SELECT 
            DATE(event_date) as day,
            AVG(confidence) as avg_confidence,
            COUNT(*) as event_count
        FROM events
        WHERE LOWER(country) = ? AND is_analyzed = 1
        AND event_date >= DATE('now', '-7 days')
        GROUP BY DATE(event_date)
        ORDER BY day ASC
    ''', (country_normalized,))
    
    rows = cursor.fetchall()
    
    # Convert to percentages for frontend
    timeline = []
    for row in rows:
        timeline.append({
            'day': row[0],
            'confidence': int(row[1] * 100),
            'event_count': row[2]
        })
    
    return jsonify({
        'country': country,
        'timeline': timeline,
        'days': len(timeline)
    })


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5003))
    app.run(host='0.0.0.0', port=port, debug=False)
