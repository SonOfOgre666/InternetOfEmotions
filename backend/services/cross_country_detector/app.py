"""
Cross-Country Detector Service
Microservice for detecting country mentions in posts using NER

Responsibilities:
- Detects country mentions using Named Entity Recognition
- Identifies cross-country discussions
- Handles multi-country detection
- Publishes detection events to RabbitMQ
"""

import os
import json
import re
import logging
from typing import Dict, List, Set
from flask import Flask, jsonify, request
from flask_cors import CORS
import pika
from transformers import pipeline

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

# Global NER model
ner_pipeline = None
ner_available = False

# All countries to detect
ALL_COUNTRIES = [
    'USA', 'UK', 'Canada', 'Australia', 'India', 'Germany', 'France', 'Japan',
    'Brazil', 'Mexico', 'Spain', 'Italy', 'Netherlands', 'Sweden', 'Norway',
    'Denmark', 'Finland', 'Poland', 'Russia', 'China', 'South Korea', 'Indonesia',
    'Philippines', 'Thailand', 'Vietnam', 'Malaysia', 'Singapore', 'Turkey',
    'Egypt', 'South Africa', 'Nigeria', 'Kenya', 'Argentina', 'Chile', 'Colombia'
]

# Country aliases for keyword matching
COUNTRY_ALIASES = {
    'usa': ['usa', 'us', 'united states', 'america', 'american'],
    'uk': ['uk', 'united kingdom', 'britain', 'british', 'england'],
    'canada': ['canada', 'canadian'],
    'australia': ['australia', 'australian', 'aussie'],
    'india': ['india', 'indian'],
    'germany': ['germany', 'german'],
    'france': ['france', 'french'],
    'japan': ['japan', 'japanese'],
    'brazil': ['brazil', 'brazilian'],
    'mexico': ['mexico', 'mexican'],
    'spain': ['spain', 'spanish'],
    'italy': ['italy', 'italian'],
    'russia': ['russia', 'russian'],
    'china': ['china', 'chinese'],
    'south korea': ['south korea', 'korea', 'korean'],
    'turkey': ['turkey', 'turkish'],
    'egypt': ['egypt', 'egyptian'],
    'south africa': ['south africa', 'south african'],
    'nigeria': ['nigeria', 'nigerian'],
}

# Build keyword to country mapping
KEYWORD_TO_COUNTRY = {}
for country, keywords in COUNTRY_ALIASES.items():
    for keyword in keywords:
        KEYWORD_TO_COUNTRY[keyword.lower()] = country


def load_ner_model():
    """Load NER model for country detection"""
    global ner_pipeline, ner_available
    
    logger.info("🤖 Loading Named Entity Recognition (NER) model...")
    try:
        ner_pipeline = pipeline(
            "ner",
            model="dslim/bert-base-NER",
            grouped_entities=True,
            device=-1  # CPU
        )
        ner_available = True
        logger.info("✓ NER model loaded successfully")
    except Exception as e:
        logger.error(f"⚠ NER model failed to load: {e}")
        logger.info("  Using keyword-based detection only")
        ner_pipeline = None
        ner_available = False


def detect_with_ner(text: str) -> Set[str]:
    """Use NER to find location entities"""
    if not ner_available:
        return set()

    try:
        text_truncated = text[:512]
        entities = ner_pipeline(text_truncated)
        
        countries = set()
        for entity in entities:
            if entity['entity_group'] == 'LOC':
                location = entity['word'].lower()
                if location in KEYWORD_TO_COUNTRY:
                    countries.add(KEYWORD_TO_COUNTRY[location])

        return countries

    except Exception as e:
        logger.error(f"NER detection error: {e}")
        return set()


def detect_with_keywords(text: str) -> Set[str]:
    """Match country keywords in text"""
    text_lower = text.lower()
    countries = set()

    for keyword, country in KEYWORD_TO_COUNTRY.items():
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text_lower):
            countries.add(country)

    return countries


def count_country_mentions(text: str, country: str) -> int:
    """Count how many times a country is mentioned"""
    text_lower = text.lower()
    count = 0

    if country in COUNTRY_ALIASES:
        for keyword in COUNTRY_ALIASES[country]:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            count += len(re.findall(pattern, text_lower))

    return count


