"""
API Gateway Microservice
Central entry point for all client requests
Routes requests to appropriate microservices
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import logging
import os
import sys
import time
import threading
import requests
from pybreaker import CircuitBreaker, CircuitBreakerError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import json
from datetime import datetime
import sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from database import SharedDatabase
from config import DB_PATH
from metrics import (
    get_metrics, track_request_metrics, service_up,
    circuit_breaker_state, circuit_breaker_failures_total
)
from country_coordinates import get_coordinates

# Configure logging (move before sentry init to avoid NameError during import-time)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Sentry for error tracking
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

SENTRY_DSN = os.getenv('SENTRY_DSN', '')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,  # 10% performance monitoring
        environment=os.getenv('ENVIRONMENT', 'production'),
        release=os.getenv('VERSION', '1.0.0')
    )
    logger.info("✓ Sentry error tracking initialized")
else:
    logger.info("⚠ Sentry DSN not configured - error tracking disabled")

app = Flask(__name__)
CORS(app)

# Initialize database
db = SharedDatabase(DB_PATH)

# Service URLs
DATA_FETCHER_URL = os.getenv('DATA_FETCHER_URL', 'http://localhost:5001')
ML_ANALYZER_URL = os.getenv('ML_ANALYZER_URL', 'http://localhost:5005')
CONTENT_EXTRACTOR_URL = os.getenv('CONTENT_EXTRACTOR_URL', 'http://localhost:5007')
EVENT_EXTRACTOR_URL = os.getenv('EVENT_EXTRACTOR_URL', 'http://localhost:5004')
AGGREGATOR_URL = os.getenv('AGGREGATOR_URL', 'http://localhost:5003')

# Circuit breakers for each service (fail_max=5 failures, reset_timeout=60s)
data_fetcher_breaker = CircuitBreaker(fail_max=5, reset_timeout=60, name='data-fetcher')
content_extractor_breaker = CircuitBreaker(fail_max=5, reset_timeout=60, name='content-extractor')
event_extractor_breaker = CircuitBreaker(fail_max=5, reset_timeout=60, name='event-extractor')
ml_analyzer_breaker = CircuitBreaker(fail_max=5, reset_timeout=60, name='ml-analyzer')
aggregator_breaker = CircuitBreaker(fail_max=5, reset_timeout=60, name='aggregator')

# Background processing
processing_active = False
processing_thread = None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError)))
def call_service_with_retry(breaker, url, timeout):
    """Call a service with circuit breaker and retry logic"""
    return breaker.call(requests.post, url, timeout=timeout)

def background_processing():
    """Background task to process data pipeline"""
    global processing_active
    last_cleanup = datetime.now()
    
    while processing_active:
        try:
            # Cleanup old posts daily (once every 24 hours)
            if (datetime.now() - last_cleanup).total_seconds() > 86400:  # 24 hours
                logger.info("🧹 Running daily cleanup of old posts...")
                try:
                    response = requests.post(f"{DATA_FETCHER_URL}/cleanup", json={}, timeout=30)
                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"✓ Cleanup: {result.get('deleted_posts', 0)} posts, {result.get('deleted_events', 0)} events removed")
                    last_cleanup = datetime.now()
                except Exception as e:
                    logger.error(f"Cleanup error: {e}")
            
            # 1. Fetch new posts
            logger.info("📥 Fetching new posts...")
            try:
                response = requests.post(f"{DATA_FETCHER_URL}/fetch/next-batch", json={}, timeout=90)
                if response.status_code == 200:
                    logger.info("✓ Fetched posts")
                else:
                    logger.warning(f"Data fetcher returned status {response.status_code}")
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                logger.error(f"Network error fetching posts: {e}")
            except CircuitBreakerError:
                logger.error("Data fetcher circuit breaker open - service unavailable")
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error fetching posts: {e}")

            # 2. Extract content from link posts
            logger.info("📰 Extracting article content...")
            content_enriched = 0
            try:
                response = requests.post(f"{CONTENT_EXTRACTOR_URL}/process/pending", json={}, timeout=120)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        content_enriched = data.get('enriched', 0)
                        logger.info(f"✓ Extracted content ({content_enriched} posts enriched)")
                    except ValueError as e:
                        logger.error(f"Invalid JSON from content extractor: {e}")
                else:
                    logger.warning(f"Content extractor returned status {response.status_code}")
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                logger.error(f"Network error extracting content: {e}")
            except CircuitBreakerError:
                logger.error("Content extractor circuit breaker open - service unavailable")
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error extracting content: {e}")

            # 3. Extract events from posts (group similar posts) - only if we have processed posts
            logger.info("🎯 Extracting events from posts...")
            try:
                # Send empty JSON to trigger extraction for all countries
                response = requests.post(f"{EVENT_EXTRACTOR_URL}/extract_events", json={}, timeout=120)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.info(f"✓ Extracted {data.get('total_events', 0)} events")
                    except ValueError as e:
                        logger.error(f"Invalid JSON from event extractor: {e}")
                else:
                    logger.warning(f"Event extractor returned status {response.status_code}")
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                logger.error(f"Network error extracting events: {e}")
            except CircuitBreakerError:
                logger.error("Event extractor circuit breaker open - service unavailable")
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error extracting events: {e}")

            # 4. Analyze emotions for events (RoBERTa + VADER)
            logger.info("🧠 Emotion analysis of events...")
            try:
                response = requests.post(f"{ML_ANALYZER_URL}/process/pending", json={}, timeout=120)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.info(f"✓ Analyzed {data.get('processed', 0)} events")
                    except ValueError as e:
                        logger.error(f"Invalid JSON from ml-analyzer: {e}")
                else:
                    logger.warning(f"ML analyzer returned status {response.status_code}")
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                logger.error(f"Network error in emotion analysis: {e}")
            except CircuitBreakerError:
                logger.error("ML analyzer circuit breaker open - service unavailable")
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error in emotion analysis: {e}")

            # 5. Aggregate country emotions from events
            logger.info("📊 Aggregating country emotions...")
            try:
                response = requests.post(f"{AGGREGATOR_URL}/aggregate/all", json={}, timeout=60)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.info(f"✓ Aggregated emotions for {data.get('aggregated_countries', 0)} countries")
                    except ValueError as e:
                        logger.error(f"Invalid JSON from aggregator: {e}")
                else:
                    logger.warning(f"Aggregator returned status {response.status_code}")
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                logger.error(f"Network error aggregating: {e}")
            except CircuitBreakerError:
                logger.error("Aggregator circuit breaker open - service unavailable")
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error aggregating: {e}")

            # Wait before next cycle
            time.sleep(30)  # 30 seconds for faster data flow

        except KeyboardInterrupt:
            logger.info("Background processing interrupted")
            processing_active = False
        except Exception as e:
            logger.exception(f"Unexpected error in background processing: {e}")
            time.sleep(10)  # Faster recovery from errors


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'api-gateway'})


@app.route('/api/health', methods=['GET'])
def api_health():
    """API health check - frontend compatible"""
    from datetime import datetime
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        db_posts = cursor.execute('SELECT COUNT(*) FROM raw_posts').fetchone()[0]
    except Exception as e:
        logger.warning(f"Health check DB query failed: {e}")
        db_posts = 0
    
    return jsonify({
        'status': 'healthy',
        'demo_mode': False,
        'db_posts': db_posts,
        'last_fetch': datetime.now().isoformat()
    })


@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    metrics_data, content_type = get_metrics()
    return Response(metrics_data, mimetype=content_type)


@app.route('/api/emotions', methods=['GET'])
@track_request_metrics
def get_emotions():
    """Get all country emotions for the map - Frontend compatible format"""
    try:
        response = requests.get(f"{AGGREGATOR_URL}/countries", timeout=10)
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError as e:
            logger.error(f"Invalid JSON from aggregator: {e}")
            return jsonify({'error': 'Invalid response format'}), 502
        
        # Import country coordinates from shared module
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
        from country_coordinates import get_coordinates
        
        # Transform for frontend - matching expected format
        emotions_data = []
        for country_data in data.get('countries', []):
            coords = get_coordinates(country_data['country'])
            emotions = country_data.get('emotions', {})
            top_emotion = country_data.get('top_emotion', 'neutral')
            
            # Calculate confidence from emotion scores
            confidence = emotions.get(top_emotion, 0.5) if emotions else 0.5
            
            emotions_data.append({
                'id': f"{country_data['country']}-{top_emotion}",
                'country': country_data['country'],
                'coords': coords,
                'emotion': top_emotion,  # Frontend expects 'emotion' not 'topEmotion'
                'confidence': confidence,
                'post_count': country_data.get('total_posts', 0),
                'text': f"Country emotion analysis for {country_data['country']}",
                'timestamp': country_data.get('last_updated', datetime.now().isoformat())
            })
        
        # Return in frontend-expected format
        return jsonify({
            'emotions': emotions_data,
            'count': len(emotions_data),
            'demo_mode': False
        })
    except requests.exceptions.Timeout:
        logger.error("Timeout fetching emotions from aggregator")
        return jsonify({'error': 'Service timeout'}), 504
    except requests.exceptions.ConnectionError:
        logger.error("Connection error to aggregator service")
        return jsonify({'error': 'Service unavailable'}), 503
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error fetching emotions: {e}")
        return jsonify({'error': 'Upstream service error'}), 502
    except (KeyError, ValueError) as e:
        logger.error(f"Data format error: {e}")
        return jsonify({'error': 'Invalid data format'}), 500
    except Exception as e:
        logger.exception(f"Unexpected error fetching emotions: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get global statistics - Frontend compatible format"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get stats from events
        total_countries_row = cursor.execute('SELECT COUNT(DISTINCT country) FROM events WHERE is_analyzed = 1').fetchone()
        total_countries = total_countries_row[0] if total_countries_row else 0
        
        total_events_row = cursor.execute('SELECT COUNT(*) FROM events WHERE is_analyzed = 1').fetchone()
        total_events = total_events_row[0] if total_events_row else 0
        
        # Get top emotions
        by_emotion = {}
        rows = cursor.execute('SELECT emotion, COUNT(*) FROM events WHERE is_analyzed = 1 GROUP BY emotion').fetchall()
        for emotion, count in rows:
            if emotion:
                by_emotion[emotion] = count
        
        # Get country breakdown
        by_country = {}
        country_rows = cursor.execute('SELECT country, COUNT(*) FROM events WHERE is_analyzed = 1 GROUP BY country').fetchall()
        for country, count in country_rows:
            if country:
                by_country[country] = count

        # Frontend-compatible format
        return jsonify({
            'total': total_events,
            'by_emotion': by_emotion,
            'by_country': by_country,
            'countries_ready': total_countries
        })
    except sqlite3.Error as e:
        logger.error(f"Database error fetching stats: {e}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logger.exception(f"Unexpected error fetching stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/country/<country>', methods=['GET'])
def get_country_details(country):
    """Get detailed data for a specific country including recent events"""
    try:
        # Normalize country name to lowercase for consistent lookup
        country_normalized = country.lower()
        
        # Get aggregated emotions with events
        response = requests.get(f"{AGGREGATOR_URL}/country/{country_normalized}", timeout=10)
        response.raise_for_status()
        country_data = response.json()
        
        # Data already includes recent_events from aggregator
        return jsonify(country_data)
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching country details for {country}")
        return jsonify({'error': 'Service timeout'}), 504
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error fetching country {country}")
        return jsonify({'error': 'Service unavailable'}), 503
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({'error': 'Country not found'}), 404
        logger.error(f"HTTP error fetching country {country}: {e}")
        return jsonify({'error': 'Upstream service error'}), 502
    except Exception as e:
        logger.exception(f"Unexpected error fetching country {country}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/timeline/<country>', methods=['GET'])
def get_country_timeline(country):
    """Get emotion timeline for a specific country"""
    try:
        # Normalize country name to lowercase for consistent lookup
        country_normalized = country.lower()
        
        # Get timeline from aggregator
        response = requests.get(f"{AGGREGATOR_URL}/timeline/{country_normalized}", timeout=10)
        response.raise_for_status()
        timeline_data = response.json()
        
        return jsonify(timeline_data)
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching timeline for {country}")
        return jsonify({'error': 'Service timeout', 'timeline': [], 'days': 0}), 504
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error fetching timeline for {country}")
        return jsonify({'error': 'Service unavailable', 'timeline': [], 'days': 0}), 503
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({'error': 'Country not found', 'timeline': [], 'days': 0}), 404
        logger.error(f"HTTP error fetching timeline for {country}: {e}")
        return jsonify({'error': 'Upstream service error', 'timeline': [], 'days': 0}), 502
    except Exception as e:
        logger.exception(f"Unexpected error fetching timeline for {country}: {e}")
        return jsonify({'error': 'Internal server error', 'timeline': [], 'days': 0}), 500


@app.route('/api/posts/stream', methods=['GET'])
def stream_posts():
    """SSE endpoint for real-time event updates"""
    def generate():
        # Run indefinitely until client disconnects
        while True:
            try:
                conn = db.get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, title, description, country, event_date, emotion
                    FROM events
                    WHERE is_analyzed = 1
                    ORDER BY created_at DESC
                    LIMIT 5
                ''')
                
                rows = cursor.fetchall()

                events = []
                for row in rows:
                    events.append({
                        'id': row[0],
                        'title': row[1],
                        'description': row[2][:200],
                        'country': row[3],
                        'timestamp': row[4],
                        'emotion': row[5]
                    })

                yield f"data: {json.dumps(events)}\n\n"
                time.sleep(10)

            except GeneratorExit:
                logger.info("SSE client disconnected")
                break
            except Exception as e:
                logger.error(f"Stream error: {e}")
                time.sleep(10)

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/process/start', methods=['POST'])
def start_processing():
    """Start background processing"""
    global processing_active, processing_thread

    if not processing_active:
        processing_active = True
        processing_thread = threading.Thread(target=background_processing, daemon=True)
        processing_thread.start()
        return jsonify({'status': 'Processing started'})
    
    return jsonify({'status': 'Already running'})


@app.route('/api/process/stop', methods=['POST'])
def stop_processing():
    """Stop background processing"""
    global processing_active

    processing_active = False
    return jsonify({'status': 'Processing stopped'})


@app.route('/api/progress', methods=['GET'])
def get_progress():
    """Get processing progress"""
    try:
        response = requests.get(f"{DATA_FETCHER_URL}/stats", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
    except Exception as e:
        logger.error(f"Error fetching progress: {e}")

    return jsonify({'error': 'Unable to fetch progress'}), 500


if __name__ == '__main__':
    # Start background processing
    processing_active = True
    processing_thread = threading.Thread(target=background_processing, daemon=True)
    processing_thread.start()

    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
