"""
ML Analysis Service
Microservice #3: Multi-model emotion detection and classification

Features:
- Listens to 'post.fetched' and 'url.extracted' events
- 4-model emotion ensemble (RoBERTa, VADER, TextBlob, Keywords)
- Collective vs personal classification (BART)
- Cross-country detection (NER + keywords)
- Lazy loading of ML models (memory optimization)
- Batch processing
"""

import os
import logging
import json
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, jsonify, request
from flask_cors import CORS
import pika
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np

# ML imports (lazy loaded)
transformers_imported = False
def import_transformers():
    global transformers, pipeline, transformers_imported
    if not transformers_imported:
        import transformers as tf
        from transformers import pipeline as pl
        transformers = tf
        pipeline = pl
        transformers_imported = True

vader_imported = False
def import_vader():
    global SentimentIntensityAnalyzer, vader_imported
    if not vader_imported:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        vader_imported = True

textblob_imported = False
def import_textblob():
    global TextBlob, textblob_imported
    if not textblob_imported:
        from textblob import TextBlob
        textblob_imported = True

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - [ML_ANALYZER] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 5003))
DATABASE_URL = os.getenv('DATABASE_URL')
RABBITMQ_URL = os.getenv('RABBITMQ_URL')
BATCH_SIZE = int(os.getenv('BATCH_SIZE', 50))
MODEL_IDLE_TIMEOUT = int(os.getenv('MODEL_IDLE_TIMEOUT', 600))  # 10 minutes

# Model weights for ensemble
EMOTION_WEIGHTS = {
    'roberta': 3.0,
    'keywords': 2.0,
    'vader': 1.0,
    'textblob': 0.8
}

# Emotion keywords
EMOTION_KEYWORDS = {
    'joy': ['happy', 'celebration', 'victory', 'success', 'win', 'amazing', 'wonderful', 'great'],
    'sadness': ['sad', 'tragedy', 'death', 'loss', 'mourning', 'grief', 'terrible', 'devastating'],
    'anger': ['angry', 'outrage', 'protest', 'violence', 'riot', 'furious', 'conflict'],
    'fear': ['fear', 'terror', 'threat', 'danger', 'crisis', 'warning', 'concern', 'worried'],
    'surprise': ['shock', 'unexpected', 'surprise', 'breaking', 'sudden', 'unbelievable'],
    'disgust': ['corruption', 'scandal', 'abuse', 'disgusting', 'appalling']
}

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# ML Models (lazy loaded)
models = {
    'roberta': None,
    'bart': None,
    'ner': None,
    'vader': None
}
models_loaded = False
last_model_use_time = time.time()

# ============================================================================
# DATABASE
# ============================================================================

def get_db_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# ============================================================================
# RABBITMQ
# ============================================================================

class RabbitMQClient:
    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        """Connect to RabbitMQ"""
        try:
            self.connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            self.channel = self.connection.channel()

            # Declare exchange
            self.channel.exchange_declare(
                exchange='posts_exchange',
                exchange_type='topic',
                durable=True
            )

            # Declare queue
            result = self.channel.queue_declare(queue='ml_analyzer_queue', durable=True)
            self.queue_name = result.method.queue

            # Bind to multiple routing keys
            self.channel.queue_bind(exchange='posts_exchange', queue=self.queue_name, routing_key='post.fetched')
            self.channel.queue_bind(exchange='posts_exchange', queue=self.queue_name, routing_key='url.extracted')

            logger.info("✓ Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def publish(self, routing_key: str, message: dict):
        """Publish message"""
        try:
            self.channel.basic_publish(
                exchange='posts_exchange',
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2, content_type='application/json')
            )
        except Exception as e:
            logger.error(f"Failed to publish: {e}")
            self.connect()
            self.publish(routing_key, message)

    def consume(self, callback):
        """Start consuming"""
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=callback)
        logger.info("⏳ Waiting for messages...")
        self.channel.start_consuming()

mq_client = RabbitMQClient(RABBITMQ_URL)

# ============================================================================
# ML MODEL MANAGEMENT
# ============================================================================