def detect_countries(text: str) -> Dict:
    """
    Detect countries mentioned in text
    
    Returns dict with countries, primary country, confidence, etc.
    """
    if not text or len(text.strip()) < 5:
        return {
            'countries': [],
            'primary_country': None,
            'confidence': 0.0,
            'mentions': {},
            'method': 'none',
            'mention_count': 0
        }

    detected_countries = set()
    methods_used = []

    # Method 1: NER-based detection
    if ner_available:
        ner_countries = detect_with_ner(text)
        detected_countries.update(ner_countries)
        if ner_countries:
            methods_used.append('NER')

    # Method 2: Keyword matching
    keyword_countries = detect_with_keywords(text)
    detected_countries.update(keyword_countries)
    if keyword_countries:
        methods_used.append('keyword')

    # Count mentions per country
    country_mentions = {}
    for country in detected_countries:
        count = count_country_mentions(text, country)
        country_mentions[country] = {
            'count': count,
            'frequency': count / len(text.split())
        }

    # Sort by frequency
    sorted_mentions = sorted(
        country_mentions.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )

    primary_country = sorted_mentions[0][0] if sorted_mentions else None

    # Calculate confidence
    if len(detected_countries) == 0:
        confidence = 0.0
    elif len(detected_countries) == 1:
        confidence = 0.9
    else:
        confidence = 0.7

    return {
        'countries': list(detected_countries),
        'primary_country': primary_country,
        'confidence': round(confidence, 2),
        'mentions': dict(sorted_mentions),
        'method': '+'.join(methods_used) if methods_used else 'none',
        'mention_count': len(detected_countries)
    }


def analyze_cross_country(post_country: str, detected_countries: List[str]) -> Dict:
    """Analyze if a post is about another country"""
    if not detected_countries:
        return {
            'is_cross_country': False,
            'primary_subject': post_country,
            'source_country': post_country,
            'relevance': 1.0
        }

    primary = detected_countries[0]
    is_cross = primary.lower() != post_country.lower()

    return {
        'is_cross_country': is_cross,
        'primary_subject': primary,
        'source_country': post_country,
        'relevance': 1.0 if is_cross else 0.5
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
        'service': 'cross_country_detector',
        'ner_available': ner_available,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/detect', methods=['POST'])
def detect():
    """Detect countries mentioned in text"""
    try:
        data = request.json
        text = data.get('text', '')
        post_country = data.get('country')

        if not text:
            return jsonify({
                'success': False,
                'error': 'Text required'
            }), 400

        # Detect countries
        result = detect_countries(text)
        result['success'] = True

        # Cross-country analysis
        if post_country:
            cross_analysis = analyze_cross_country(post_country, result['countries'])
            result['cross_country_analysis'] = cross_analysis

            # Publish event if cross-country detected
            if cross_analysis['is_cross_country']:
                publish_event('cross_country.detected', {
                    'source_country': post_country,
                    'subject_country': cross_analysis['primary_subject'],
                    'text': text[:200]
                })

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error detecting countries: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/detect/batch', methods=['POST'])
def detect_batch():
    """Detect countries in multiple texts"""
    try:
        data = request.json
        texts = data.get('texts', [])

        if not texts:
            return jsonify({
                'success': False,
                'error': 'No texts provided'
            }), 400

        results = []
        cross_country_count = 0

        for item in texts:
            text = item.get('text', '')
            post_country = item.get('country')

            detection = detect_countries(text)
            
            if post_country:
                cross_analysis = analyze_cross_country(post_country, detection['countries'])
                detection['cross_country_analysis'] = cross_analysis
                if cross_analysis['is_cross_country']:
                    cross_country_count += 1

            results.append(detection)

        return jsonify({
            'success': True,
            'results': results,
            'total': len(texts),
            'cross_country_count': cross_country_count
        })

    except Exception as e:
        logger.error(f"Error in batch detection: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("🚀 Starting Cross-Country Detector Service")
    load_ner_model()
    app.run(host='0.0.0.0', port=5000, debug=False)
