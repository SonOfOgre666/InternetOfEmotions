"""
Internet of Emotions - Main Backend
Real-time emotion analysis from global Reddit data with collective intelligence
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import praw
import logging
import time
import random
import os
from datetime import datetime
from collections import defaultdict, Counter
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed  # For parallel fetching

from post_database import PostDatabase

from flask import Flask, jsonify, Response
from flask_cors import CORS
import praw
import os
from datetime import datetime
import time
import json
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed  # For parallel fetching
from emotion_analyzer import EmotionAnalyzer
from collective_analyzer import CollectiveAnalyzer
from post_database import PostDatabase
from country_coordinates import get_coordinates
from multimodal_analyzer import MultimodalAnalyzer
from cross_country_detector import CrossCountryDetector
from collections import defaultdict
import random
import threading
import logging
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))


# ============================================================================
# RATE LIMITER - Prevent Reddit API ban (60 requests/minute limit)
# ============================================================================
class RateLimiter:
    """
    Rate limiter for Reddit API calls
    Reddit limit: 60 requests per minute
    """
    def __init__(self, max_calls=55, period=60):
        self.max_calls = max_calls  # 55 to leave buffer
        self.period = period  # 60 seconds
        self.calls = []
        self.lock = threading.Lock()
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.lock:
                now = time.time()
                # Remove calls older than period
                self.calls = [c for c in self.calls if now - c < self.period]
                
                if len(self.calls) >= self.max_calls:
                    sleep_time = self.period - (now - self.calls[0]) + 0.1
                    logger.warning(f"⏱️ Rate limit reached ({len(self.calls)}/{self.max_calls}), sleeping {sleep_time:.1f}s")
                    time.sleep(sleep_time)
                    # Clear old calls after sleep
                    now = time.time()
                    self.calls = [c for c in self.calls if now - c < self.period]
                
                self.calls.append(now)
            
            return func(*args, **kwargs)
        return wrapper

# Initialize rate limiter
reddit_rate_limiter = RateLimiter(max_calls=55, period=60)


app = Flask(__name__)
# Configure CORS with origin restrictions
CORS(app, resources={
    r"/*": {
        "origins": os.getenv('FRONTEND_URL', 'http://localhost:3000'),
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Validate required environment variables
def validate_environment():
    """Validate that all required environment variables are set"""
    required_vars = [
        'REDDIT_CLIENT_ID',
        'REDDIT_CLIENT_SECRET',
        'REDDIT_USER_AGENT'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        error_msg = f"❌ Missing required environment variables: {', '.join(missing_vars)}\n"
        error_msg += "Please set these in your .env file or environment."
        logger.error(error_msg)
        raise EnvironmentError(error_msg)
    
    logger.info("✅ All required environment variables are set")

# Run validation before initializing Reddit client
validate_environment()


class ModelManager:
    """
    Singleton pattern for ML models - loads models once and shares across threads
    Prevents memory bloat from loading 4 models × 3 threads = 12GB+ RAM usage
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        logger.info("🤖 Loading ML models (singleton)...")
        self.emotion_analyzer = EmotionAnalyzer()
        self.collective_analyzer = CollectiveAnalyzer()
        self.multimodal_analyzer = MultimodalAnalyzer()
        self.cross_country_detector = CrossCountryDetector()
        logger.info("✅ ML models loaded successfully")
        
        self._initialized = True
    
    @classmethod
    def get_models(cls):
        """Get singleton instance of all models"""
        instance = cls()
        return {
            'emotion': instance.emotion_analyzer,
            'collective': instance.collective_analyzer,
            'multimodal': instance.multimodal_analyzer,
            'cross_country': instance.cross_country_detector
        }


# Initialize ML models using singleton pattern
models = ModelManager.get_models()
emotion_analyzer = models['emotion']
collective_analyzer = models['collective']
multimodal_analyzer = models['multimodal']
cross_country_detector = models['cross_country']

# Use absolute path to ensure database is always in backend directory
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'posts.db')
db = PostDatabase(db_path)

