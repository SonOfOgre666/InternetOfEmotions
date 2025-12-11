"""
Country Aggregation Service
Microservice #5: Aggregate emotions at country level

Features:
- Listens to 'post.analyzed' events
- 4-algorithm consensus (majority, weighted, intensity, median)
- Updates country-level emotion statistics
- Publishes 'country.updated' events
"""

import os
import logging
import json
import time
import threading
from datetime import datetime
from typing import Dict, List
from collections import Counter
from flask import Flask, jsonify, request
from flask_cors import CORS
import pika
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from country_coordinates import COUNTRY_COORDS  # ✓ Added

logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - [COUNTRY_AGG] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SERVICE_PORT = int(os.getenv('SERVICE_PORT', 5005))
DATABASE_URL = os.getenv('DATABASE_URL')
RABBITMQ_URL = os.getenv('RABBITMQ_URL')

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

class RabbitMQClient:
    def __init__(self, url):
        self.url = url
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        self.connection = pika.BlockingConnection(pika.URLParameters(self.url))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='posts_exchange', exchange_type='topic', durable=True)
        result = self.channel.queue_declare(queue='country_aggregation_queue', durable=True)
        self.queue_name = result.method.queue
        self.channel.queue_bind(exchange='posts_exchange', queue=self.queue_name, routing_key='post.analyzed')
        logger.info("✓ Connected to RabbitMQ")

    def publish(self, routing_key, message):
        self.channel.basic_publish(
            exchange='posts_exchange',
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2, content_type='application/json')
        )

    def consume(self, callback):
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=callback)
        logger.info("⏳ Waiting for messages...")
        self.channel.start_consuming()

mq_client = RabbitMQClient(RABBITMQ_URL)


