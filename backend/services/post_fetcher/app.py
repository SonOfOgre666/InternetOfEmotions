"""
Post Fetcher Service
Microservice #1: Fetches posts from Reddit subreddits

Features:
- Fetches posts from news subreddits (≤30 days old)
- Filters out image-only posts (keeps text + image posts)
- Filters out URL-only posts (delegates to URL Extractor)
- Stores post metadata with Reddit creation date
- Publishes 'post.fetched' events to RabbitMQ
"""

import os
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from flask import Flask, jsonify, request
from flask_cors import CORS
import praw
import pika
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - [POST_FETCHER] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 5001))
DATABASE_URL = os.getenv('DATABASE_URL')
RABBITMQ_URL = os.getenv('RABBITMQ_URL')
MAX_POST_AGE_DAYS = int(os.getenv('MAX_POST_AGE_DAYS', 30))
FETCH_INTERVAL_SECONDS = int(os.getenv('FETCH_INTERVAL_SECONDS', 300))

# Reddit API credentials
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'InternetOfEmotions/2.0')

# Regional subreddit mapping (same as before)
REGIONS = {
    "europe": ["albania", "andorra", "austria", "belarus", "belgium", "bosnia and herzegovina",
               "bulgaria", "croatia", "czech republic", "denmark", "estonia", "finland", "france",
               "germany", "greece", "hungary", "iceland", "ireland", "italy", "kosovo", "latvia",
               "liechtenstein", "lithuania", "luxembourg", "malta", "moldova", "monaco", "montenegro",
               "netherlands", "north macedonia", "norway", "poland", "portugal", "romania", "russia",
               "san marino", "serbia", "slovakia", "slovenia", "spain", "sweden", "switzerland",
               "ukraine", "united kingdom", "vatican city"],
    "asia": ["afghanistan", "armenia", "azerbaijan", "bangladesh", "bhutan", "brunei", "cambodia",
             "china", "georgia", "india", "indonesia", "japan", "kazakhstan", "kyrgyzstan", "laos",
             "malaysia", "maldives", "mongolia", "myanmar", "nepal", "north korea", "pakistan",
             "philippines", "singapore", "south korea", "sri lanka", "tajikistan", "thailand",
             "timor-leste", "turkmenistan", "uzbekistan", "vietnam", "taiwan"],
    "africa": ["algeria", "angola", "benin", "botswana", "burkina faso", "burundi", "cabo verde",
               "cameroon", "central african republic", "chad", "comoros", "congo (brazzaville)",
               "congo (kinshasa)", "côte d'ivoire", "djibouti", "equatorial guinea", "eritrea",
               "eswatini", "ethiopia", "gabon", "gambia", "ghana", "guinea", "guinea-bissau", "kenya",
               "lesotho", "liberia", "libya", "madagascar", "malawi", "mali", "mauritania", "mauritius",
               "morocco", "mozambique", "namibia", "niger", "nigeria", "rwanda", "sao tome and principe",
               "senegal", "seychelles", "sierra leone", "somalia", "south africa", "south sudan",
               "sudan", "tanzania", "togo", "tunisia", "uganda", "zambia", "zimbabwe"],
    "americas": ["antigua and barbuda", "argentina", "bahamas", "barbados", "belize", "bolivia",
                 "brazil", "canada", "chile", "colombia", "costa rica", "cuba", "dominica",
                 "dominican republic", "ecuador", "el salvador", "grenada", "guatemala", "guyana",
                 "haiti", "honduras", "jamaica", "mexico", "nicaragua", "panama", "paraguay", "peru",
                 "saint kitts and nevis", "saint lucia", "saint vincent and the grenadines", "suriname",
                 "trinidad and tobago", "united states", "uruguay", "venezuela"],
    "oceania": ["australia", "federated states of micronesia", "fiji", "kiribati", "marshall islands",
                "nauru", "new zealand", "palau", "papua new guinea", "samoa", "solomon islands",
                "tonga", "tuvalu", "vanuatu"],
    "middleeast": ["bahrain", "cyprus", "iran", "iraq", "israel", "jordan", "kuwait", "lebanon",
                   "oman", "palestine", "qatar", "saudi arabia", "syria", "turkey",
                   "united arab emirates", "yemen"]
}

REGION_SUBREDDITS = {
    "europe": ["europe", "InternationalNews", "world", "worldnews", "news", "breakingnews"],
    "asia": ["asia", "InternationalNews", "world", "worldnews", "news", "breakingnews"],
    "africa": ["africa", "InternationalNews", "world", "worldnews", "news", "breakingnews"],
    "americas": ["latinamerica", "InternationalNews", "world", "worldnews", "news", "breakingnews"],
    "oceania": ["australia", "InternationalNews", "world", "worldnews", "news", "breakingnews"],
    "middleeast": ["middleeast", "InternationalNews", "world", "worldnews", "news", "breakingnews"]
}

# Build country-to-region mapping
COUNTRY_TO_REGION = {}
ALL_COUNTRIES = []
for region, countries in REGIONS.items():
    for country in countries:
        COUNTRY_TO_REGION[country.lower()] = region
        ALL_COUNTRIES.append(country)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database connection