def load_models():
    """Lazy load ML models"""
    global models, models_loaded, last_model_use_time

    if models_loaded:
        last_model_use_time = time.time()
        return

    logger.info("⏳ Loading ML models... (this may take 15-20 seconds)")
    start_time = time.time()

    try:
        # Import libraries
        import_transformers()
        import_vader()
        import_textblob()

        # Load RoBERTa emotion model
        logger.info("Loading RoBERTa emotion model...")
        models['roberta'] = pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base', top_k=None)

        # Load BART for collective classification
        logger.info("Loading BART collective classifier...")
        models['bart'] = pipeline('zero-shot-classification', model='facebook/bart-large-mnli')

        # Load BERT NER for country detection
        logger.info("Loading BERT NER model...")
        models['ner'] = pipeline('ner', model='dslim/bert-base-NER', aggregation_strategy='simple')

        # Initialize VADER
        logger.info("Loading VADER sentiment analyzer...")
        models['vader'] = SentimentIntensityAnalyzer()

        models_loaded = True
        last_model_use_time = time.time()

        elapsed = time.time() - start_time
        logger.info(f"✓ All models loaded in {elapsed:.1f}s")

    except Exception as e:
        logger.error(f"❌ Failed to load models: {e}")
        raise

def unload_models_if_idle():
    """Unload models if idle for too long"""
    global models, models_loaded, last_model_use_time

    if not models_loaded:
        return

    idle_time = time.time() - last_model_use_time

    if idle_time > MODEL_IDLE_TIMEOUT:
        logger.info(f"⏱️  Models idle for {idle_time:.0f}s, unloading...")
        models = {key: None for key in models}
        models_loaded = False
        logger.info("✓ Models unloaded (memory freed)")

# ============================================================================
# EMOTION ANALYSIS
# ============================================================================

def analyze_emotion_roberta(text: str) -> Dict:
    """RoBERTa emotion detection"""
    try:
        if not models['roberta']:
            load_models()

        results = models['roberta'](text[:512])[0]  # Limit to 512 tokens
        top_result = max(results, key=lambda x: x['score'])

        return {
            'emotion': top_result['label'],
            'confidence': top_result['score']
        }
    except Exception as e:
        logger.error(f"RoBERTa analysis failed: {e}")
        return {'emotion': 'neutral', 'confidence': 0.5}

def analyze_sentiment_vader(text: str) -> Dict:
    """VADER sentiment analysis"""
    try:
        if not models['vader']:
            load_models()

        scores = models['vader'].polarity_scores(text)
        compound = scores['compound']

        # Map sentiment to emotion
        if compound >= 0.5:
            emotion = 'joy'
        elif compound <= -0.5:
            emotion = 'sadness'
        elif compound <= -0.2:
            emotion = 'anger'
        else:
            emotion = 'neutral'

        return {
            'emotion': emotion,
            'confidence': abs(compound)
        }
    except Exception as e:
        logger.error(f"VADER analysis failed: {e}")
        return {'emotion': 'neutral', 'confidence': 0.5}

def analyze_sentiment_textblob(text: str) -> Dict:
    """TextBlob sentiment analysis"""
    try:
        import_textblob()
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity

        if polarity > 0.3:
            emotion = 'joy'
        elif polarity < -0.3:
            emotion = 'sadness'
        elif polarity < -0.1:
            emotion = 'anger'
        else:
            emotion = 'neutral'

        return {
            'emotion': emotion,
            'confidence': abs(polarity)
        }
    except Exception as e:
        logger.error(f"TextBlob analysis failed: {e}")
        return {'emotion': 'neutral', 'confidence': 0.5}

def analyze_keywords(text: str) -> Dict:
    """Keyword-based emotion detection"""
    text_lower = text.lower()
    emotion_scores = {}

    for emotion, keywords in EMOTION_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        emotion_scores[emotion] = matches

    if max(emotion_scores.values()) > 0:
        top_emotion = max(emotion_scores, key=emotion_scores.get)
        confidence = min(emotion_scores[top_emotion] / 10, 1.0)
        return {'emotion': top_emotion, 'confidence': confidence}
    else:
        return {'emotion': 'neutral', 'confidence': 0.5}

