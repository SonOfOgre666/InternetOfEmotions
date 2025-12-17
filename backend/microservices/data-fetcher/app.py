"""
Data Fetcher Microservice
Responsible for fetching posts from Reddit and storing them in database
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import praw
import logging
import os
import sys
import time
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from database import SharedDatabase
from models import Post
from config import (
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT,
    MAX_POST_AGE_DAYS, REGION_SUBREDDITS, COUNTRY_TO_REGION,
    ALL_COUNTRIES, DB_PATH, DATA_FETCH_WORKERS, REDDIT_FETCH_LIMIT,
    SUBREDDITS_BY_COUNTRY
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Ensure module is also available as 'app' (tests patch `app` directly)
import sys as _sys
if __name__ in _sys.modules:
    _sys.modules.setdefault('app', _sys.modules[__name__])

# Initialize database
db = SharedDatabase(DB_PATH)


class CircularRotation:
    """Manages circular rotation through ALL countries"""
    def __init__(self, countries=None):
        # Allow default invocation without params for tests
        if countries is None:
            from config import ALL_COUNTRIES as _all_countries
            countries = _all_countries
        self.countries = countries
        self.current_index = 0
        self.cycle_number = 0
        self.countries_per_batch = 30  # Optimized batch size for faster coverage
        self.lock = threading.Lock()

        logger.info(f"🔄 Circular rotation initialized: {len(countries)} countries")

    def get_next_batch(self):
        """Get next batch of countries in circular order"""
        with self.lock:
            batch = []
            for _ in range(self.countries_per_batch):
                batch.append(self.countries[self.current_index])
                self.current_index += 1

                if self.current_index >= len(self.countries):
                    self.current_index = 0
                    self.cycle_number += 1
                    logger.info(f"🔁 ✓ CYCLE {self.cycle_number} COMPLETE!")

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


# Initialize rotation and Reddit
circular_rotation = CircularRotation(ALL_COUNTRIES)
# Backwards compatible alias expected by tests
rotation = circular_rotation

logger.info("🔗 Initializing Reddit API connection...")
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)
logger.info("✓ Reddit API connected")


def get_country_region(country: str) -> str:
    """Get region for a country"""
    return COUNTRY_TO_REGION.get(country.lower(), "worldnews")


def search_regional_subreddits(country: str, limit: int = 50, reddit_instance=None) -> list:
    """
    Search Reddit for posts about a country.
    Only processes TEXT and LINK (blog/news) posts.
    Ignores: images, videos, galleries, social media.
    """
    posts = []
    seen_ids = set()

    date_threshold = datetime.now() - timedelta(days=MAX_POST_AGE_DAYS)
    date_threshold_timestamp = date_threshold.timestamp()

    # Combine country-specific and regional subreddits for comprehensive coverage
    country_lower = country.lower()
    all_subs = []
    
    # Add country-specific subreddits first (if available)
    if country_lower in SUBREDDITS_BY_COUNTRY:
        all_subs.extend(SUBREDDITS_BY_COUNTRY[country_lower])
    
    # Add regional subreddits for broader coverage
    region = get_country_region(country)
    regional_subs = REGION_SUBREDDITS.get(region, ["worldnews", "news"])
    # Add regional subs that aren't already in the list
    for sub in regional_subs:
        if sub not in all_subs:
            all_subs.append(sub)
    
    # Use all available subreddits
    subreddits = all_subs
    # Decide per-subreddit limit based on overall limit and configured fetch limit
    per_sub_limit = max(10, int(min(REDDIT_FETCH_LIMIT, limit) / max(1, len(subreddits))))

    try:
        for subreddit_name in subreddits:
            try:
                # If a reddit_instance is provided (per-thread), use it; otherwise fall back
                local_reddit = reddit_instance if reddit_instance is not None else reddit
                subreddit = local_reddit.subreddit(subreddit_name)
                
                # Add small delay to reduce rate limiting (429 errors)
                time.sleep(0.5)
                
                # For country-name subreddits (r/Morocco, r/france, r/portugal etc), 
                # fetch newest posts directly without keyword search
                if subreddit_name.lower() == country.lower().replace(' ', ''):
                    search_results = subreddit.new(limit=per_sub_limit)
                else:
                    # For other subreddits, search by country keyword
                    search_results = subreddit.search(
                        country,
                        limit=per_sub_limit,
                        time_filter='month',
                        sort='new'
                    )

                for submission in search_results:
                    if submission.created_utc < date_threshold_timestamp:
                        continue

                    if submission.id in seen_ids:
                        continue
                    seen_ids.add(submission.id)

                    # Classify post type and extract content
                    post_data = classify_and_extract_post(submission, country)
                    
                    if post_data:  # Only add if we got valid data
                        # Prioritize link posts (news) by inserting at front
                        if post_data.get('post_type') == 'link':
                            posts.insert(0, post_data)
                        else:
                            posts.append(post_data)

                        if len(posts) >= limit:
                            break

            except Exception as e:
                logger.warning(f"Error searching r/{subreddit_name}: {e}")
                continue

            if len(posts) >= limit:
                break

    except Exception as e:
        logger.error(f"Error fetching posts for {country}: {e}")

    return posts


def classify_and_extract_post(submission, country: str) -> dict:
    """
    Classify Reddit post type and extract appropriate content.
    Only processes TEXT and LINK (blog/news) posts.
    Ignores: images, videos, galleries, social media links, non-English content.
    
    Returns: Post dict or None if ignored
    """
    title = submission.title or ""
    selftext = submission.selftext or ""
    url = submission.url or ""
    
    # Accept ALL languages - translation will happen in content-extractor
    # No more filtering based on Latin characters
    
    # Early detection: if this is an external news/blog URL, return link immediately
    try:
        blog_domains_early = ['bbc.', 'cnn.', 'theguardian.', 'nytimes.', 'reuters.', 'aljazeera.',
                              'france24.', 'dw.', 'lemonde.', 'elpais.', 'folha.', 'globo.',
                              'timesofindia.', 'ndtv.', 'thehindu.', 'news.', 'blog.', 'medium.',
                              'bbc.com', 'cnn.com', 'bloomberg.', 'washingtonpost.']
        if url and any(domain in url.lower() for domain in blog_domains_early) and not submission.is_self:
            return {
                'text': title,
                'country': country,
                'timestamp': datetime.fromtimestamp(submission.created_utc).isoformat(),
                'post_id': submission.id,
                'post_type': 'link',
                'media_url': None,
                'link_url': url,
                'needs_extraction': 1,
                'source': getattr(submission, 'domain', None),
                'url': url,
                'author': getattr(submission.author, 'name', None) if hasattr(submission, 'author') else None,
                'score': getattr(submission, 'score', 0)
            }
    except Exception:
        pass
    
    # TEXT POST: Has selftext (Reddit self-post)
    if submission.is_self and selftext:
        # Check if text contains external blog links
        import re
        urls_in_text = re.findall(r'https?://[^\s]+', selftext)
        
        # Blog domains to extract
        blog_domains = ['bbc.', 'cnn.', 'theguardian.', 'nytimes.', 'reuters.', 'aljazeera.',
                       'france24.', 'dw.', 'lemonde.', 'elpais.', 'folha.', 'globo.',
                       'timesofindia.', 'ndtv.', 'thehindu.', 'news.', 'blog.', 'medium.',
                       'bbc.com', 'cnn.com', 'bloomberg.', 'washingtonpost.']
        
        for found_url in urls_in_text:
            if any(domain in found_url.lower() for domain in blog_domains):
                # Text post with blog link - extract the blog content
                logger.info(f"📰 Text with blog link: {found_url[:50]}")
                return {
                    'text': title,
                    'country': country,
                    'timestamp': datetime.fromtimestamp(submission.created_utc).isoformat(),
                    'post_id': submission.id,
                    'post_type': 'link',
                    'media_url': None,
                    'link_url': found_url,
                    'needs_extraction': 1,
                    'source': getattr(submission, 'domain', None),
                    'url': getattr(submission, 'url', None),
                    'author': getattr(submission.author, 'name', None) if hasattr(submission, 'author') else None,
                    'score': getattr(submission, 'score', 0)
                }
        
        # Pure text post
        combined_text = f"{title}. {selftext[:500]}".strip()
        return {
            'text': combined_text,
            'country': country,
            'timestamp': datetime.fromtimestamp(submission.created_utc).isoformat(),
            'post_id': submission.id,
            'post_type': 'text',
            'media_url': None,
            'link_url': None,
            'needs_extraction': 0,
            'source': getattr(submission, 'domain', None),
            'url': getattr(submission, 'url', None),
            'author': getattr(submission.author, 'name', None) if hasattr(submission, 'author') else None,
            'score': getattr(submission, 'score', 0)
        }
    
    # IGNORE: Image posts (even with text)
    if any(url.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
        # Image post - still return minimal metadata for tracking
        return {
            'text': title,
            'country': country,
            'timestamp': datetime.fromtimestamp(submission.created_utc).isoformat(),
            'post_id': submission.id,
            'post_type': 'image',
            'media_url': url,
            'link_url': None,
            'needs_extraction': 0,
            'source': getattr(submission, 'domain', None),
            'url': getattr(submission, 'url', None),
            'author': getattr(submission.author, 'name', None) if hasattr(submission, 'author') else None,
            'score': getattr(submission, 'score', 0)
        }
    
    # IGNORE: Video posts
    if 'v.redd.it' in url or any(url.endswith(ext) for ext in ['.mp4', '.webm', '.mov']):
        # Video post - track minimal metadata
        return {
            'text': title,
            'country': country,
            'timestamp': datetime.fromtimestamp(submission.created_utc).isoformat(),
            'post_id': submission.id,
            'post_type': 'video',
            'media_url': url,
            'link_url': None,
            'needs_extraction': 0,
            'source': getattr(submission, 'domain', None),
            'url': getattr(submission, 'url', None),
            'author': getattr(submission.author, 'name', None) if hasattr(submission, 'author') else None,
            'score': getattr(submission, 'score', 0)
        }
    
    # IGNORE: Gallery posts
    if hasattr(submission, 'is_gallery') and submission.is_gallery:
        return None
    
    # IGNORE: Social media links (require login, no value)
    social_media = ['twitter.com', 'x.com', 'facebook.com', 'instagram.com', 'tiktok.com',
                   'linkedin.com', 'reddit.com', 'youtube.com', 'youtu.be']
    if any(sm in url.lower() for sm in social_media):
        # Still insert metadata for tracking but mark as ignored for extraction
        return {
            'text': title,
            'country': country,
            'timestamp': datetime.fromtimestamp(submission.created_utc).isoformat(),
            'post_id': submission.id,
            'post_type': 'social',
            'media_url': None,
            'link_url': url,
            'needs_extraction': 0,
            'source': getattr(submission, 'domain', None),
            'url': getattr(submission, 'url', None),
            'author': getattr(submission.author, 'name', None) if hasattr(submission, 'author') else None,
            'score': getattr(submission, 'score', 0)
        }
    
    # LINK POST: External blog/news URL
    blog_domains = ['bbc.', 'cnn.', 'theguardian.', 'nytimes.', 'reuters.', 'aljazeera.',
                   'france24.', 'dw.', 'lemonde.', 'elpais.', 'folha.', 'globo.',
                   'timesofindia.', 'ndtv.', 'thehindu.', 'news.', 'blog.', 'medium.',
                   'bbc.com', 'cnn.com', 'bloomberg.', 'washingtonpost.']
    
    # If URL points to a blog domain, extract regardless of permalink
    if url:
        if any(domain in url.lower() for domain in blog_domains):
            logger.info(f"📰 Link post: {url[:50]}")
            return {
                'text': title,
                'country': country,
                'timestamp': datetime.fromtimestamp(submission.created_utc).isoformat(),
                'post_id': submission.id,
                'post_type': 'link',
                'media_url': None,
                'link_url': url,
                'needs_extraction': 1,
                'source': getattr(submission, 'domain', None),
                'url': getattr(submission, 'url', None),
                'author': getattr(submission.author, 'name', None) if hasattr(submission, 'author') else None,
                'score': getattr(submission, 'score', 0)
            }
    
    # FALLBACK: Skip everything else
    return None


def store_post(post_data: dict):
    """Store a post in the database"""
    try:
        db.execute_commit('''
            INSERT OR IGNORE INTO raw_posts 
            (id, text, country, timestamp, source, url, author, score, post_type, media_url, link_url, needs_extraction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            post_data['post_id'], post_data['text'], post_data['country'],
            post_data['timestamp'], post_data.get('source'),
            post_data.get('url'), post_data.get('author'), post_data.get('score', 0),
            post_data['post_type'], post_data.get('media_url'), 
            post_data.get('link_url'), post_data.get('needs_extraction', 0)
        ))
        return True
    except Exception as e:
        logger.error(f"Error storing post {post_data.get('post_id')}: {e}")
        return False


def store_raw_posts(posts):
    """Store posts in raw_posts table, preferring a bulk insert for performance"""
    try:
        stored = db.insert_raw_posts_bulk(posts)
        logger.info(f"Stored {stored} posts in bulk")
        return stored
    except Exception as e:
        logger.warning(f"Bulk insert failed, falling back to per-post insert: {e}")
        stored = 0
        for post_data in posts:
            if store_post(post_data):
                stored += 1
        return stored


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'data-fetcher',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/fetch', methods=['POST'])
def fetch_posts():
    """Fetch posts for specified countries"""
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON request'}), 400

    countries = data.get('countries')
    # Allow legacy single-country requests
    if not countries and 'country' in data:
        countries = [data.get('country')]

    if not countries:
        return jsonify({'error': 'No countries specified'}), 400

    results = {}
    for country in countries:
        try:
            limit = data.get('limit', 50)
            posts = search_regional_subreddits(country, limit)
            stored = store_raw_posts(posts)
        except Exception as e:
            logger.error(f"Error fetching/storing posts for {country}: {e}")
            return jsonify({'error': 'Internal Error'}), 500
        results[country] = {
            'fetched': len(posts),
            'stored': stored,
            'duplicates_skipped': len(posts) - stored
        }
    # Note: stored < fetched is normal (INSERT OR IGNORE skips duplicates)

    # For legacy single-country usage, return stored_count top-level
    if len(results) == 1:
        only_country = list(results.keys())[0]
        return jsonify({
            'country': only_country,
            'fetched_count': results[only_country]['fetched'],
            'stored_count': results[only_country]['stored']
        })

    return jsonify({'results': results})


@app.route('/fetch/country', methods=['POST'])
def fetch_country():
    """Fetch posts for a single country (legacy endpoint used in tests)"""
    data = request.get_json(silent=True)
    if not data or 'country' not in data:
        return jsonify({'error': 'No country specified'}), 400

    country = data.get('country')
    try:
        posts = search_regional_subreddits(country)
        stored = store_raw_posts(posts)
    except Exception as e:
        logger.error(f"Error fetching/storing for country {country}: {e}")
        return jsonify({'error': 'Internal Error'}), 500

    # Note: stored < fetched is normal (INSERT OR IGNORE skips duplicates)
    return jsonify({
        'country': country, 
        'fetched_count': len(posts), 
        'stored_count': stored,
        'duplicates_skipped': len(posts) - stored
    })


@app.route('/fetch/next-batch', methods=['POST'])
def fetch_next_batch():
    """Fetch posts for next batch of countries in rotation"""
    try:
        rb = rotation.get_next_batch()
        # Support older tests where rotation returns a list of posts directly
        if isinstance(rb, tuple) and len(rb) == 3:
            batch, cycle, index = rb
            is_country_batch = True
        elif isinstance(rb, list):
            batch = rb
            cycle, index = 0, 0
            is_country_batch = False
        else:
            return jsonify({'error': 'Rotation returned unexpected format'}), 500
    except Exception as e:
        logger.error(f"Rotation error: {e}")
        return jsonify({'error': 'Rotation error'}), 500

    results = {}
    all_posts = []
    if is_country_batch:
        # Parallel fetch per country
        workers = min(len(batch), DATA_FETCH_WORKERS)
        def _fetch_country(country):
            try:
                # Create a local Reddit instance for thread-safety
                local_reddit = praw.Reddit(
                    client_id=REDDIT_CLIENT_ID,
                    client_secret=REDDIT_CLIENT_SECRET,
                    user_agent=REDDIT_USER_AGENT
                )
                posts = search_regional_subreddits(country, limit=REDDIT_FETCH_LIMIT, reddit_instance=local_reddit)
                stored = store_raw_posts(posts)
                return country, len(posts), stored, posts
            except Exception as exc:
                logger.exception(f"Error in thread fetching {country}: {exc}")
                return country, 0, 0, []

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(_fetch_country, country): country for country in batch}
            for fut in as_completed(futures):
                country_name = futures[fut]
                try:
                    country, fetched, stored, posts = fut.result()
                    results[country] = {'fetched': fetched, 'stored': stored}
                    all_posts.extend(posts)
                except Exception as e:
                    logger.error(f"Failed fetching for {country_name}: {e}")
                    results[country_name] = {'fetched': 0, 'stored': 0}
    else:
        # rotation returned a list of posts directly
        all_posts = batch
        stored = store_raw_posts(all_posts)
        results = {'batch': {'fetched': len(all_posts), 'stored': stored}}

    # Note: stored < fetched is normal (INSERT OR IGNORE skips duplicates)

    return jsonify({
        'batch': batch,
        'cycle_number': cycle,
        'current_index': index,
        'results': results,
        'posts': all_posts
    })


@app.route('/stats', methods=['GET'])
def get_stats():
    """Get fetcher statistics"""
    rotation_stats = rotation.get_stats()
    
    # Get database stats
    try:
        total_raw = db.execute_query('SELECT COUNT(*) FROM raw_posts')[0][0]
        total_raw = int(total_raw) if total_raw is not None else 0
    except Exception:
        total_raw = 0
    
    # Merge rotation stats to top-level as tests mock rotation.get_stats()
    return jsonify({
        **rotation_stats,
        'total_raw_posts': total_raw
    })


@app.route('/cleanup', methods=['POST'])
def cleanup_old_posts():
    """Remove posts older than MAX_POST_AGE_DAYS based on Reddit post timestamp"""
    try:
        result = db.cleanup_old_posts(max_age_days=MAX_POST_AGE_DAYS)
        return jsonify({
            'status': 'success',
            'max_age_days': MAX_POST_AGE_DAYS,
            **result
        })
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