# Configuration
MIN_POSTS_PER_COUNTRY = 5  # Reduced to 5 to show more countries initially
MAX_POSTS_PER_COUNTRY = 100
PATTERN_DETECTION_THRESHOLD = 5
UPDATE_INTERVAL_MINUTES = 5
REDDIT_FETCH_LIMIT = 25  # Posts to fetch per subreddit (not per country)
MAX_WORKERS = 3  # Number of parallel fetch threads (OPTIMIZATION)

# Regional mapping for targeted subreddit searches
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

# Subreddits per region for targeted searches
REGION_SUBREDDITS = {
    "europe":     ["europe", "worldnews", "news", "UpliftingNews", "UnderReportedNews"],
    "asia":       ["asia", "worldnews", "news", "UpliftingNews", "UnderReportedNews"],
    "africa":     ["africa", "worldnews", "news", "UpliftingNews", "UnderReportedNews"],
    "americas":   ["worldnews", "news", "latinamerica", "UpliftingNews", "UnderReportedNews"],
    "oceania":    ["australia", "worldnews", "news", "UpliftingNews", "UnderReportedNews"],
    "middleeast": ["middleeast", "worldnews", "news", "UpliftingNews", "UnderReportedNews"],
}

# Build reverse lookup: country -> region
COUNTRY_TO_REGION = {}
for region, countries in REGIONS.items():
    for country in countries:
        COUNTRY_TO_REGION[country.lower()] = region

# Build flat list of all tracked countries
ALL_COUNTRIES = []
for region, countries in REGIONS.items():
    ALL_COUNTRIES.extend(countries)

logger.info(f"🗺️  Tracking {len(ALL_COUNTRIES)} countries across {len(REGIONS)} regions")

# Initialize Reddit API - REAL DATA ONLY
logger.info("🔗 Initializing Reddit API connection...")
reddit = None
try:
    reddit = praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        user_agent=os.getenv('REDDIT_USER_AGENT', 'EmotionsDashboard/1.0')
    )
    # Test connection
    reddit.user.me()
    logger.info("✓ Reddit API connected successfully - Using REAL DATA")
except Exception as e:
    logger.error(f"❌ Reddit API connection failed: {e}")
    logger.error("Please configure REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, and REDDIT_USER_AGENT in .env file")
    raise SystemExit("Cannot start without Reddit API credentials")


def get_country_region(country: str) -> str:
    """Get the region for a country (for targeted subreddit search)"""
    country_lower = country.lower()
    
    # Direct lookup
    if country_lower in COUNTRY_TO_REGION:
        return COUNTRY_TO_REGION[country_lower]
    
    # Fuzzy matching for variations
    for region, countries in REGIONS.items():
        for c in countries:
            if country_lower in c or c in country_lower:
                return region
    
    # Default fallback
    return "worldnews"


@reddit_rate_limiter
def search_regional_subreddits(country: str, limit: int = 50) -> list:
    """
    Search region-specific subreddits for posts about a country
    NEW STRATEGY: Targeted subreddit searches instead of global search
    
    Example: Albania (Europe) -> Search in r/europe, r/worldnews, r/news for "albania"
    """
    posts = []
    seen_ids = set()  # Prevent duplicates
    
    # Calculate date threshold (only posts from last 30 days)
    from datetime import timedelta
    date_threshold = datetime.now() - timedelta(days=30)
    date_threshold_timestamp = date_threshold.timestamp()
    
    # Get region for this country
    region = get_country_region(country)
    
    # Get subreddits for this region
    subreddits = REGION_SUBREDDITS.get(region, ["worldnews", "news"])
    
    logger.info(f"🔍 Searching for {country} in region '{region}' subreddits: {subreddits}")
    
    try:
        # Search each regional subreddit
        for subreddit_name in subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                
                # Search for country name in this subreddit
                # Using .search() with sort=new to get recent posts
                search_results = subreddit.search(
                    country,  # Search query = country name
                    limit=15,  # Posts per subreddit
                    time_filter='month',  # Only last 30 days
                    sort='new'  # Sort by newest first
                )
                
                for submission in search_results:
                    # DATE FILTER: Skip posts older than 30 days
                    if submission.created_utc < date_threshold_timestamp:
                        continue
                    
                    # Skip duplicates
                    if submission.id in seen_ids:
                        continue
                    seen_ids.add(submission.id)
                    
                    # Must have content
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
                            'search_query': f'{country} in r/{subreddit_name}',
                            'post_age_days': round(post_age_days, 1),
                            'region': region
                        })
                        
                        # Stop early if we have enough posts
                        if len(posts) >= limit:
                            logger.info(f"✓ Found {len(posts)} posts for {country} from regional search (stopped early)")
                            return posts
                            
            except Exception as e:
                logger.debug(f"  ✗ Error searching r/{subreddit_name} for {country}: {e}")
                continue
        
        # Sort by date (newest first)
        posts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        if posts:
            oldest_post_days = (datetime.now() - datetime.fromisoformat(posts[-1]['timestamp'])).days
            logger.info(f"✓ Found {len(posts)} posts for {country} from regional subreddits (newest to {oldest_post_days}d old)")
        else:
            logger.info(f"⚠ Found 0 posts for {country} from regional subreddits")
        
    except Exception as e:
        logger.error(f"❌ Error in regional search for {country}: {e}")
    
    return posts