class CountryEmotionAggregator:
    """
    Advanced emotion aggregation using 4 algorithms with intensity weighting
    """
    
    def __init__(self):
        # Emotion intensity weights (from old aggregator)
        self.emotion_intensity = {
            'anger': 0.95,
            'fear': 0.90,
            'disgust': 0.85,
            'sadness': 0.70,
            'surprise': 0.60,
            'joy': 0.80,
            'neutral': 0.30
        }
    
    def aggregate(self, posts: List[Dict]) -> Dict:
        """
        Enhanced aggregation with all 4 algorithms from country_emotion_aggregator.py
        """
        if not posts:
            return None
        
        emotions = [p['emotion'] for p in posts]
        confidences = [p['confidence'] for p in posts]
        
        # Algorithm 1: Majority vote
        majority_result = self._majority_vote(emotions)
        
        # Algorithm 2: Weighted vote (confidence-based)
        weighted_result = self._weighted_vote(emotions, confidences)
        
        # Algorithm 3: Intensity-weighted vote
        intensity_result = self._intensity_weighted_vote(emotions, confidences)
        
        # Algorithm 4: Median intensity vote (robust to outliers)
        median_result = self._intensity_median_vote(emotions, confidences)
        
        # Consensus from all algorithms
        algorithm_votes = {
            'majority': majority_result[0],
            'weighted': weighted_result[0],
            'intensity': intensity_result[0],
            'median': median_result[0]
        }
        
        final_emotion = self._consensus_emotion(algorithm_votes)
        
        # Calculate confidence
        emotion_counts = Counter(emotions)
        confidence = self._calculate_confidence(final_emotion, emotion_counts, confidences)
        
        # Weighted scores
        weighted_scores = self._calculate_weighted_scores(emotions, confidences)
        
        return {
            'dominant_emotion': final_emotion,
            'confidence': round(confidence, 3),
            'algorithm_votes': algorithm_votes,
            'post_count': len(posts),
            'emotion_distribution': dict(emotion_counts),
            'weighted_scores': {k: round(v, 3) for k, v in weighted_scores.items()},
            'average_confidence': round(np.mean(confidences), 2)
        }
    
    def _majority_vote(self, emotions: List[str]) -> tuple:
        """Simple majority - most common emotion wins"""
        counter = Counter(emotions)
        most_common, count = counter.most_common(1)[0]
        return (most_common, count / len(emotions))
    
    def _weighted_vote(self, emotions: List[str], confidences: List[float]) -> tuple:
        """Weighted by confidence scores"""
        emotion_scores = {}
        for emotion, confidence in zip(emotions, confidences):
            if emotion not in emotion_scores:
                emotion_scores[emotion] = []
            emotion_scores[emotion].append(confidence)
        
        weighted_emotions = {}
        for emotion, conf_list in emotion_scores.items():
            avg_confidence = np.mean(conf_list)
            weight = len(conf_list) / len(emotions)
            weighted_emotions[emotion] = avg_confidence * weight
        
        best = max(weighted_emotions.items(), key=lambda x: x[1])
        return (best[0], best[1])
    
    def _intensity_weighted_vote(self, emotions: List[str], confidences: List[float]) -> tuple:
        """Weighted by emotion intensity + confidence"""
        emotion_scores = {}
        for emotion, confidence in zip(emotions, confidences):
            intensity = self.emotion_intensity.get(emotion, 0.5)
            score = intensity * confidence
            if emotion not in emotion_scores:
                emotion_scores[emotion] = []
            emotion_scores[emotion].append(score)
        
        total_scores = {e: sum(scores) for e, scores in emotion_scores.items()}
        best = max(total_scores.items(), key=lambda x: x[1])
        total = sum(total_scores.values())
        return (best[0], best[1] / total if total > 0 else 0)
    
    def _intensity_median_vote(self, emotions: List[str], confidences: List[float]) -> tuple:
        """Median-based with intensity (robust to outliers)"""
        emotion_scores = {}
        for emotion, confidence in zip(emotions, confidences):
            intensity = self.emotion_intensity.get(emotion, 0.5)
            score = intensity * confidence
            if emotion not in emotion_scores:
                emotion_scores[emotion] = []
            emotion_scores[emotion].append(score)
        
        median_scores = {e: np.median(scores) for e, scores in emotion_scores.items()}
        best = max(median_scores.items(), key=lambda x: x[1])
        total = sum(median_scores.values())
        return (best[0], best[1] / total if total > 0 else 0)
    
    def _consensus_emotion(self, algorithm_votes: Dict) -> str:
        """Determine final emotion from algorithm consensus"""
        emotions = list(algorithm_votes.values())
        counter = Counter(emotions)
        return counter.most_common(1)[0][0]
    
    def _calculate_confidence(self, emotion: str, distribution: Dict, confidences: List[float]) -> float:
        """Calculate overall confidence in prediction"""
        emotion_count = distribution.get(emotion, 0)
        total = sum(distribution.values())
        agreement = emotion_count / total if total > 0 else 0
        avg_confidence = np.mean(confidences)
        return min((agreement * 0.6) + (avg_confidence * 0.4), 1.0)
    
    def _calculate_weighted_scores(self, emotions: List[str], confidences: List[float]) -> Dict:
        """Calculate weighted score for each emotion"""
        emotion_scores = {}
        for emotion, confidence in zip(emotions, confidences):
            intensity = self.emotion_intensity.get(emotion, 0.5)
            if emotion not in emotion_scores:
                emotion_scores[emotion] = []
            emotion_scores[emotion].append(confidence * intensity)
        
        return {e: np.mean(scores) for e, scores in emotion_scores.items()}


aggregator = CountryEmotionAggregator()


def aggregate_country_emotion(country: str) -> Dict:
    """Enhanced country-level emotion aggregation"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ap.emotion, ap.confidence
        FROM analyzed_posts ap
        JOIN raw_posts rp ON ap.post_id = rp.id
        WHERE LOWER(rp.country) = LOWER(%s) AND ap.is_collective = TRUE
        ORDER BY ap.analysis_timestamp DESC
        LIMIT 1000
    """, (country,))

    posts = cursor.fetchall()
    cursor.close()
    conn.close()

    if not posts:
        return None

    # Use enhanced aggregator
    result = aggregator.aggregate(posts)
    
    if result:
        result['country'] = country
    
    return result