def ensemble_emotion_analysis(text: str) -> Dict:
    """4-model ensemble emotion detection"""
    # Get predictions from all models
    roberta = analyze_emotion_roberta(text)
    vader = analyze_sentiment_vader(text)
    textblob = analyze_sentiment_textblob(text)
    keywords = analyze_keywords(text)

    # Weighted voting
    emotion_votes = {}
    emotion_votes[roberta['emotion']] = emotion_votes.get(roberta['emotion'], 0) + EMOTION_WEIGHTS['roberta'] * roberta['confidence']
    emotion_votes[vader['emotion']] = emotion_votes.get(vader['emotion'], 0) + EMOTION_WEIGHTS['vader'] * vader['confidence']
    emotion_votes[textblob['emotion']] = emotion_votes.get(textblob['emotion'], 0) + EMOTION_WEIGHTS['textblob'] * textblob['confidence']
    emotion_votes[keywords['emotion']] = emotion_votes.get(keywords['emotion'], 0) + EMOTION_WEIGHTS['keywords'] * keywords['confidence']

    # Get top emotion
    final_emotion = max(emotion_votes, key=emotion_votes.get)
    total_weight = sum(EMOTION_WEIGHTS.values())
    final_confidence = emotion_votes[final_emotion] / total_weight

    return {
        'emotion': final_emotion,
        'confidence': round(final_confidence, 3),
        'roberta_emotion': roberta['emotion'],
        'roberta_confidence': round(roberta['confidence'], 3),
        'vader_sentiment': vader['emotion'],
        'vader_confidence': round(vader['confidence'], 3),  # ✓ Added
        'textblob_sentiment': textblob['emotion'],
        'textblob_confidence': round(textblob['confidence'], 3),  # ✓ Added
        'keyword_match': keywords['emotion']
    }

def classify_collective(text: str) -> bool:
    """Classify if post is about collective/country issue"""
    try:
        if not models['bart']:
            load_models()

        result = models['bart'](
            text[:512],
            candidate_labels=['collective issue', 'personal issue'],
            hypothesis_template='This text is about a {}.'
        )

        is_collective = result['labels'][0] == 'collective issue'
        return is_collective

    except Exception as e:
        logger.error(f"Collective classification failed: {e}")
        return True  # Default to collective

def detect_countries(text: str) -> List[str]:
    """Detect country mentions using NER"""
    try:
        if not models['ner']:
            load_models()

        entities = models['ner'](text[:512])
        countries = [ent['word'] for ent in entities if ent['entity_group'] == 'LOC']

        return list(set(countries))  # Unique countries

    except Exception as e:
        logger.error(f"Country detection failed: {e}")
        return []

def analyze_post(post_id: int, text: str) -> Dict:
    """Complete post analysis"""
    # Emotion analysis
    emotion_result = ensemble_emotion_analysis(text)

    # Collective classification
    is_collective = classify_collective(text)

    # Country detection
    detected_countries = detect_countries(text)

    return {
        'post_id': post_id,
        'emotion': emotion_result['emotion'],
        'confidence': emotion_result['confidence'],
        'is_collective': is_collective,
        'detected_countries': detected_countries,
        'roberta_emotion': emotion_result.get('roberta_emotion'),
        'roberta_confidence': emotion_result.get('roberta_confidence'),
        'vader_sentiment': emotion_result.get('vader_sentiment'),
        'vader_confidence': emotion_result.get('vader_confidence'),  # ✓ Fixed
        'textblob_sentiment': emotion_result.get('textblob_sentiment'),
        'textblob_confidence': emotion_result.get('textblob_confidence'),  # ✓ Fixed
        'keyword_match': emotion_result.get('keyword_match')
    }