def process_and_store_posts(posts: list) -> list:
    """Process posts with AI analysis and store in database"""
    processed_posts = []

    for post in posts:
        try:
            # Text emotion analysis
            emotion_result = emotion_analyzer.analyze(post['text'])

            # Collective issue detection
            collective_result = collective_analyzer.analyze_post(post['text'])

            # Cross-country detection - find what countries are discussed
            cross_country_result = cross_country_detector.detect_countries(post['text'])
            cross_analysis = cross_country_detector.get_cross_country_analysis(
                post['country'],
                cross_country_result['countries']
            )

            # Optional: Multimodal analysis if images present
            media_analysis = multimodal_analyzer.analyze_reddit_media(post)

            # Combine all analysis
            post_data = {
                **post,
                'emotion': emotion_result['emotion'],
                'confidence': emotion_result['confidence'],
                'is_collective': collective_result['is_collective'],
                'collective_score': collective_result['collective_score'],
                'has_media': media_analysis['has_media'],
                'media_type': media_analysis['media_type'],
                'media_emotion': media_analysis['analysis']['emotion'] if media_analysis['analysis'] else None,
                'media_confidence': media_analysis['analysis']['confidence'] if media_analysis['analysis'] else None,
                # NEW: Cross-country detection data
                'mentioned_countries': cross_country_result['countries'],
                'primary_subject_country': cross_country_result['primary_country'],
                'country_detection_confidence': cross_country_result['confidence'],
                'is_cross_country': cross_analysis['is_cross_country'],
                'country_mentions_count': cross_country_result['mention_count'],
                'detection_methods': cross_country_result['method']
            }

            # Store in database
            if db.add_post(post_data):
                processed_posts.append(post_data)

                # If post is about another country, also add to that country's list
                if cross_analysis['is_cross_country'] and cross_country_result['primary_country']:
                    subject_country = cross_country_result['primary_country']
                    # Create copy with country changed
                    cross_post = post_data.copy()
                    cross_post['country'] = subject_country
                    cross_post['source_country'] = post['country']
                    cross_post['is_cross_country_reference'] = True
                    
                    if db.add_post(cross_post):
                        logger.info(f"✓ Added cross-country post: {post.get('id')} to {subject_country}")

        except Exception as e:
            logger.warning(f"Error processing post {post.get('id')}: {e}")
            continue

    return processed_posts


def detect_country_patterns(country: str) -> list:
    """Detect patterns in country posts"""
    posts = db.get_posts_by_country(country, limit=1000)

    if len(posts) >= PATTERN_DETECTION_THRESHOLD:
        try:
            patterns = collective_analyzer.detect_collective_patterns(
                [p['text'] for p in posts],
                min_pattern_size=PATTERN_DETECTION_THRESHOLD
            )
            return patterns if patterns else []
        except Exception as e:
            logger.debug(f"Error detecting patterns for {country}: {e}")
            return []

    return []


