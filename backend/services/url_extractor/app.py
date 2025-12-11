"""
URL Content Extractor Service
Microservice #2: Extracts content from URLs in posts

Features:
- Listens to 'post.fetched' events from RabbitMQ
- Ignores social media URLs (Twitter, Facebook, Instagram, etc.)
- Extracts content from blogs and news sites
- Uses newspaper3k and BeautifulSoup for extraction
- Publishes 'url.extracted' events
"""

import os
import logging
import json
import time
import threading
from datetime import datetime
from typing import Optional, Dict
from urllib.parse import urlparse
from flask import Flask, jsonify, request
from flask_cors import CORS
import pika
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from bs4 import BeautifulSoup
import newspaper
from newspaper import Article

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - [URL_EXTRACTOR] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 5002))
DATABASE_URL = os.getenv('DATABASE_URL')
RABBITMQ_URL = os.getenv('RABBITMQ_URL')
EXTRACTION_TIMEOUT = int(os.getenv('EXTRACTION_TIMEOUT_SECONDS', 30))
MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 50000))

# Social media domains to ignore (no authentication possible)
SOCIAL_MEDIA_DOMAINS = [
    'twitter.com', 'x.com', 'facebook.com', 'fb.com',
    'instagram.com', 'linkedin.com', 'reddit.com',
    'tiktok.com', 'snapchat.com', 'pinterest.com',
    'youtube.com', 'youtu.be', 'vimeo.com',
    'tumblr.com', 'whatsapp.com', 'telegram.org',
    't.me', 'discord.com', 'discord.gg'
]

# Known blog platforms
BLOG_PLATFORMS = [
    'medium.com', 'wordpress.com', 'blogspot.com',
    'blogger.com', 'substack.com', 'ghost.io',
    'wix.com', 'squarespace.com'
]

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database connection
def get_db_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# ============================================================================
# RABBITMQ SETUP
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

            # Declare queue for incoming messages
            result = self.channel.queue_declare(queue='url_extractor_queue', durable=True)
            self.queue_name = result.method.queue

            # Bind to 'post.fetched' routing key
            self.channel.queue_bind(
                exchange='posts_exchange',
                queue=self.queue_name,
                routing_key='post.fetched'
            )

            logger.info("✓ Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def publish(self, routing_key: str, message: dict):
        """Publish message to RabbitMQ"""
        try:
            self.channel.basic_publish(
                exchange='posts_exchange',
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent
                    content_type='application/json'
                )
            )
            logger.debug(f"Published event: {routing_key}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            self.connect()
            self.publish(routing_key, message)

    def consume(self, callback):
        """Start consuming messages"""
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=callback
        )
        logger.info("⏳ Waiting for messages...")
        self.channel.start_consuming()

    def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()

mq_client = RabbitMQClient(RABBITMQ_URL)

# ============================================================================
# URL EXTRACTION LOGIC
# ============================================================================

def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www.
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception as e:
        logger.error(f"Error extracting domain from {url}: {e}")
        return ''

def is_social_media(domain: str) -> bool:
    """Check if domain is social media"""
    return any(sm in domain for sm in SOCIAL_MEDIA_DOMAINS)

def is_blog_platform(domain: str) -> bool:
    """Check if domain is a blog platform"""
    return any(blog in domain for blog in BLOG_PLATFORMS)

def extract_content_newspaper(url: str) -> Optional[Dict]:
    """
    Extract content using newspaper3k library
    Works well for news articles and blogs
    """
    try:
        article = Article(url, timeout=EXTRACTION_TIMEOUT)
        article.download()
        article.parse()

        # Limit content length
        text = article.text[:MAX_CONTENT_LENGTH] if article.text else None

        if not text or len(text) < 100:
            return None

        return {
            'extracted_text': text,
            'title': article.title or None,
            'author': ', '.join(article.authors) if article.authors else None,
            'published_date': article.publish_date,
            'extraction_method': 'newspaper3k'
        }
    except Exception as e:
        logger.debug(f"newspaper3k extraction failed for {url}: {e}")
        return None