def store_analysis(analysis: Dict):
    """Store analysis results in database"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO analyzed_posts (
                post_id, emotion, confidence, is_collective, detected_countries,
                roberta_emotion, roberta_confidence, vader_sentiment, textblob_sentiment, keyword_match
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (post_id) DO UPDATE SET
                emotion = EXCLUDED.emotion,
                confidence = EXCLUDED.confidence,
                is_collective = EXCLUDED.is_collective,
                detected_countries = EXCLUDED.detected_countries,
                analysis_timestamp = NOW()
        """, (
            analysis['post_id'],
            analysis['emotion'],
            analysis['confidence'],
            analysis['is_collective'],
            analysis['detected_countries'],
            analysis.get('roberta_emotion'),
            analysis.get('roberta_confidence'),
            analysis.get('vader_confidence'),  # ✓ Fixed: store confidence not emotion
            analysis.get('textblob_confidence'),  # ✓ Fixed: store confidence not emotion
            analysis.get('keyword_match')
        ))

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        logger.error(f"Error storing analysis: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# MESSAGE CONSUMER
# ============================================================================

def handle_message(ch, method, properties, body):
    """Handle post.fetched or url.extracted events"""
    try:
        event = json.loads(body)
        post_id = event.get('post_id')

        logger.info(f"📨 Received event for post {post_id}")

        # Get post content from database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT rp.id, rp.title, rp.text, uc.extracted_text
            FROM raw_posts rp
            LEFT JOIN url_content uc ON rp.id = uc.post_id
            WHERE rp.id = %s
        """, (post_id,))

        post = cursor.fetchone()
        cursor.close()
        conn.close()

        if not post:
            logger.warning(f"Post {post_id} not found in database")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Combine text sources
        text_parts = [post['title']]
        if post['text']:
            text_parts.append(post['text'])
        if post['extracted_text']:
            text_parts.append(post['extracted_text'])

        combined_text = ' '.join(text_parts)

        # Analyze
        logger.info(f"🧠 Analyzing post {post_id}...")
        analysis = analyze_post(post_id, combined_text)

        # Store
        store_analysis(analysis)

        logger.info(f"✓ Post {post_id} analyzed: {analysis['emotion']} (conf: {analysis['confidence']})")

        # Publish event
        mq_client.publish('post.analyzed', {
            'post_id': post_id,
            'emotion': analysis['emotion'],
            'confidence': analysis['confidence'],
            'is_collective': analysis['is_collective'],
            'detected_countries': analysis['detected_countries']
        })

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def consumer_thread():
    """Background consumer thread"""
    logger.info("🚀 Starting ML analysis consumer...")
    try:
        mq_client.consume(handle_message)
    except Exception as e:
        logger.error(f"Consumer error: {e}")
        time.sleep(5)
        consumer_thread()

def idle_checker_thread():
    """Check for idle models and unload"""
    while True:
        time.sleep(60)  # Check every minute
        unload_models_if_idle()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'ml_analyzer',
        'models_loaded': models_loaded,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/models/status', methods=['GET'])
def models_status():
    """Get model loading status"""
    return jsonify({
        'models_loaded': models_loaded,
        'last_use': datetime.fromtimestamp(last_model_use_time).isoformat() if models_loaded else None,
        'idle_timeout': MODEL_IDLE_TIMEOUT
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_manual():
    """Manually analyze text"""
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({'error': 'text required'}), 400

    # Load models if needed
    if not models_loaded:
        load_models()

    result = ensemble_emotion_analysis(text)
    is_collective = classify_collective(text)
    countries = detect_countries(text)

    return jsonify({
        'emotion': result['emotion'],
        'confidence': result['confidence'],
        'is_collective': is_collective,
        'detected_countries': countries,
        'details': result
    })

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🧠 ML Analysis Service")
    logger.info("=" * 60)
    logger.info(f"📊 Batch size: {BATCH_SIZE}")
    logger.info(f"⏱️  Model idle timeout: {MODEL_IDLE_TIMEOUT}s")
    logger.info("=" * 60)

    # Start consumer
    consumer = threading.Thread(target=consumer_thread, daemon=True)
    consumer.start()

    # Start idle checker
    idle_checker = threading.Thread(target=idle_checker_thread, daemon=True)
    idle_checker.start()

    logger.info("✓ Threads started")
    logger.info(f"🚀 Starting Flask server on port {SERVICE_PORT}")
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False, threaded=True)