def extract_top_events(posts: list, limit: int = 5) -> list:
    """
    Extract top events/topics from posts using NLP and frequency analysis
    Returns list of important topics with their frequency and sample posts
    
    IMPROVED: Filters out generic global news, focuses on country-specific issues
    """
    from collections import Counter
    import re
    
    if not posts:
        return []
    
    # Extract actual topic phrases (2-4 words) from post titles/text
    topic_posts = {}  # topic phrase -> list of posts
    
    # Words to exclude (too generic or global)
    exclude_words = {
        'reddit', 'post', 'comment', 'user', 'thread', 'upvote', 'downvote',
        'says', 'said', 'report', 'news', 'today', 'yesterday', 'week',
        'italian', 'ukrainian', 'american', 'hawaii', 'federal', 'dick', 'cheney',
        'judge', 'declares', 'confirms', 'rules', 'online', 'porn', 'made', 'illegal'
    }
    
    for post in posts[:50]:  # First 50 posts only
        text = post['text'].lower()
        
        # Extract meaningful noun phrases (2-4 words)
        # Look for capitalized phrases or important patterns
        sentences = re.split(r'[.!?]', text)
        
        for sentence in sentences[:3]:  # First 3 sentences only
            # Look for patterns like "X crisis", "X shortage", "X protest", etc.
            crisis_patterns = [
                r'(\w+)\s+(crisis|shortage|conflict|protest|strike|election|violence|war|corruption|inflation|unemployment|disaster|emergency)',
                r'(rising|high|record)\s+(\w+)',
                r'(\w+)\s+(increase|decrease|collapse|breakdown)',
                r'government\s+(\w+)',
                r'(\w+)\s+prices'
            ]
            
            for pattern in crisis_patterns:
                matches = re.finditer(pattern, sentence)
                for match in matches:
                    phrase = match.group(0).strip()
                    
                    # Filter out generic/global events
                    if any(exclude in phrase.lower() for exclude in exclude_words):
                        continue
                    
                    # Only keep if phrase is 2+ words and relevant
                    if len(phrase.split()) >= 2 and len(phrase) > 5:
                        if phrase not in topic_posts:
                            topic_posts[phrase] = []
                        
                        topic_posts[phrase].append({
                            'text': post['text'][:150] + '...',
                            'emotion': post.get('emotion', 'neutral'),
                            'score': post.get('score', 0),
                            'url': post.get('url', '#'),
                            'source': post.get('source', 'unknown')
                        })
    
    # Rank topics by frequency and relevance
    topic_scores = []
    for phrase, related_posts in topic_posts.items():
        if len(related_posts) >= 2:  # At least 2 posts mention this
            total_score = sum(p['score'] for p in related_posts)
            avg_score = total_score / len(related_posts)
            
            topic_scores.append({
                'topic': phrase.title(),
                'count': len(related_posts),
                'avg_engagement': round(avg_score, 1),
                'top_post': related_posts[0],
                'sample_posts': related_posts[:3]
            })
    
    # Sort by count
    topic_scores.sort(key=lambda x: (x['count'], x['avg_engagement']), reverse=True)
    
    # If no specific topics found, fall back to showing top emotion keywords
    if not topic_scores:
        return [{
            'topic': 'General Discussion',
            'count': len(posts),
            'avg_engagement': 0,
            'top_post': {
                'text': posts[0]['text'][:150] + '...' if posts else 'No details available',
                'emotion': posts[0].get('emotion', 'neutral') if posts else 'neutral',
                'score': 0,
                'url': '#'
            },
            'sample_posts': []
        }]
    
    return topic_scores[:limit]


