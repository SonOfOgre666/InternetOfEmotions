"""
Collective Analyzer Service
Microservice for filtering personal vs collective issues using ML/NLP

Responsibilities:
- Classifies posts as individual or collective issues
- Uses zero-shot classification (facebook/bart-large-mnli)
- Detects patterns across multiple posts
- Publishes analysis results to RabbitMQ
"""

import os
import json
import logging
from typing import Dict, List
from collections import Counter
from flask import Flask, jsonify, request
from flask_cors import CORS
import pika
import torch
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@rabbitmq:5672/')

# Global ML model
classifier = None
ml_available = False


def load_ml_model():
    """Load zero-shot classification model"""
    global classifier, ml_available
    
    logger.info("🤖 Loading collective intelligence classifier...")
    try:
        classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=0 if torch.cuda.is_available() else -1
        )
        ml_available = True
        logger.info("✓ Collective intelligence classifier loaded successfully")
    except Exception as e:
        logger.error(f"⚠ ML classifier failed to load: {e}")
        logger.info("  Falling back to keyword-based detection")
        classifier = None
        ml_available = False


# Keyword-based fallback
PERSONAL_INDICATORS = [
    'my', 'i am', "i'm", 'my life', 'my problem', 'i feel', 'i think',
    'personally', 'my family', 'my friend', 'my job', 'my boss'
]

COLLECTIVE_INDICATORS = [
    'we', 'us', 'our', 'people', 'everyone', 'many', 'most',
    'citizens', 'population', 'community', 'society', 'country',
    'nation', 'government', 'crisis', 'widespread'
]

COLLECTIVE_TOPICS = [
    'war', 'conflict', 'crisis', 'disaster', 'emergency', 'shortage',
    'inflation', 'unemployment', 'protest', 'election', 'policy',
    'epidemic', 'pandemic', 'violence', 'terrorism', 'corruption'
]


def analyze_with_ml(text: str) -> Dict:
    """Use zero-shot classification for analysis"""
    try:
        candidate_labels = [
            "collective social issue affecting many people",
            "personal individual problem or feeling",
            "country-level crisis or emergency",
            "private family or relationship matter"
        ]
        
        text_truncated = text[:512]
        result = classifier(text_truncated, candidate_labels, multi_label=False)
        
        labels = result['labels']
        scores = result['scores']
        
        collective_score = 0.0
        for label, score in zip(labels, scores):
            if 'collective' in label.lower() or 'country-level' in label.lower():
                collective_score += score
            elif 'personal' in label.lower() or 'private' in label.lower():
                collective_score -= score * 0.5
        
        collective_score = max(0, min(1, (collective_score + 0.5)))
        is_collective = collective_score >= 0.5
        
        return {
            'is_collective': is_collective,
            'collective_score': round(collective_score, 2),
            'reason': f"ML classified as: {labels[0]}",
            'method': 'zero-shot-classification',
            'top_label': labels[0],
            'confidence': round(scores[0], 2)
        }
        
    except Exception as e:
        logger.error(f"ML classification error: {e}")
        return analyze_with_keywords(text)


def analyze_with_keywords(text: str) -> Dict:
    """Fallback keyword-based analysis"""
    text_lower = text.lower()

    personal_score = sum(1 for indicator in PERSONAL_INDICATORS if indicator in text_lower)
    collective_score = sum(1 for indicator in COLLECTIVE_INDICATORS if indicator in text_lower)
    topic_score = sum(1 for topic in COLLECTIVE_TOPICS if topic in text_lower)

    total_score = (collective_score + topic_score * 2) - personal_score
    normalized_score = max(0, min(1, total_score / 10))
    is_collective = normalized_score >= 0.3

    return {
        'is_collective': is_collective,
        'collective_score': normalized_score,
        'reason': 'Keyword-based classification',
        'method': 'keyword-based',
        'personal_indicators': personal_score,
        'collective_indicators': collective_score,
        'topic_indicators': topic_score
    }


def publish_event(routing_key: str, data: dict):
    """Publish event to RabbitMQ"""
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        channel.exchange_declare(exchange='posts_exchange', exchange_type='topic', durable=True)

        message = json.dumps(data)
        channel.basic_publish(
            exchange='posts_exchange',
            routing_key=routing_key,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )

        connection.close()
        logger.info(f"Published event: {routing_key}")
    except Exception as e:
        logger.error(f"Error publishing event: {e}")


# API Endpoints

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    from datetime import datetime
    return jsonify({
        'status': 'healthy',
        'service': 'collective_analyzer',
        'ml_available': ml_available,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze if text represents collective or personal issue"""
    try:
        data = request.json
        text = data.get('text', '')

        if not text or len(text.strip()) < 10:
            return jsonify({
                'success': False,
                'error': 'Text too short'
            }), 400

        # Perform analysis
        if ml_available:
            result = analyze_with_ml(text)
        else:
            result = analyze_with_keywords(text)

        result['success'] = True

        # Publish event if collective issue detected
        if result['is_collective']:
            publish_event('collective.detected', {
                'text': text[:200],
                'score': result['collective_score'],
                'method': result['method']
            })

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error analyzing text: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/analyze/batch', methods=['POST'])
def analyze_batch():
    """Analyze multiple texts"""
    try:
        data = request.json
        texts = data.get('texts', [])

        if not texts:
            return jsonify({
                'success': False,
                'error': 'No texts provided'
            }), 400

        results = []
        collective_count = 0

        for text in texts:
            if ml_available:
                result = analyze_with_ml(text)
            else:
                result = analyze_with_keywords(text)
            
            results.append(result)
            if result['is_collective']:
                collective_count += 1

        return jsonify({
            'success': True,
            'results': results,
            'total': len(texts),
            'collective_count': collective_count,
            'collective_ratio': round(collective_count / len(texts), 2)
        })

    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/patterns', methods=['POST'])
def detect_patterns():
    """Detect collective patterns across posts"""
    try:
        data = request.json
        posts = data.get('posts', [])
        min_size = data.get('min_pattern_size', 5)

        if len(posts) < min_size:
            return jsonify({
                'success': True,
                'patterns': [],
                'message': 'Not enough posts for pattern detection'
            })

        # Extract texts
        texts = [p.get('text', '') for p in posts]

        # Simple keyword extraction (TF-IDF)
        try:
            vectorizer = TfidfVectorizer(max_features=20, stop_words='english')
            vectors = vectorizer.fit_transform(texts)
            keywords = vectorizer.get_feature_names_out()
            avg_scores = np.asarray(vectors.mean(axis=0)).flatten()
            
            keyword_scores = sorted(
                zip(keywords, avg_scores),
                key=lambda x: x[1],
                reverse=True
            )
            
            top_keywords = [kw for kw, score in keyword_scores[:10]]

            # Emotion distribution
            emotions = [p.get('emotion', 'unknown') for p in posts]
            emotion_counts = Counter(emotions)

            pattern = {
                'size': len(posts),
                'keywords': top_keywords,
                'emotion_distribution': dict(emotion_counts),
                'dominant_emotion': emotion_counts.most_common(1)[0][0] if emotion_counts else None
            }

            return jsonify({
                'success': True,
                'patterns': [pattern]
            })

        except Exception as e:
            logger.error(f"Pattern detection error: {e}")
            return jsonify({
                'success': True,
                'patterns': [],
                'error': str(e)
            })

    except Exception as e:
        logger.error(f"Error detecting patterns: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("🚀 Starting Collective Analyzer Service")
    load_ml_model()
    app.run(host='0.0.0.0', port=5000, debug=False)