def get_db_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# RabbitMQ connection
class RabbitMQPublisher:
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
            logger.info("✓ Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def publish(self, routing_key: str, message: dict):
        """Publish message to RabbitMQ"""
        try:
            import json
            self.channel.basic_publish(
                exchange='posts_exchange',
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent message
                    content_type='application/json'
                )
            )
            logger.debug(f"Published event: {routing_key}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            # Reconnect and retry
            self.connect()
            self.publish(routing_key, message)

    def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()

# Initialize RabbitMQ publisher
mq_publisher = RabbitMQPublisher(RABBITMQ_URL)

# Initialize Reddit API
logger.info("🔗 Initializing Reddit API connection...")
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)
logger.info("✓ Reddit API connected")

# ============================================================================
# POST FETCHING LOGIC
# ============================================================================

def is_image_only_post(submission) -> bool:
    """
    Check if post is image-only (no text content)
    Images WITH text body are kept
    """
    has_text = bool(submission.selftext and len(submission.selftext.strip()) > 20)
    is_image = submission.url and any(submission.url.lower().endswith(ext)
                                      for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])

    # Image-only posts: has image but NO text
    return is_image and not has_text

def is_url_only_post(submission) -> bool:
    """
    Check if post is URL-only (no text content, just a URL)
    These will be delegated to URL Extractor service
    """
    has_text = bool(submission.selftext and len(submission.selftext.strip()) > 20)
    has_url = bool(submission.url and not submission.is_self)

    # URL-only posts: has URL but NO text (and not an image)
    return has_url and not has_text and not is_image_only_post(submission)

def fetch_posts_for_country(country: str, limit: int = 50) -> List[Dict]:
    """
    Fetch posts for a specific country from Reddit

    Filtering rules:
    1. Posts ≤ 30 days old (based on reddit_created_at)
    2. Ignore image-only posts
    3. Keep URL posts (will be processed by URL Extractor)
    4. Keep text posts
    5. Keep text+image posts
    """
    posts = []
    seen_ids = set()

    # Calculate date threshold (30 days ago) - use UTC to match Reddit timestamps
    date_threshold = datetime.utcnow() - timedelta(days=MAX_POST_AGE_DAYS)
    date_threshold_timestamp = date_threshold.timestamp()

    region = COUNTRY_TO_REGION.get(country.lower(), "worldnews")
    subreddits = REGION_SUBREDDITS.get(region, ["worldnews", "news"])

    try:
        for subreddit_name in subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                search_results = subreddit.search(
                    country,
                    limit=15,
                    time_filter='month',
                    sort='new'
                )

                for submission in search_results:
                    # Filter 1: Check post age (≤30 days)
                    if submission.created_utc < date_threshold_timestamp:
                        logger.debug(f"⏭ Skipping old post from {country} (age > {MAX_POST_AGE_DAYS} days)")
                        continue

                    # Filter 2: Check for duplicates
                    if submission.id in seen_ids:
                        continue
                    seen_ids.add(submission.id)

                    # Filter 3: Skip image-only posts
                    if is_image_only_post(submission):
                        logger.debug(f"⏭ Skipping image-only post: {submission.id}")
                        continue

                    # Determine if post has URL (will need extraction)
                    has_url = is_url_only_post(submission)

                    # Extract post data
                    post_age_days = (datetime.utcnow().timestamp() - submission.created_utc) / 86400

                    posts.append({
                        'reddit_id': submission.id,
                        'title': submission.title,
                        'text': submission.selftext[:5000] if submission.selftext else None,  # Limit text length
                        'url': submission.url if not submission.is_self else None,
                        'author': str(submission.author) if submission.author else '[deleted]',
                        'subreddit': submission.subreddit.display_name,
                        'score': submission.score,
                        'num_comments': submission.num_comments,
                        'reddit_created_at': datetime.fromtimestamp(submission.created_utc),
                        'country': country,
                        'region': region,
                        'has_url': has_url,
                        'post_age_days': round(post_age_days, 1)
                    })

                    if len(posts) >= limit:
                        return posts

            except Exception as e:
                logger.debug(f"Error searching r/{subreddit_name}: {e}")
                continue

        logger.info(f"✓ Fetched {len(posts)} posts for {country}")
        return posts

    except Exception as e:
        logger.error(f"Error fetching posts for {country}: {e}")
        return []