def fetch_and_store_country(country: str) -> dict:
    """
    Fetch and store posts for a single country (for parallel execution)
    Returns: {'country': str, 'stored': int, 'time': float}
    """
    start_time = time.time()
    raw_count = db.get_raw_post_count(country)
    
    # Skip if already have enough posts
    if raw_count >= 100:
        return {'country': country, 'stored': 0, 'time': 0, 'skipped': True}
    
    fetch_limit = min(50, 100 - raw_count)
    
    try:
        # NEW: Use regional subreddit search (more targeted & relevant)
        raw_posts = search_regional_subreddits(country, limit=fetch_limit)
        
        stored = 0
        if raw_posts:
            for post in raw_posts:
                if db.add_raw_post(post):
                    stored += 1
        
        elapsed = time.time() - start_time
        return {
            'country': country,
            'stored': stored,
            'time': elapsed,
            'skipped': False
        }
    except Exception as e:
        logger.error(f"Error fetching posts for {country}: {e}")
        return {
            'country': country,
            'stored': 0,
            'time': time.time() - start_time,
            'error': str(e)
        }


def thread_error_recovery(func, thread_name: str, max_retries: int = 5):
    """
    Wrapper for background threads with error recovery and exponential backoff
    Prevents permanent thread death from single failures
    """
    retry_count = 0
    backoff_seconds = 30
    
    def wrapper():
        nonlocal retry_count, backoff_seconds
        
        while retry_count < max_retries:
            try:
                logger.info(f"✓ {thread_name} thread started (attempt {retry_count + 1}/{max_retries})")
                func()  # Run the actual thread function
                
            except Exception as e:
                retry_count += 1
                logger.error(f"❌ {thread_name} thread crashed: {e}")
                
                if retry_count >= max_retries:
                    logger.critical(f"💀 {thread_name} thread failed {max_retries} times. Giving up.")
                    break
                
                # Exponential backoff: 30s, 60s, 120s, 240s, 480s
                logger.warning(f"🔄 Restarting {thread_name} in {backoff_seconds}s (attempt {retry_count + 1}/{max_retries})")
                time.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, 480)  # Cap at 8 minutes
        
        logger.error(f"💀 {thread_name} thread permanently stopped after {max_retries} failures")
    
    return wrapper


def collect_posts_background():
    """
    Background thread to fetch posts from Reddit
    OPTIMIZED: Uses parallel fetching with ThreadPoolExecutor
    NEW: Regional subreddit search strategy for targeted, relevant posts
    """
    logger.info("🔄 Starting fast Reddit post collection thread...")
    logger.info("� Using REGIONAL SUBREDDIT SEARCH for targeted country posts")
    logger.info(f"📍 Regions: {list(REGIONS.keys())}")
    logger.info("⚡ PARALLEL FETCHING: Processing 3 countries simultaneously")

    while True:
        try:
            all_countries = ALL_COUNTRIES.copy()
            random.shuffle(all_countries)
            
            # Filter countries that need more posts
            countries_needing_posts = [
                c for c in all_countries 
                if db.get_raw_post_count(c) < 100
            ]
            
            if not countries_needing_posts:
                logger.info("⏸ All countries have 100+ posts. Waiting 5 minutes...")
                time.sleep(300)
                continue
            
            logger.info(f"📥 Fetching posts for {len(countries_needing_posts)} countries using parallel processing...")
            
            # PARALLEL PROCESSING: Fetch 3 countries at once
            with ThreadPoolExecutor(max_workers=3) as executor:
                # Submit all countries to the thread pool
                future_to_country = {
                    executor.submit(fetch_and_store_country, country): country 
                    for country in countries_needing_posts
                }
                
                # Process completed tasks as they finish
                for future in as_completed(future_to_country):
                    result = future.result()
                    
                    if result.get('skipped'):
                        continue
                    
                    if result.get('error'):
                        logger.error(f"❌ {result['country']}: {result['error']}")
                    else:
                        logger.info(
                            f"✓ {result['country']}: Stored {result['stored']} posts "
                            f"in {result['time']:.1f}s"
                        )

            logger.info(f"⏸ Fetching cycle complete. Waiting 2 minutes before next cycle...")
            time.sleep(120)  # 2 minutes between full cycles

        except Exception as e:
            logger.error(f"❌ Error in post collection: {e}")
            time.sleep(30)