def store_country_emotion(aggregation: Dict):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO country_emotions (
                country, dominant_emotion, confidence, algorithm_votes, post_count, 
                emotion_distribution, weighted_scores, average_confidence
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (country) DO UPDATE SET
                dominant_emotion = EXCLUDED.dominant_emotion,
                confidence = EXCLUDED.confidence,
                algorithm_votes = EXCLUDED.algorithm_votes,
                post_count = EXCLUDED.post_count,
                emotion_distribution = EXCLUDED.emotion_distribution,
                weighted_scores = EXCLUDED.weighted_scores,
                average_confidence = EXCLUDED.average_confidence,
                last_updated = NOW()
        """, (
            aggregation['country'],
            aggregation['dominant_emotion'],
            aggregation['confidence'],
            json.dumps(aggregation['algorithm_votes']),
            aggregation['post_count'],
            json.dumps(aggregation['emotion_distribution']),
            json.dumps(aggregation.get('weighted_scores', {})),
            aggregation.get('average_confidence', 0.5)
        ))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error storing country emotion: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def handle_post_analyzed(ch, method, properties, body):
    try:
        event = json.loads(body)
        post_id = event.get('post_id')

        # Get country from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT country FROM raw_posts WHERE id = %s", (post_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        country = result['country']

        logger.info(f"📊 Aggregating emotions for {country}")

        # Aggregate
        aggregation = aggregate_country_emotion(country)

        if aggregation:
            store_country_emotion(aggregation)
            logger.info(f"✓ {country}: {aggregation['dominant_emotion']} (conf: {aggregation['confidence']})")

            # Publish event
            mq_client.publish('country.updated', {
                'country': country,
                'dominant_emotion': aggregation['dominant_emotion'],
                'confidence': aggregation['confidence']
            })

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"Error handling post.analyzed: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def consumer_thread():
    logger.info("🚀 Starting country aggregation consumer...")
    try:
        mq_client.consume(handle_post_analyzed)
    except Exception as e:
        logger.error(f"Consumer error: {e}")
        time.sleep(5)
        consumer_thread()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'country_aggregation', 'timestamp': datetime.now().isoformat()})

@app.route('/api/country/<country>', methods=['GET'])
def get_country_emotion(country):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM country_emotions WHERE LOWER(country) = LOWER(%s)", (country,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        data = dict(result)
        # ✓ Fixed: Transform to frontend-expected structure
        return jsonify({
            'country_emotion': {
                'dominant_emotion': data['dominant_emotion'],
                'confidence': data['confidence'],
                'method': '4-algorithm consensus',
                'details': {
                    'algorithm_consensus': data.get('algorithm_votes', {})
                }
            },
            'emotion_distribution': json.loads(data['emotion_distribution']) if isinstance(data['emotion_distribution'], str) else data['emotion_distribution'],
            'total_posts': data['post_count'],
            'top_events': []  # TODO: Implement event extraction from posts
        })
    else:
        return jsonify({'error': 'Country not found'}), 404

@app.route('/api/countries', methods=['GET'])
def get_all_countries():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM country_emotions ORDER BY post_count DESC")
    results = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    
    # Transform for frontend compatibility (map markers need coords)
    # Note: Frontend expects 'emotions' array with coords field
    emotions = []
    for country_data in results:
        country_name = country_data['country']
        # ✓ Fixed: Use actual coordinates from country_coordinates
        coords = COUNTRY_COORDS.get(country_name, [0, 0])  # Default to [0,0] if not found
        
        emotions.append({
            'id': country_data['id'],
            'country': country_name,
            'emotion': country_data['dominant_emotion'],
            'confidence': country_data['confidence'],
            'coords': coords,  # ✓ Now has real coordinates
            'post_count': country_data['post_count']
        })
    
    return jsonify({
        'emotions': emotions,  # ✓ Fixed: frontend expects 'emotions' not 'countries'
        'demo_mode': False,
        'count': len(results)
    })

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("📊 Country Aggregation Service")
    logger.info("=" * 60)

    consumer = threading.Thread(target=consumer_thread, daemon=True)
    consumer.start()
    logger.info("✓ Consumer started")

    logger.info(f"🚀 Starting Flask server on port {SERVICE_PORT}")
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False, threaded=True)