def extract_content_beautifulsoup(url: str) -> Optional[Dict]:
    """
    Fallback extraction using BeautifulSoup
    More generic, works when newspaper3k fails
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=EXTRACTION_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()

        # Try to find article content
        article_tags = soup.find_all(['article', 'main', 'div'], class_=['content', 'article', 'post', 'entry'])

        if article_tags:
            text = ' '.join([tag.get_text(strip=True) for tag in article_tags])
        else:
            # Fallback to all paragraphs
            paragraphs = soup.find_all('p')
            text = ' '.join([p.get_text(strip=True) for p in paragraphs])

        # Clean up text
        text = ' '.join(text.split())[:MAX_CONTENT_LENGTH]

        if not text or len(text) < 100:
            return None

        # Try to extract title
        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else None

        return {
            'extracted_text': text,
            'title': title,
            'author': None,
            'published_date': None,
            'extraction_method': 'beautifulsoup'
        }
    except Exception as e:
        logger.debug(f"BeautifulSoup extraction failed for {url}: {e}")
        return None

def extract_url_content(url: str) -> Dict:
    """
    Main extraction function
    Returns extraction result with status
    """
    domain = extract_domain(url)

    # Check if social media (ignore)
    if is_social_media(domain):
        return {
            'status': 'ignored',
            'content_type': 'social_media',
            'domain': domain,
            'extracted_text': None,
            'error_message': 'Social media URL - authentication required'
        }

    # Determine content type
    content_type = 'blog' if is_blog_platform(domain) else 'news'

    # Try newspaper3k first (best for articles)
    result = extract_content_newspaper(url)

    # Fallback to BeautifulSoup if newspaper fails
    if not result:
        result = extract_content_beautifulsoup(url)

    if result:
        return {
            'status': 'success',
            'content_type': content_type,
            'domain': domain,
            **result
        }
    else:
        return {
            'status': 'failed',
            'content_type': content_type,
            'domain': domain,
            'extracted_text': None,
            'error_message': 'Could not extract content from URL'
        }

def store_url_content(post_id: int, url: str, extraction_result: Dict) -> bool:
    """Store URL content in database"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO url_content (
                post_id, url, domain, content_type, extracted_text,
                title, author, published_date, extraction_status, error_message
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (post_id) DO UPDATE SET
                domain = EXCLUDED.domain,
                content_type = EXCLUDED.content_type,
                extracted_text = EXCLUDED.extracted_text,
                title = EXCLUDED.title,
                author = EXCLUDED.author,
                published_date = EXCLUDED.published_date,
                extraction_status = EXCLUDED.extraction_status,
                error_message = EXCLUDED.error_message,
                extracted_at = NOW()
        """, (
            post_id,
            url,
            extraction_result.get('domain'),
            extraction_result.get('content_type'),
            extraction_result.get('extracted_text'),
            extraction_result.get('title'),
            extraction_result.get('author'),
            extraction_result.get('published_date'),
            extraction_result.get('status'),
            extraction_result.get('error_message')
        ))

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        logger.error(f"Error storing URL content for post {post_id}: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# MESSAGE CONSUMER
# ============================================================================

def handle_post_fetched(ch, method, properties, body):
    """Handle 'post.fetched' event"""
    try:
        event = json.loads(body)
        post_id = event.get('post_id')
        url = event.get('url')
        has_url = event.get('has_url', False)

        logger.info(f"📨 Received post.fetched event for post {post_id}")

        # Skip if no URL
        if not has_url or not url:
            logger.debug(f"Post {post_id} has no URL, skipping")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Check if already extracted (avoid duplicate work)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM url_content WHERE post_id = %s", (post_id,))
        already_extracted = cursor.fetchone()
        cursor.close()
        conn.close()

        if already_extracted:
            logger.debug(f"Post {post_id} URL already extracted, skipping")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Extract content
        logger.info(f"🔍 Extracting content from: {url}")
        extraction_result = extract_url_content(url)

        # Store result
        store_url_content(post_id, url, extraction_result)

        status = extraction_result.get('status')
        logger.info(f"✓ Extraction {status} for post {post_id}: {extraction_result.get('domain')}")

        # Publish 'url.extracted' event if successful
        if status == 'success':
            mq_client.publish('url.extracted', {
                'post_id': post_id,
                'url': url,
                'extracted_content': extraction_result.get('extracted_text'),
                'title': extraction_result.get('title'),
                'content_type': extraction_result.get('content_type')
            })

        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"Error handling post.fetched event: {e}")
        # Reject and requeue (will retry)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def consumer_thread():
    """Background thread for consuming RabbitMQ messages"""
    logger.info("🚀 Starting URL extraction consumer...")
    try:
        mq_client.consume(handle_post_fetched)
    except Exception as e:
        logger.error(f"Consumer thread error: {e}")
        time.sleep(5)
        consumer_thread()  # Retry

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'url_extractor',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/status', methods=['GET'])
def status():
    """Get extractor status and statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get extraction statistics
    cursor.execute("""
        SELECT
            extraction_status,
            COUNT(*) as count
        FROM url_content
        GROUP BY extraction_status
    """)
    stats = {row['extraction_status']: row['count'] for row in cursor.fetchall()}

    # Get content type distribution
    cursor.execute("""
        SELECT
            content_type,
            COUNT(*) as count
        FROM url_content
        WHERE extraction_status = 'success'
        GROUP BY content_type
    """)
    content_types = {row['content_type']: row['count'] for row in cursor.fetchall()}

    cursor.close()
    conn.close()

    return jsonify({
        'extraction_stats': stats,
        'content_types': content_types,
        'social_media_domains': len(SOCIAL_MEDIA_DOMAINS),
        'blog_platforms': len(BLOG_PLATFORMS)
    })

@app.route('/api/extract', methods=['POST'])
def extract_manual():
    """Manually trigger URL extraction"""
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'error': 'url parameter required'}), 400

    # Extract content
    result = extract_url_content(url)

    return jsonify(result)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🔗 URL Content Extractor Service")
    logger.info("=" * 60)
    logger.info(f"📍 Extraction timeout: {EXTRACTION_TIMEOUT}s")
    logger.info(f"📏 Max content length: {MAX_CONTENT_LENGTH} chars")
    logger.info(f"🚫 Social media domains blocked: {len(SOCIAL_MEDIA_DOMAINS)}")
    logger.info(f"📝 Blog platforms recognized: {len(BLOG_PLATFORMS)}")
    logger.info("=" * 60)

    # Start consumer thread
    consumer = threading.Thread(target=consumer_thread, daemon=True)
    consumer.start()
    logger.info("✓ Consumer thread started")

    # Start Flask app
    logger.info(f"🚀 Starting Flask server on port {SERVICE_PORT}")
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False, threaded=True)