def analyze_posts_background():
    """Background thread to analyze raw posts with ML models (independent)"""
    logger.info("🤖 Starting ML analysis thread...")
    
    # Track cleanup cycle (cleanup old posts every hour)
    last_cleanup = time.time()
    cleanup_interval = 3600  # 1 hour in seconds
    
    while True:
        try:
            # Periodic cleanup of old posts (every hour)
            if time.time() - last_cleanup > cleanup_interval:
                logger.info("🧹 Running periodic cleanup of posts older than  days...")
                deleted_count = db.cleanup_old_posts(days=2, max_posts_per_country=200)
                if deleted_count > 0:
                    logger.info(f"✓ Cleaned up {deleted_count} old posts")
                last_cleanup = time.time()
            
            # Get unanalyzed posts
            unanalyzed_count = db.get_unanalyzed_count()
            
            if unanalyzed_count > 0:
                logger.info(f"🔬 Analyzing {unanalyzed_count} unanalyzed posts...")
                
                # Process in batches of 100 (INCREASED for faster processing)
                batch = db.get_unanalyzed_posts(limit=100)
                
                for post in batch:
                    try:
                        # Text emotion analysis
                        emotion_result = emotion_analyzer.analyze(post['text'])

                        # Collective issue detection
                        collective_result = collective_analyzer.analyze_post(post['text'])

                        # Cross-country detection
                        cross_country_result = cross_country_detector.detect_countries(post['text'])
                        cross_analysis = cross_country_detector.get_cross_country_analysis(
                            post['country'],
                            cross_country_result['countries']
                        )

                        # Optional: Multimodal analysis
                        media_analysis = multimodal_analyzer.analyze_reddit_media(post)

                        # Combine all analysis
                        post_data = {
                            **post,
                            'emotion': emotion_result['emotion'],
                            'confidence': emotion_result['confidence'],
                            'is_collective': collective_result['is_collective'],
                            'collective_score': collective_result['collective_score'],
                            'has_media': media_analysis['has_media'],
                            'media_type': media_analysis['media_type'],
                            'media_emotion': media_analysis['analysis']['emotion'] if media_analysis['analysis'] else None,
                            'media_confidence': media_analysis['analysis']['confidence'] if media_analysis['analysis'] else None,
                            'mentioned_countries': cross_country_result['countries'],
                            'primary_subject_country': cross_country_result['primary_country'],
                            'country_detection_confidence': cross_country_result['confidence'],
                            'is_cross_country': cross_analysis['is_cross_country'],
                            'country_mentions_count': cross_country_result['mention_count'],
                            'detection_methods': cross_country_result['method']
                        }

                        # Store analyzed post
                        if db.add_post(post_data):
                            db.mark_post_analyzed(post['id'])
                            
                            # Handle cross-country posts
                            if cross_analysis['is_cross_country'] and cross_country_result['primary_country']:
                                subject_country = cross_country_result['primary_country']
                                cross_post = post_data.copy()
                                cross_post['country'] = subject_country
                                cross_post['source_country'] = post['country']
                                cross_post['is_cross_country_reference'] = True
                                db.add_post(cross_post)

                    except Exception as e:
                        logger.warning(f"Error analyzing post {post.get('id')}: {e}")
                        # Mark as analyzed even if failed to avoid infinite retries
                        db.mark_post_analyzed(post['id'])
                        continue
                
                logger.info(f"✓ Batch analysis complete. {db.get_unanalyzed_count()} remaining.")
            
            else:
                logger.debug("No unanalyzed posts. Waiting...")
            
            time.sleep(0.5)  # Check for new posts every 0.5 seconds (FASTER processing)

        except Exception as e:
            logger.error(f"❌ Error in analysis thread: {e}")
            time.sleep(10)


# API Endpoints

@app.route('/api/emotions')
def get_emotions():
    """Get emotions from countries ready for display (collective posts only)"""
    ready_countries = db.get_countries_ready_for_display(min_posts=MIN_POSTS_PER_COUNTRY)

    all_emotions = []
    for country in ready_countries:
        # Get ONLY collective posts (filter out personal issues)
        posts = db.get_posts_by_country(country, limit=20, collective_only=True)
        sampled = posts[:10] if len(posts) > 10 else posts
        all_emotions.extend(sampled)

    return jsonify({
        'emotions': all_emotions,
        'count': len(all_emotions),
        'countries_ready': len(ready_countries)
    })


