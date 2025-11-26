"""
Internet of Emotions - OPTIMIZED Backend with CIRCULAR ROTATION
Real-time emotion analysis with guaranteed fresh data

KEY FEATURES:
1. Circular Rotation - Fetches ALL 196 countries in order (round-robin)
2. Strict 28-Day Filter - Only posts ≤4 weeks old
3. Duplicate Prevention - INSERT OR IGNORE based on post ID
4. Auto Cleanup - Removes posts older than 28 days automatically
5. Real-Time Guarantee - Always shows latest events
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import praw
import logging
import time
import os
from datetime import datetime, timedelta
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from dotenv import load_dotenv

from post_database import PostDatabase
from country_coordinates import get_coordinates
from smart_scheduler import SmartMLProcessor, SmartCacheManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# ============================================================================
# CONFIGURATION
# ============================================================================
MIN_POSTS_PER_COUNTRY = 1  # Show country on map with just 1 analyzed post
MAX_POSTS_PER_COUNTRY = 100
MAX_POST_AGE_DAYS = 28  # 4 weeks strict limit - applied during FETCH
REDDIT_FETCH_LIMIT = 25
CLEANUP_INTERVAL_HOURS = 168  # Cleanup every week (safety net only, fetch filter is primary)

# Regional mapping
REGIONS = {
    "europe": [
        "albania","andorra","austria","belarus","belgium","bosnia and herzegovina","bulgaria",
        "croatia","czech republic","denmark","estonia","finland","france","germany","greece",
        "hungary","iceland","ireland","italy","kosovo","latvia","liechtenstein","lithuania",
        "luxembourg","malta","moldova","monaco","montenegro","netherlands","north macedonia",
        "norway","poland","portugal","romania","russia","san marino","serbia","slovakia",
        "slovenia","spain","sweden","switzerland","ukraine","united kingdom","vatican city"
    ],
    "asia": [
        "afghanistan","armenia","azerbaijan","bangladesh","bhutan","brunei","cambodia","china",
        "georgia","india","indonesia","japan","kazakhstan","kyrgyzstan","laos","malaysia",
        "maldives","mongolia","myanmar","nepal","north korea","pakistan","philippines",
        "singapore","south korea","sri lanka","tajikistan","thailand","timor-leste","turkmenistan",
        "uzbekistan","vietnam","taiwan"
    ],
    "africa": [
        "algeria","angola","benin","botswana","burkina faso","burundi","cabo verde","cameroon",
        "central african republic","chad","comoros","congo (brazzaville)","congo (kinshasa)",
        "côte d'ivoire","djibouti","equatorial guinea","eritrea","eswatini","ethiopia","gabon",
        "gambia","ghana","guinea","guinea-bissau","kenya","lesotho","liberia","libya","madagascar",
        "malawi","mali","mauritania","mauritius","morocco","mozambique","namibia","niger","nigeria",
        "rwanda","sao tome and principe","senegal","seychelles","sierra leone","somalia",
        "south africa","south sudan","sudan","tanzania","togo","tunisia","uganda","zambia","zimbabwe"
    ],
    "americas": [
        "antigua and barbuda","argentina","bahamas","barbados","belize","bolivia","brazil","canada",
        "chile","colombia","costa rica","cuba","dominica","dominican republic","ecuador","el salvador",
        "grenada","guatemala","guyana","haiti","honduras","jamaica","mexico","nicaragua","panama",
        "paraguay","peru","saint kitts and nevis","saint lucia","saint vincent and the grenadines",
        "suriname","trinidad and tobago","united states","uruguay","venezuela"
    ],
    "oceania": [
        "australia","federated states of micronesia","fiji","kiribati","marshall islands","nauru",
        "new zealand","palau","papua new guinea","samoa","solomon islands","tonga","tuvalu","vanuatu"
    ],
    "middleeast": [
        "bahrain","cyprus","iran","iraq","israel","jordan","kuwait","lebanon","oman",
        "palestine","qatar","saudi arabia","syria","turkey","united arab emirates","yemen"
    ]
}

REGION_SUBREDDITS = {
    "europe":     ["europe", "worldnews", "news", "UpliftingNews", "UnderReportedNews"],
    "asia":       ["asia", "worldnews", "news", "UpliftingNews", "UnderReportedNews"],
    "africa":     ["africa", "worldnews", "news", "UpliftingNews", "UnderReportedNews"],
    "americas":   ["latinamerica","worldnews", "news", "UpliftingNews", "UnderReportedNews"],
    "oceania":    ["australia", "worldnews", "news", "UpliftingNews", "UnderReportedNews"],
    "middleeast": ["middleeast", "worldnews", "news", "UpliftingNews", "UnderReportedNews"],
}

COUNTRY_TO_REGION = {}
for region, countries in REGIONS.items():
    for country in countries:
        COUNTRY_TO_REGION[country.lower()] = region

ALL_COUNTRIES = []
for region, countries in REGIONS.items():
    ALL_COUNTRIES.extend(countries)

logger.info(f"🗺️  Tracking {len(ALL_COUNTRIES)} countries across {len(REGIONS)} regions")

# ============================================================================
# CIRCULAR ROTATION TRACKER
# ============================================================================
class CircularRotation:
    """
    Manages circular rotation through ALL countries
    Guarantees every country gets fetched in order
    """
    def __init__(self, countries):
        self.countries = countries
        self.current_index = 0
        self.cycle_number = 0
        self.countries_per_batch = 10
        self.lock = threading.Lock()

        logger.info(f"🔄 Circular rotation initialized: {len(countries)} countries")
        logger.info(f"📊 Batch size: {self.countries_per_batch} countries per cycle")
        logger.info(f"🔁 Full cycle: {len(countries)} countries = {len(countries) // self.countries_per_batch} batches")

    def get_next_batch(self):
        """Get next batch of countries in circular order"""
        with self.lock:
            batch = []

            for _ in range(self.countries_per_batch):
                batch.append(self.countries[self.current_index])
                self.current_index += 1

                # Wrap around (complete cycle)
                if self.current_index >= len(self.countries):
                    self.current_index = 0
                    self.cycle_number += 1
                    logger.info(f"🔁 ✓ CYCLE {self.cycle_number} COMPLETE! Restarting from first country...")

            return batch, self.cycle_number, self.current_index

    def get_stats(self):
        """Get rotation statistics"""
        progress = (self.current_index / len(self.countries)) * 100
        return {
            'cycle_number': self.cycle_number,
            'current_index': self.current_index,
            'total_countries': len(self.countries),
            'progress_percent': round(progress, 1),
            'countries_remaining': len(self.countries) - self.current_index
        }

# Initialize rotation
circular_rotation = CircularRotation(ALL_COUNTRIES)

# ============================================================================
# APP INITIALIZATION
# ============================================================================
app = Flask(__name__)
CORS(app)

def validate_environment():
    required_vars = ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USER_AGENT']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(f"❌ Missing: {', '.join(missing_vars)}")
    logger.info("✅ Environment validated")

validate_environment()

# Initialize database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'posts.db')
db = PostDatabase(db_path)

# Initialize SMART components
smart_ml_processor = SmartMLProcessor()
smart_cache = SmartCacheManager()

# Initialize Reddit API
logger.info("🔗 Initializing Reddit API connection...")
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT', 'EmotionsDashboard/1.0')
)
reddit.user.me()
logger.info("✓ Reddit API connected")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def get_country_region(country: str) -> str:
    """Get region for a country"""
    country_lower = country.lower()
    return COUNTRY_TO_REGION.get(country_lower, "worldnews")

def search_regional_subreddits_strict(country: str, limit: int = 50) -> list:
    """
    Search with STRICT 28-day filter and duplicate prevention
    PRIMARY AGE FILTER: Posts older than 28 days are REJECTED before storage.
    This is the main filter - cleanup function is only a safety net.
    """
    posts = []
    seen_ids = set()

    # STRICT: Only posts from last 28 days (4 weeks) - PRIMARY AGE FILTER
    date_threshold = datetime.now() - timedelta(days=MAX_POST_AGE_DAYS)
    date_threshold_timestamp = date_threshold.timestamp()

    region = get_country_region(country)
    subreddits = REGION_SUBREDDITS.get(region, ["worldnews", "news"])

    try:
        for subreddit_name in subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                search_results = subreddit.search(
                    country,
                    limit=15,
                    time_filter='month',  # Reddit filter
                    sort='new'
                )

                for submission in search_results:
                    # STRICT 28-DAY FILTER - Reject old posts BEFORE storage
                    if submission.created_utc < date_threshold_timestamp:
                        logger.debug(f"⏭ Skipping old post from {country} (age > {MAX_POST_AGE_DAYS} days)")
                        continue

                    # DUPLICATE PREVENTION
                    if submission.id in seen_ids:
                        continue
                    seen_ids.add(submission.id)

                    if submission.selftext or submission.title:
                        text = f"{submission.title}. {submission.selftext[:500]}"
                        post_age_days = (datetime.now().timestamp() - submission.created_utc) / 86400

                        posts.append({
                            'text': text,
                            'country': country,
                            'coords': get_coordinates(country),
                            'timestamp': datetime.fromtimestamp(submission.created_utc).isoformat(),
                            'source': f'r/{submission.subreddit.display_name}',
                            'id': submission.id,
                            'url': f'https://reddit.com{submission.permalink}',
                            'author': str(submission.author) if submission.author else '[deleted]',
                            'score': submission.score,
                            'num_comments': submission.num_comments,
                            'subreddit': submission.subreddit.display_name,
                            'post_age_days': round(post_age_days, 1),
                            'region': region
                        })

                        if len(posts) >= limit:
                            return posts

            except Exception as e:
                logger.debug(f"Error searching r/{subreddit_name}: {e}")
                continue

        posts.sort(key=lambda x: x['timestamp'], reverse=True)

    except Exception as e:
        logger.error(f"Error searching {country}: {e}")

    return posts

def fetch_and_store_country_smart(country: str) -> dict:
    """
    Fetch posts with duplicate prevention
    Only stores NEW posts not already in database
    """
    start_time = time.time()

    # Get existing post IDs for this country
    cursor = db.get_connection().cursor()
    cursor.execute('SELECT id FROM raw_posts WHERE country = ?', (country,))
    existing_ids = set(row[0] for row in cursor.fetchall())

    try:
        # Fetch from Reddit (strict 28-day filter)
        raw_posts = search_regional_subreddits_strict(country, limit=50)

        # Filter out duplicates
        new_posts = [p for p in raw_posts if p['id'] not in existing_ids]

        # Store only new posts
        stored = 0
        duplicates = 0
        for post in new_posts:
            if db.add_raw_post(post):
                stored += 1
            else:
                duplicates += 1

        elapsed = time.time() - start_time

        total_found = len(raw_posts)
        skipped = total_found - stored

        return {
            'country': country,
            'total_found': total_found,
            'new_posts': stored,
            'duplicates': skipped,
            'time': elapsed
        }
    except Exception as e:
        return {
            'country': country,
            'error': str(e),
            'time': time.time() - start_time
        }

def cleanup_old_posts():
    """
    SAFETY NET: Remove posts older than 28 days (4 weeks)
    NOTE: The primary age filter is applied during Reddit fetch (line 226-227).
    This cleanup is only a safety net for edge cases or manual DB entries.
    Runs infrequently (weekly) to avoid removing posts unnecessarily.
    """
    cursor = db.get_connection().cursor()
    cutoff_date = (datetime.now() - timedelta(days=MAX_POST_AGE_DAYS)).isoformat()

    # Count old posts
    cursor.execute('SELECT COUNT(*) FROM posts WHERE timestamp < ?', (cutoff_date,))
    old_posts = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM raw_posts WHERE timestamp < ?', (cutoff_date,))
    old_raw = cursor.fetchone()[0]

    if old_posts > 0 or old_raw > 0:
        logger.info(f"🧹 Removing old posts: {old_posts} analyzed, {old_raw} raw (older than {MAX_POST_AGE_DAYS} days)")

        cursor.execute('DELETE FROM posts WHERE timestamp < ?', (cutoff_date,))
        cursor.execute('DELETE FROM raw_posts WHERE timestamp < ?', (cutoff_date,))

        db.get_connection().commit()

        logger.info(f"✓ Cleanup complete: Removed {old_posts + old_raw} posts older than 4 weeks")
        return old_posts + old_raw

    return 0

def extract_top_events(posts: list, limit: int = 5) -> list:
    """
    Extract top events/topics from posts
    IMPROVED: Better topic detection + full text + always finds something
    """
    from collections import Counter, defaultdict
    import re

    if not posts:
        return []

    topic_posts = defaultdict(list)
    exclude_words = {
        'reddit', 'post', 'comment', 'user', 'thread', 'upvote',
        'says', 'said', 'report', 'news', 'today', 'yesterday'
    }

    # Strategy 1: Extract key phrases (broader patterns)
    for post in posts[:100]:  # Analyze more posts
        text = post['text']
        text_lower = text.lower()

        # EXPANDED patterns for ANY significant topic
        topic_patterns = [
            # Politics & Government
            r'(\w+)\s+(government|president|minister|parliament|election|vote|law|policy|reform)',
            r'(government|president)\s+(\w+)',

            # Economics
            r'(\w+)\s+(economy|inflation|prices|cost|tax|budget|trade|market|gdp)',
            r'(\w+)\s+prices?\s+(rise|rising|fall|falling|increase|decrease)',

            # Social Issues
            r'(\w+)\s+(crisis|shortage|conflict|protest|strike|violence|war|attack|disaster)',
            r'(climate|environmental?|pollution|energy)\s+(\w+)',

            # Health & Safety
            r'(\w+)\s+(health|medical|hospital|doctor|disease|pandemic|vaccine)',

            # Infrastructure & Development
            r'(\w+)\s+(infrastructure|development|project|construction|plan|investment)',

            # International Relations
            r'(\w+)\s+(deal|agreement|treaty|summit|visit|relations|cooperation)',

            # Technology & Innovation
            r'(\w+)\s+(technology|innovation|digital|ai|internet|cyber)',

            # General news-worthy phrases (noun + verb patterns)
            r'(\w+)\s+(announces?|launches?|plans?|begins?|ends?|signs?|approves?)',

            # Capture title phrases (first sentence often most important)
            r'^([^.!?]{20,80})',  # First 20-80 chars of title
        ]

        sentences = re.split(r'[.!?]', text)[:5]  # First 5 sentences

        for sentence in sentences:
            for pattern in topic_patterns:
                matches = re.finditer(pattern, sentence, re.IGNORECASE)
                for match in matches:
                    phrase = match.group(0).strip()

                    # Filter out garbage
                    if len(phrase) < 10 or len(phrase) > 100:
                        continue

                    if any(exclude in phrase.lower() for exclude in exclude_words):
                        continue

                    # Clean up phrase
                    phrase = phrase.replace('\n', ' ').strip()
                    phrase_key = phrase.lower()

                    # Store FULL post text (no truncation!)
                    topic_posts[phrase_key].append({
                        'text': text,  # FULL TEXT - no '...'
                        'emotion': post.get('emotion', 'neutral'),
                        'score': post.get('score', 0),
                        'url': post.get('url', '#'),
                        'source': post.get('source', 'unknown'),
                        'timestamp': post.get('timestamp', '')
                    })

    # Build topic list
    topic_scores = []
    for phrase, related_posts in topic_posts.items():
        if len(related_posts) >= 1:  # Even 1 post is a topic
            # Sort posts by score (engagement)
            related_posts.sort(key=lambda x: x['score'], reverse=True)

            # Clean phrase for display
            display_phrase = phrase.title()

            topic_scores.append({
                'topic': display_phrase,
                'count': len(related_posts),
                'avg_engagement': sum(p['score'] for p in related_posts) / len(related_posts),
                'top_post': related_posts[0],  # Highest engagement
                'sample_posts': related_posts[:3]
            })

    # Sort by: count first, then engagement
    topic_scores.sort(key=lambda x: (x['count'], x['avg_engagement']), reverse=True)

    # If we found topics, return them
    if topic_scores:
        return topic_scores[:limit]

    # FALLBACK: If no topics found, use most engaged posts as "topics"
    logger.debug(f"No topics found, using fallback (most engaged posts)")

    fallback_topics = []
    # Sort posts by engagement
    sorted_posts = sorted(posts[:20], key=lambda x: x.get('score', 0), reverse=True)

    for post in sorted_posts[:limit]:
        # Extract first sentence as topic
        text = post['text']
        first_sentence = re.split(r'[.!?]', text)[0].strip()

        if len(first_sentence) > 15:
            fallback_topics.append({
                'topic': first_sentence[:80],  # First 80 chars
                'count': 1,
                'avg_engagement': post.get('score', 0),
                'top_post': {
                    'text': text,  # FULL TEXT
                    'emotion': post.get('emotion', 'neutral'),
                    'score': post.get('score', 0),
                    'url': post.get('url', '#'),
                    'source': post.get('source', 'unknown')
                },
                'sample_posts': [{
                    'text': text,
                    'emotion': post.get('emotion', 'neutral'),
                    'score': post.get('score', 0)
                }]
            })

    return fallback_topics if fallback_topics else [{
        'topic': 'General Discussion',
        'count': len(posts),
        'avg_engagement': 0,
        'top_post': {
            'text': posts[0]['text'] if posts else 'No recent discussions',
            'emotion': posts[0].get('emotion', 'neutral') if posts else 'neutral',
            'score': 0,
            'url': '#'
        },
        'sample_posts': []
    }]

# ============================================================================
# CIRCULAR ROTATION THREAD
# ============================================================================
def circular_collection_thread():
    """
    Fetches ALL countries in circular rotation
    Guarantees every country gets fresh data
    """
    logger.info("🔄 Starting CIRCULAR ROTATION collection thread...")
    logger.info(f"📊 Will fetch ALL {len(ALL_COUNTRIES)} countries in order")
    logger.info(f"🔁 Each cycle = {len(ALL_COUNTRIES)} countries")
    logger.info(f"⏱️  Estimated cycle time: ~{len(ALL_COUNTRIES) * 2 / 60:.0f} minutes")

    last_cleanup = time.time()

    while True:
        try:
            # Get next batch in rotation
            batch, cycle_num, current_idx = circular_rotation.get_next_batch()

            logger.info(f"🔄 Cycle {cycle_num} | Batch starting at index {current_idx - len(batch)}")
            logger.info(f"📥 Fetching: {batch}")

            # Fetch in parallel
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_country = {
                    executor.submit(fetch_and_store_country_smart, country): country
                    for country in batch
                }

                for future in as_completed(future_to_country):
                    result = future.result()

                    if 'error' in result:
                        logger.error(f"❌ {result['country']}: {result['error']}")
                    else:
                        if result['new_posts'] > 0:
                            logger.info(
                                f"✓ {result['country']}: "
                                f"{result['new_posts']} new posts "
                                f"({result['duplicates']} duplicates skipped) "
                                f"in {result['time']:.1f}s"
                            )
                        else:
                            logger.info(
                                f"○ {result['country']}: No new posts "
                                f"({result['total_found']} already in DB)"
                            )

            # Periodic cleanup
            if time.time() - last_cleanup > CLEANUP_INTERVAL_HOURS * 3600:
                logger.info("🧹 Running scheduled cleanup...")
                cleanup_old_posts()
                last_cleanup = time.time()

            # Rotation stats
            stats = circular_rotation.get_stats()
            logger.info(
                f"🔁 Rotation: {stats['progress_percent']}% "
                f"({stats['current_index']}/{stats['total_countries']}) "
                f"| Cycle #{stats['cycle_number']}"
            )

            # Brief pause between batches
            time.sleep(2)

        except Exception as e:
            logger.error(f"❌ Error in circular rotation: {e}")
            time.sleep(30)

def smart_analysis_thread():
    """ML analysis with lazy loading"""
    logger.info("🧠 Starting SMART ML analysis thread...")

    last_cleanup = time.time()
    cleanup_interval = 3600

    while True:
        try:
            # Periodic cleanup
            if time.time() - last_cleanup > cleanup_interval:
                smart_cache.clear_expired()
                last_cleanup = time.time()

            # Check for idle ML models
            smart_ml_processor.unload_models_if_idle()

            # Get unanalyzed posts
            unanalyzed_count = db.get_unanalyzed_count()

            if unanalyzed_count > 0:
                batch_size = min(50, unanalyzed_count)
                batch = db.get_unanalyzed_posts(limit=batch_size)

                processed = smart_ml_processor.process_batch_smart(batch, db)

                logger.info(f"✓ Processed {processed}/{len(batch)} posts")

            # Adaptive sleep
            sleep_time = 2 if unanalyzed_count > 50 else 5
            time.sleep(sleep_time)

        except Exception as e:
            logger.error(f"❌ Error in analysis: {e}")
            time.sleep(10)

# ============================================================================
# API ENDPOINTS
# ============================================================================
@app.route('/api/emotions')
def get_emotions():
    """Get emotions with caching"""
    cached = smart_cache.get('emotions', 'all')
    if cached:
        return jsonify(cached)

    ready_countries = db.get_countries_ready_for_display(min_posts=MIN_POSTS_PER_COUNTRY)

    all_emotions = []
    for country in ready_countries:
        # No age filter - posts already filtered during fetch
        posts = db.get_posts_by_country(country, limit=20, collective_only=True, max_age_days=None)
        all_emotions.extend(posts[:10])

    result = {
        'emotions': all_emotions,
        'count': len(all_emotions),
        'countries_ready': len(ready_countries),
        'max_age_days': MAX_POST_AGE_DAYS  # Still shown for info, but not used in query
    }

    smart_cache.set('emotions', 'all', result)
    return jsonify(result)

@app.route('/api/stats')
def get_stats():
    """Get statistics"""
    cached = smart_cache.get('global_stats', 'all')
    if cached:
        return jsonify(cached)

    ready_countries = db.get_countries_ready_for_display(min_posts=MIN_POSTS_PER_COUNTRY)

    by_emotion = defaultdict(int)
    by_country = defaultdict(int)

    for country in ready_countries:
        posts = db.get_posts_by_country(country, limit=1000, collective_only=True, max_age_days=None)
        for post in posts:
            by_emotion[post['emotion']] += 1
            by_country[post['country']] += 1

    result = {
        'total': sum(by_emotion.values()),
        'by_emotion': dict(by_emotion),
        'by_country': dict(by_country),
        'countries_ready': len(ready_countries),
        'max_age_days': MAX_POST_AGE_DAYS
    }

    smart_cache.set('global_stats', 'all', result)
    return jsonify(result)

@app.route('/api/country/<country>')
def get_country_details(country):
    """Get country details"""
    cached = smart_cache.get('country_details', country)
    if cached:
        return jsonify(cached)

    posts = db.get_posts_by_country(country, limit=1000, collective_only=True, max_age_days=None)
    country_emotion = db.get_country_aggregated_emotion(country)
    top_events = extract_top_events(posts, limit=5)

    result = {
        'country': country,
        'total_posts': len(posts),
        'emotion_distribution': db.get_country_emotion_distribution(country, max_age_days=None),
        'country_emotion': {
            'dominant_emotion': country_emotion['dominant_emotion'],
            'confidence': country_emotion['confidence'],
            'method': country_emotion['method']
        },
        'top_events': top_events,
        'max_age_days': MAX_POST_AGE_DAYS
    }

    smart_cache.set('country_details', country, result)
    return jsonify(result)

@app.route('/api/progress')
def get_progress():
    """Get collection progress"""
    rotation_stats = circular_rotation.get_stats()

    progress = []
    for country in ALL_COUNTRIES:
        raw_count = db.get_raw_post_count(country)
        analyzed_count = db.get_country_post_count(country)

        progress.append({
            'country': country,
            'raw_posts': raw_count,
            'analyzed_posts': analyzed_count,
            'ready': analyzed_count >= MIN_POSTS_PER_COUNTRY
        })

    return jsonify({
        'countries': progress,
        'ready_countries': sum(1 for p in progress if p['ready']),
        'total_countries': len(ALL_COUNTRIES),
        'rotation': rotation_stats,
        'max_age_days': MAX_POST_AGE_DAYS,
        'ml_models_loaded': smart_ml_processor.models_loaded,
        'unanalyzed_queue': db.get_unanalyzed_count()
    })

@app.route('/api/health')
def health():
    """Health check"""
    rotation_stats = circular_rotation.get_stats()

    return jsonify({
        'status': 'healthy',
        'rotation': rotation_stats,
        'max_age_days': MAX_POST_AGE_DAYS,
        'countries_tracked': len(ALL_COUNTRIES),
        'optimizations': {
            'circular_rotation': True,
            'strict_28day_filter': True,
            'duplicate_prevention': True,
            'auto_cleanup': True,
            'lazy_ml_loading': True,
            'ml_models_loaded': smart_ml_processor.models_loaded
        }
    })

@app.route('/api/posts/stream')
def stream_posts():
    """SSE stream"""
    def generate():
        while True:
            try:
                ready_countries = db.get_countries_ready_for_display(min_posts=MIN_POSTS_PER_COUNTRY)
                if ready_countries:
                    import random
                    country = random.choice(ready_countries)
                    posts = db.get_posts_by_country(country, limit=100, collective_only=True, max_age_days=None)
                    if posts:
                        post = random.choice(posts)
                        yield f"data: {json.dumps(post)}\n\n"
                time.sleep(30)
            except Exception as e:
                logger.error(f"Stream error: {e}")
                time.sleep(10)

    return Response(generate(), mimetype='text/event-stream')

# ============================================================================
# STARTUP
# ============================================================================
if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🌍 Internet of Emotions - FIXED OPTIMIZED Backend")
    logger.info("=" * 60)
    logger.info(f"📍 Max post age: {MAX_POST_AGE_DAYS} days (4 weeks)")
    logger.info(f"🔁 Circular rotation: ALL {len(ALL_COUNTRIES)} countries")
    logger.info(f"🚫 Duplicate prevention: ENABLED")
    logger.info(f"🧹 Auto cleanup: Every {CLEANUP_INTERVAL_HOURS} hour(s) (safety net)")
    logger.info("=" * 60)

    # Skip startup cleanup - age filter works at fetch time
    # cleanup_old_posts()  # Disabled: Let scheduled cleanup handle edge cases only
    logger.info("✓ Age filter: Active during fetch (28-day limit enforced)")

    # Start circular rotation thread
    collection_thread = threading.Thread(target=circular_collection_thread, daemon=True)
    collection_thread.start()
    logger.info("✓ Circular rotation thread started")

    # Start analysis thread
    analysis_thread = threading.Thread(target=smart_analysis_thread, daemon=True)
    analysis_thread.start()
    logger.info("✓ Analysis thread started")

    logger.info("🚀 Starting Flask server on http://0.0.0.0:5000")
    logger.info("=" * 60)

    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