def store_post(post: Dict) -> Optional[int]:
    """
    Store post in database
    Returns post_id if successful, None if duplicate
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO raw_posts (
                reddit_id, title, text, url, author, subreddit,
                score, num_comments, reddit_created_at, fetched_at,
                country, region, has_url
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s
            )
            ON CONFLICT (reddit_id) DO NOTHING
            RETURNING id
        """, (
            post['reddit_id'],
            post['title'],
            post['text'],
            post['url'],
            post['author'],
            post['subreddit'],
            post['score'],
            post['num_comments'],
            post['reddit_created_at'],
            post['country'],
            post['region'],
            post['has_url']
        ))

        result = cursor.fetchone()
        conn.commit()

        if result:
            post_id = result['id']
            logger.debug(f"✓ Stored post {post['reddit_id']} (ID: {post_id})")
            return post_id
        else:
            logger.debug(f"○ Post {post['reddit_id']} already exists (skipped)")
            return None

    except Exception as e:
        conn.rollback()
        logger.error(f"Error storing post {post.get('reddit_id')}: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def publish_post_fetched_event(post_id: int, post: Dict):
    """
    Publish 'post.fetched' event to RabbitMQ
    This triggers URL Extractor and ML Analyzer services
    """
    event_data = {
        'post_id': post_id,
        'reddit_id': post['reddit_id'],
        'title': post['title'],
        'text': post['text'],
        'url': post['url'],
        'has_url': post['has_url'],
        'country': post['country'],
        'timestamp': post['reddit_created_at'].isoformat()
    }

    mq_publisher.publish('post.fetched', event_data)

# ============================================================================
# CIRCULAR ROTATION FETCHING THREAD
# ============================================================================

class CircularRotation:
    """Manages circular rotation through all countries"""

    def __init__(self, countries: List[str]):
        self.countries = countries
        self.current_index = 0
        self.cycle_number = 0
        self.countries_per_batch = 10
        self.lock = threading.Lock()

        logger.info(f"🔄 Circular rotation initialized: {len(countries)} countries")
        logger.info(f"📊 Batch size: {self.countries_per_batch} countries per cycle")

    def get_next_batch(self) -> tuple:
        """Get next batch of countries in circular order"""
        with self.lock:
            batch = []

            for _ in range(self.countries_per_batch):
                batch.append(self.countries[self.current_index])
                self.current_index += 1

                # Wrap around
                if self.current_index >= len(self.countries):
                    self.current_index = 0
                    self.cycle_number += 1
                    logger.info(f"🔁 ✓ CYCLE {self.cycle_number} COMPLETE! Restarting...")

            return batch, self.cycle_number, self.current_index

circular_rotation = CircularRotation(ALL_COUNTRIES)

def fetching_thread():
    """Background thread for continuous post fetching"""
    logger.info("🚀 Starting post fetching thread...")

    while True:
        try:
            # Get next batch
            batch, cycle_num, current_idx = circular_rotation.get_next_batch()

            logger.info(f"🔄 Cycle {cycle_num} | Batch starting at index {current_idx - len(batch)}")
            logger.info(f"📥 Fetching: {batch}")

            # Fetch posts for each country in batch
            for country in batch:
                posts = fetch_posts_for_country(country, limit=50)

                new_posts = 0
                for post in posts:
                    post_id = store_post(post)
                    if post_id:
                        new_posts += 1
                        publish_post_fetched_event(post_id, post)

                logger.info(f"✓ {country}: {new_posts} new posts ({len(posts) - new_posts} duplicates)")

            # Sleep between batches
            time.sleep(FETCH_INTERVAL_SECONDS)

        except Exception as e:
            logger.error(f"❌ Error in fetching thread: {e}")
            time.sleep(30)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'post_fetcher',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/status', methods=['GET'])
def status():
    """Get fetcher status and statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get total posts
    cursor.execute("SELECT COUNT(*) as count FROM raw_posts")
    total_posts = cursor.fetchone()['count']

    # Get posts by country
    cursor.execute("""
        SELECT country, COUNT(*) as count
        FROM raw_posts
        GROUP BY country
        ORDER BY count DESC
        LIMIT 10
    """)
    top_countries = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        'total_posts': total_posts,
        'top_countries': [dict(row) for row in top_countries],
        'current_cycle': circular_rotation.cycle_number,
        'current_index': circular_rotation.current_index,
        'total_countries': len(ALL_COUNTRIES)
    })

@app.route('/api/fetch', methods=['POST'])
def fetch_manual():
    """Manually trigger fetch for specific country"""
    data = request.get_json()
    country = data.get('country')

    if not country:
        return jsonify({'error': 'country parameter required'}), 400

    if country not in ALL_COUNTRIES:
        return jsonify({'error': f'Invalid country: {country}'}), 400

    # Fetch posts
    posts = fetch_posts_for_country(country, limit=50)

    new_posts = 0
    for post in posts:
        post_id = store_post(post)
        if post_id:
            new_posts += 1
            publish_post_fetched_event(post_id, post)

    return jsonify({
        'country': country,
        'total_fetched': len(posts),
        'new_posts': new_posts,
        'duplicates': len(posts) - new_posts
    })

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🌍 Post Fetcher Service")
    logger.info("=" * 60)
    logger.info(f"📍 Max post age: {MAX_POST_AGE_DAYS} days")
    logger.info(f"⏱️  Fetch interval: {FETCH_INTERVAL_SECONDS}s")
    logger.info(f"🗺️  Tracking {len(ALL_COUNTRIES)} countries")
    logger.info("=" * 60)

    # Start fetching thread
    fetching_thread_obj = threading.Thread(target=fetching_thread, daemon=True)
    fetching_thread_obj.start()
    logger.info("✓ Fetching thread started")

    # Start Flask app
    logger.info(f"🚀 Starting Flask server on port {SERVICE_PORT}")
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False, threaded=True)