@app.route('/api/stats')
def get_stats():
    """Get emotion statistics across ready countries"""
    ready_countries = db.get_countries_ready_for_display(min_posts=MIN_POSTS_PER_COUNTRY)

    by_emotion = defaultdict(int)
    by_country = defaultdict(int)

    for country in ready_countries:
        posts = db.get_collective_posts(country, min_cluster_size=PATTERN_DETECTION_THRESHOLD)

        for post in posts:
            by_emotion[post['emotion']] += 1
            by_country[post['country']] += 1

    return jsonify({
        'total': sum(by_emotion.values()),
        'by_emotion': dict(by_emotion),
        'by_country': dict(by_country),
        'countries_ready': len(ready_countries)
    })


@app.route('/api/countries')
def get_countries():
    """Get detailed country statistics with aggregated emotions"""
    # TEMPORARY FIX: If no analyzed posts ready, use raw posts data
    country_stats = db.get_all_country_stats()
    
    if not country_stats:
        # Fallback: Show countries with raw posts while analysis catches up
        logger.info("⚠️ No analyzed posts ready, using raw posts data as fallback")
        result = []
        
        # Get countries with raw posts
        cursor = db.get_connection().cursor()
        cursor.execute('''
            SELECT country, COUNT(*) as count 
            FROM raw_posts 
            GROUP BY country 
            HAVING COUNT(*) >= ?
            ORDER BY count DESC
        ''', (MIN_POSTS_PER_COUNTRY,))
        
        for row in cursor.fetchall():
            country = row[0]
            count = row[1]
            
            result.append({
                'country': country,
                'coords': get_coordinates(country),
                'total_posts': count,
                'dominant_emotion': 'neutral',  # Default until analyzed
                'emotion_distribution': {'neutral': count},
                'ready': True,
                'aggregation_confidence': 0.0,
                'aggregation_method': 'pending_analysis'
            })
        
        return jsonify(result)

    result = []
    for stat in country_stats:
        # Get aggregated emotion for each country
        country_emotion = db.get_country_aggregated_emotion(stat['country'])
        
        result.append({
            'country': stat['country'],
            'coords': get_coordinates(stat['country']),
            'total_posts': stat['total_posts'],
            'dominant_emotion': country_emotion['dominant_emotion'],  # From aggregation
            'emotion_distribution': stat['emotion_distribution'],
            'ready': stat['ready_for_display'],
            'aggregation_confidence': country_emotion['confidence'],
            'aggregation_method': country_emotion['method']
        })

    return jsonify(result)


@app.route('/api/country/<country>')
def get_country_details(country):
    """Get detailed analysis for a specific country with aggregated emotion (collective posts only)"""
    # Get ONLY collective posts (filter out personal issues)
    posts = db.get_posts_by_country(country, limit=1000, collective_only=True)
    collective_posts = db.get_collective_posts(country, min_cluster_size=PATTERN_DETECTION_THRESHOLD)
    patterns = detect_country_patterns(country)
    
    # Get aggregated country emotion using ML-powered algorithms
    country_emotion = db.get_country_aggregated_emotion(country)
    
    # NEW: Extract top topics/events from posts
    top_events = extract_top_events(posts, limit=5)

    return jsonify({
        'country': country,
        'total_posts': len(posts),
        'collective_posts': len(collective_posts),
        'patterns': len(patterns),
        'pattern_details': patterns,
        'emotion_distribution': db.get_country_emotion_distribution(country),
        'ready_for_display': len(posts) >= MIN_POSTS_PER_COUNTRY,
        # Aggregated country emotion
        'country_emotion': {
            'dominant_emotion': country_emotion['dominant_emotion'],
            'confidence': country_emotion['confidence'],
            'method': country_emotion['method'],
            'algorithm_votes': country_emotion['algorithm_votes'],
            'details': country_emotion['details']
        },
        # NEW: Top events/issues in this country
        'top_events': top_events
    })


@app.route('/api/progress')
def get_progress():
    """Get data collection progress for all countries"""
    progress = []

    for country in ALL_COUNTRIES:
        raw_count = db.get_raw_post_count(country)
        analyzed_count = db.get_country_post_count(country)
        progress.append({
            'country': country,
            'raw_posts': raw_count,
            'analyzed_posts': analyzed_count,
            'post_count': analyzed_count,  # For backward compatibility
            'progress_percent': min(100, (analyzed_count / MIN_POSTS_PER_COUNTRY) * 100),
            'ready': analyzed_count >= MIN_POSTS_PER_COUNTRY,
            'region': COUNTRY_TO_REGION.get(country.lower(), 'unknown')
        })

    progress.sort(key=lambda x: x['analyzed_posts'], reverse=True)

    return jsonify({
        'countries': progress,
        'total_countries': len(progress),
        'ready_countries': sum(1 for p in progress if p['ready']),
        'total_raw_posts': db.get_raw_post_count(),
        'total_analyzed_posts': sum(p['analyzed_posts'] for p in progress),
        'unanalyzed_queue': db.get_unanalyzed_count()
    })


@app.route('/api/posts/stream')
def stream_posts():
    """Server-Sent Events for real-time post updates"""
    def generate():
        while True:
            try:
                ready_countries = db.get_countries_ready_for_display(min_posts=MIN_POSTS_PER_COUNTRY)

                if ready_countries:
                    country = random.choice(ready_countries)
                    posts = db.get_collective_posts(country, min_cluster_size=PATTERN_DETECTION_THRESHOLD)

                    if posts:
                        post = random.choice(posts)
                        yield f"data: {json.dumps(post)}\n\n"

                time.sleep(30)

            except Exception as e:
                logger.error(f"Error in stream: {e}")
                time.sleep(10)

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/health')
def health():
    """Health check with system status"""
    total_posts = sum(db.get_country_post_count(c) for c in ALL_COUNTRIES)
    ready_countries = len(db.get_countries_ready_for_display(min_posts=MIN_POSTS_PER_COUNTRY))

    return jsonify({
        'status': 'healthy',
        'total_posts': total_posts,
        'countries_tracked': len(ALL_COUNTRIES),
        'countries_ready': ready_countries,
        'min_posts_required': MIN_POSTS_PER_COUNTRY,
        'data_source': 'Reddit (Real Data)'
    })


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🌍 Internet of Emotions Dashboard - Production Backend")
    logger.info("=" * 60)
    logger.info(f"📍 Min posts per country: {MIN_POSTS_PER_COUNTRY}")
    logger.info(f"📍 Max posts per country: {MAX_POSTS_PER_COUNTRY}")
    logger.info(f"🗺️  Tracking {len(ALL_COUNTRIES)} countries across {len(REGIONS)} regions")
    logger.info(f"🔄 Fast fetching + Independent ML analysis")
    logger.info("=" * 60)

    # Start FAST post fetching thread (just gets raw posts from Reddit)
    collection_thread = threading.Thread(
        target=thread_error_recovery(collect_posts_background, "Reddit Collection"),
        daemon=True
    )
    collection_thread.start()
    logger.info("✓ Fast Reddit fetching thread started")

    # Start INDEPENDENT ML analysis thread (processes raw posts)
    analysis_thread = threading.Thread(
        target=thread_error_recovery(analyze_posts_background, "ML Analysis"),
        daemon=True
    )
    analysis_thread.start()
    logger.info("✓ ML analysis thread started")

    logger.info("🚀 Starting Flask server on http://0.0.0.0:5000")
    logger.info("🤖 AI-powered emotion analysis active")
    logger.info("📊 Real data from Reddit being collected")
    logger.info("=" * 60)

    # Use Flask dev server by default
    # For production deployment, use: gunicorn --workers 4 --threads 2 --bind 0.0.0.0:5000 app:app
    if os.getenv('USE_GUNICORN') == 'true':
        logger.info("✅ Running in Gunicorn mode. Start with: gunicorn --workers 4 --threads 2 --bind 0.0.0.0:5000 app:app")
    else:
        logger.info("⚡ Running Flask development server (use USE_GUNICORN=true for production)")
        app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
