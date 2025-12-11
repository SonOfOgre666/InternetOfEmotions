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

import os
os.environ['TQDM_DISABLE'] = '1'  # Disable tqdm progress bars globally

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

# Configure logging FIRST
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Advanced features imports
try:
    from detoxify import Detoxify
    DETOXIFY_AVAILABLE = True
except ImportError:
    DETOXIFY_AVAILABLE = False
    logger.warning("⚠️  Detoxify not installed - safety filters disabled")

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logger.warning("⚠️  rank-bm25 not installed - hybrid search disabled")

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("⚠️  sentence-transformers/faiss not installed - semantic search disabled")

try:
    import pickle
    PICKLE_AVAILABLE = True
except ImportError:
    PICKLE_AVAILABLE = False

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
    "europe":     ["europe","InternationalNews" ,"world", "worldnews", "news", "breakingnews", "NewsAndPolitics", "GlobalNews", "UpliftingNews", "UnderReportedNews"],
    "asia":       ["asia", "InternationalNews" ,"world", "worldnews", "news", "breakingnews", "NewsAndPolitics", "GlobalNews", "UpliftingNews", "UnderReportedNews"],
    "africa":     ["africa", "InternationalNews" ,"world", "worldnews", "news", "breakingnews","NewsAndPolitics", "GlobalNews", "UpliftingNews", "UnderReportedNews"],
    "americas":   ["latinamerica", "InternationalNews" ,"world", "worldnews", "news", "breakingnews","NewsAndPolitics","GlobalNews", "UpliftingNews", "UnderReportedNews"],
    "oceania":    ["australia", "InternationalNews" ,"world", "worldnews", "news", "breakingnews","NewsAndPolitics","GlobalNews", "UpliftingNews", "UnderReportedNews"],
    "middleeast": ["middleeast", "InternationalNews" ,"world", "worldnews", "news", "breakingnews","NewsAndPolitics","GlobalNews", "UpliftingNews", "UnderReportedNews"],
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
# ADVANCED FEATURES: VECTOR SEARCH & HYBRID RETRIEVAL
# ============================================================================

# FAISS & Embedding Configuration
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'  # Lightweight, 384-dim
EMBED_DIM = 384
FAISS_INDEX_FILE = 'ioe_faiss.index'
BM25_INDEX_FILE = 'ioe_bm25.pkl'

# Initialize embedding model and FAISS index
embed_model = None
faiss_index = None
bm25_index = None
bm25_doc_ids = []
detoxify_model = None

if FAISS_AVAILABLE:
    try:
        logger.info("⏳ Loading embedding model...")
        embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        logger.info("✓ Embedding model loaded")

        # Load or create FAISS index
        if os.path.exists(FAISS_INDEX_FILE):
            logger.info(f"📂 Loading FAISS index from {FAISS_INDEX_FILE}...")
            faiss_index = faiss.read_index(FAISS_INDEX_FILE)
            logger.info(f"✓ FAISS index loaded ({faiss_index.ntotal} vectors)")
        else:
            logger.info("🆕 Creating new FAISS index...")
            faiss_index = faiss.IndexIDMap(faiss.IndexFlatIP(EMBED_DIM))
            logger.info("✓ FAISS index created")
    except Exception as e:
        logger.error(f"❌ FAISS initialization failed: {e}")
        FAISS_AVAILABLE = False

# Load BM25 index if available
if BM25_AVAILABLE and os.path.exists(BM25_INDEX_FILE):
    try:
        with open(BM25_INDEX_FILE, 'rb') as f:
            bm25_data = pickle.load(f)
            bm25_index = bm25_data['index']
            bm25_doc_ids = bm25_data['doc_ids']
        logger.info(f"✓ BM25 index loaded ({len(bm25_doc_ids)} documents)")
    except Exception as e:
        logger.warning(f"⚠️  BM25 index load failed: {e}")

# Load Detoxify model if available
if DETOXIFY_AVAILABLE:
    try:
        logger.info("⏳ Loading Detoxify toxicity model...")
        detoxify_model = Detoxify('original')
        # Test the model with a simple prediction to ensure it works
        test_result = detoxify_model.predict("This is a test message.")
        logger.info("✓ Detoxify model loaded and tested")
    except Exception as e:
        logger.warning(f"⚠️  Detoxify model load/test failed: {e}")
        DETOXIFY_AVAILABLE = False
        detoxify_model = None

# ============================================================================
# ADVANCED FEATURES: SAFETY & QUALITY
# ============================================================================

# PII Detection Patterns
import re
from typing import Tuple, Dict, Any

PII_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
}

def detect_pii(text: str) -> Dict[str, Any]:
    """Detect personally identifiable information (PII) in text"""
    found_pii = {}
    has_pii = False
    redacted_text = text

    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            found_pii[pii_type] = len(matches)
            has_pii = True
            # Redact with type label
            redacted_text = re.sub(pattern, f'[{pii_type.upper()}_REDACTED]', redacted_text)

    return {
        'has_pii': has_pii,
        'found_types': found_pii,
        'redacted_text': redacted_text
    }

def check_content_safety(text: str, threshold: float = 0.7) -> Dict[str, Any]:
    """Check content for toxicity using Detoxify"""
    global detoxify_model, DETOXIFY_AVAILABLE
    if not DETOXIFY_AVAILABLE or detoxify_model is None:
        return {'is_safe': True, 'scores': {}, 'warning': 'Detoxify not available'}

    try:
        scores = detoxify_model.predict(text)

        # Check if any toxicity score exceeds threshold
        is_safe = all(score < threshold for score in scores.values())

        return {
            'is_safe': is_safe,
            'scores': scores,
            'max_score': max(scores.values()) if scores else 0.0,
            'threshold': threshold
        }
    except Exception as e:
        logger.warning(f"⚠️  Toxicity check failed: {e}")
        # Disable detoxify if it keeps failing
        DETOXIFY_AVAILABLE = False
        detoxify_model = None
        return {'is_safe': True, 'scores': {}, 'error': str(e)}

def filter_unsafe_content(text: str, apply_pii_redaction: bool = True) -> Tuple[bool, str, Dict[str, Any]]:
    """Combined safety filter: toxicity + PII detection"""
    metadata = {'toxicity_check': {}, 'pii_check': {}}

    # Check toxicity
    toxicity_result = check_content_safety(text)
    metadata['toxicity_check'] = toxicity_result
    if not toxicity_result['is_safe']:
        logger.debug(f"🚫 Content failed toxicity check: max_score={toxicity_result.get('max_score', 0):.2f}")
        return False, text, metadata

    # Check PII
    pii_result = detect_pii(text)
    metadata['pii_check'] = pii_result

    # Return redacted text if PII found
    if apply_pii_redaction and pii_result['has_pii']:
        logger.debug(f"🔒 PII detected and redacted: {pii_result['found_types']}")
        return True, pii_result['redacted_text'], metadata

    return True, text, metadata

def extractive_quality_score(text: str) -> float:
    """
    Score content quality for news extraction (Reddit Answers Step 4.1)
    Based on objective signals: statistics, quotes, named entities, temporal markers
    """
    score = 0.0
    text_lower = text.lower()

    # Signal 1: Contains numbers/statistics (factual content)
    if re.search(r'\d+', text):
        score += 0.2
        # Extra credit for percentages or large numbers
        if re.search(r'\d+%|\d{2,}', text):
            score += 0.1

    # Signal 2: Contains quotes (direct evidence)
    if '"' in text or '"' in text or '"' in text:
        score += 0.15

    # Signal 3: Capitalized words (named entities: people, places, orgs)
    capitals = re.findall(r'\b[A-Z][a-z]+\b', text)
    if len(capitals) >= 2:
        score += 0.15

    # Signal 4: Temporal markers (newsworthy/recent events)
    temporal_markers = ['today', 'yesterday', 'recently', 'announced', 'reported',
                        'this week', 'this month', 'breaking', 'just', 'now']
    if any(marker in text_lower for marker in temporal_markers):
        score += 0.15

    # Signal 5: Length (substantive content)
    word_count = len(text.split())
    if 20 <= word_count <= 300:  # Sweet spot for quality content
        score += 0.1
    elif word_count > 300:
        score += 0.05  # Long is okay but not ideal

    # Penalties for low-quality signals
    opinion_markers = ['i think', 'i believe', 'in my opinion', 'imho', 'imo']
    if any(marker in text_lower for marker in opinion_markers):
        score -= 0.2

    # Penalty for excessive caps (shouting/spam)
    if sum(1 for c in text if c.isupper()) > len(text) * 0.3:
        score -= 0.15

    return max(0.0, min(1.0, score))  # Clamp to [0, 1]

def normalize_query(query: str) -> str:
    """Normalize search query by removing noise and standardizing format"""
    # Convert to lowercase
    query = query.lower().strip()

    # Remove special characters but keep spaces
    query = re.sub(r'[^\w\s-]', ' ', query)

    # Collapse multiple spaces
    query = re.sub(r'\s+', ' ', query)

    # Remove common stop words for better search
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
    words = [w for w in query.split() if w not in stop_words]

    return ' '.join(words)

def keyword_coverage_score(text: str, keywords: list) -> float:
    """Calculate how well text covers the given keywords"""
    if not keywords:
        return 0.0

    text_lower = text.lower()
    matches = sum(1 for kw in keywords if kw.lower() in text_lower)
    return matches / len(keywords)

# ============================================================================
# VECTOR SEARCH & HYBRID RETRIEVAL
# ============================================================================

def add_to_faiss_index(post_id: str, text: str) -> bool:
    """Add a post to the FAISS vector index"""
    if not FAISS_AVAILABLE or embed_model is None or faiss_index is None:
        return False

    try:
        # Generate embedding
        embedding = embed_model.encode([text], convert_to_numpy=True).astype('float32')
        faiss.normalize_L2(embedding)

        # Add to index with post ID as the vector ID
        vector_id = int(hash(post_id) & 0x7FFFFFFF)  # Positive int32
        faiss_index.add_with_ids(embedding, np.array([vector_id]))

        return True
    except Exception as e:
        logger.debug(f"Failed to add to FAISS: {e}")
        return False

def save_faiss_index():
    """Save FAISS index to disk"""
    if not FAISS_AVAILABLE or faiss_index is None:
        return False

    try:
        faiss.write_index(faiss_index, FAISS_INDEX_FILE)
        logger.info(f"✓ FAISS index saved ({faiss_index.ntotal} vectors)")
        return True
    except Exception as e:
        logger.error(f"Failed to save FAISS index: {e}")
        return False

def rebuild_bm25_index():
    """Rebuild BM25 index from all posts in database"""
    global bm25_index, bm25_doc_ids

    if not BM25_AVAILABLE:
        return False

    try:
        # Get all posts from database
        all_posts = []
        for country in ALL_COUNTRIES:
            country_posts = db.get_posts_by_country(country)
            all_posts.extend(country_posts)

        if not all_posts:
            logger.warning("No posts found to build BM25 index")
            return False

        # Tokenize all documents
        tokenized_docs = []
        bm25_doc_ids = []

        for post in all_posts:
            text = post.get('text', '')
            tokens = text.lower().split()
            tokenized_docs.append(tokens)
            bm25_doc_ids.append(post.get('id', ''))

        # Build BM25 index
        bm25_index = BM25Okapi(tokenized_docs)

        # Save to disk
        with open(BM25_INDEX_FILE, 'wb') as f:
            pickle.dump({'index': bm25_index, 'doc_ids': bm25_doc_ids}, f)

        logger.info(f"✓ BM25 index rebuilt ({len(bm25_doc_ids)} documents)")
        return True

    except Exception as e:
        logger.error(f"Failed to rebuild BM25 index: {e}")
        return False

def semantic_search(query: str, top_k: int = 20) -> list:
    """
    Semantic search using FAISS vector similarity
    Returns list of posts ranked by semantic relevance
    """
    if not FAISS_AVAILABLE or embed_model is None or faiss_index is None:
        return []

    try:
        # Encode query
        query_embedding = embed_model.encode([query], convert_to_numpy=True).astype('float32')
        faiss.normalize_L2(query_embedding)

        # Search FAISS index
        distances, indices = faiss_index.search(query_embedding, top_k)

        # Get post IDs from vector IDs
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1:  # Valid result
                results.append({
                    'vector_id': int(idx),
                    'similarity': float(dist)
                })

        return results

    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        return []

def hybrid_search(query: str, top_k: int = 50) -> list:
    """
    Hybrid search combining BM25 (sparse) + FAISS (dense) retrieval
    Returns list of post IDs with combined scores
    """
    if not (BM25_AVAILABLE and FAISS_AVAILABLE):
        # Fallback to semantic only
        return semantic_search(query, top_k)

    if bm25_index is None or embed_model is None or faiss_index is None:
        return []

    try:
        # BM25 search (sparse keyword matching)
        tokenized_query = query.lower().split()
        bm25_scores = bm25_index.get_scores(tokenized_query)

        # FAISS search (dense semantic)
        query_embedding = embed_model.encode([query], convert_to_numpy=True).astype('float32')
        faiss.normalize_L2(query_embedding)
        distances, indices = faiss_index.search(query_embedding, top_k)

        # Combine scores (50% BM25 + 50% FAISS)
        combined_scores = {}

        # Add BM25 scores
        for doc_id, score in zip(bm25_doc_ids, bm25_scores):
            combined_scores[doc_id] = {'bm25': score, 'faiss': 0.0}

        # Add FAISS scores
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1:
                # Find corresponding doc_id
                vector_id = int(idx)
                # Try to find matching doc_id (this is a simplified mapping)
                for doc_id in combined_scores.keys():
                    if int(hash(doc_id) & 0x7FFFFFFF) == vector_id:
                        combined_scores[doc_id]['faiss'] = float(dist)
                        break

        # Normalize and combine
        if combined_scores:
            bm25_values = [s['bm25'] for s in combined_scores.values()]
            faiss_values = [s['faiss'] for s in combined_scores.values()]

            bm25_min, bm25_max = min(bm25_values), max(bm25_values)
            faiss_min, faiss_max = min(faiss_values), max(faiss_values)

            results = []
            for doc_id, scores in combined_scores.items():
                # Normalize to [0, 1]
                norm_bm25 = (scores['bm25'] - bm25_min) / (bm25_max - bm25_min + 1e-10)
                norm_faiss = (scores['faiss'] - faiss_min) / (faiss_max - faiss_min + 1e-10)

                # Combine: 50% BM25 + 50% FAISS
                combined = 0.5 * norm_bm25 + 0.5 * norm_faiss

                results.append({
                    'post_id': doc_id,
                    'bm25_score': scores['bm25'],
                    'faiss_score': scores['faiss'],
                    'combined_score': combined
                })

            # Sort by combined score
            results.sort(key=lambda x: x['combined_score'], reverse=True)
            return results[:top_k]

        return []

    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        return []

def multi_signal_ranking(posts: list, query: str, keywords: list) -> list:
    """
    Multi-signal ranking (6 signals) inspired by Reddit Answers Beta:
    1. Semantic relevance (FAISS similarity)
    2. Keyword coverage
    3. Quality score
    4. Recency (temporal)
    5. Social signals (upvotes, comments)
    6. Trust signals (source quality)

    Signal weights: 25% semantic, 20% keyword, 25% quality, 15% recency, 10% social, 5% trust
    """
    if not posts:
        return []

    # Normalize query for keyword matching
    normalized_query = normalize_query(query)
    query_keywords = normalized_query.split() if not keywords else keywords

    scored_posts = []

    for post in posts:
        scores = {}
        text = post.get('text', '')

        # Signal 1: Semantic relevance (if FAISS available)
        scores['semantic'] = post.get('similarity', 0.5)  # From FAISS search

        # Signal 2: Keyword coverage
        scores['keyword'] = keyword_coverage_score(text, query_keywords)

        # Signal 3: Quality score
        scores['quality'] = post.get('quality_score', 0.5)

        # Signal 4: Recency (posts from last 7 days score higher)
        try:
            post_date = datetime.fromisoformat(post.get('timestamp', ''))
            age_days = (datetime.now() - post_date).days
            scores['recency'] = max(0, 1 - (age_days / 28))  # Decay over 28 days
        except:
            scores['recency'] = 0.5

        # Signal 5: Social signals (normalized upvotes + comments)
        upvotes = post.get('score', 0)
        comments = post.get('num_comments', 0)
        scores['social'] = min(1.0, (upvotes / 100 + comments / 50) / 2)

        # Signal 6: Trust (subreddit quality - simplified)
        trusted_subs = ['worldnews', 'news', 'InternationalNews', 'europe', 'asia']
        scores['trust'] = 1.0 if post.get('subreddit', '') in trusted_subs else 0.5

        # Weighted combination
        final_score = (
            0.25 * scores['semantic'] +
            0.20 * scores['keyword'] +
            0.25 * scores['quality'] +
            0.15 * scores['recency'] +
            0.10 * scores['social'] +
            0.05 * scores['trust']
        )

        post['multi_signal_score'] = round(final_score, 4)
        post['signal_breakdown'] = scores
        scored_posts.append(post)

    # Sort by multi-signal score
    scored_posts.sort(key=lambda x: x['multi_signal_score'], reverse=True)
    return scored_posts

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

                        # SAFETY FILTER: Check for toxicity and PII
                        is_safe, filtered_text, safety_metadata = filter_unsafe_content(text)
                        if not is_safe:
                            logger.debug(f"🚫 Filtered unsafe content from {country}")
                            continue

                        # QUALITY SCORE: Assess content quality
                        quality_score = extractive_quality_score(filtered_text)

                        post_age_days = (datetime.now().timestamp() - submission.created_utc) / 86400

                        posts.append({
                            'text': filtered_text,  # Use filtered text (PII redacted if needed)
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
                            'region': region,
                            'quality_score': round(quality_score, 3),  # Add quality metric
                            'safety_metadata': safety_metadata  # Store safety check results
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

        # Store only new posts AND add to FAISS index
        stored = 0
        duplicates = 0
        indexed = 0
        for post in new_posts:
            if db.add_raw_post(post):
                stored += 1
                # Add to FAISS index if available
                if add_to_faiss_index(post['id'], post['text']):
                    indexed += 1
            else:
                duplicates += 1

        # Periodically save FAISS index (every 100 new posts)
        if stored > 0 and FAISS_AVAILABLE and faiss_index and faiss_index.ntotal % 100 == 0:
            save_faiss_index()

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
                        'timestamp': post.get('timestamp', ''),
                        'quality_score': post.get('quality_score', 0.5)  # Include quality metric
                    })

    # Build topic list
    topic_scores = []
    for phrase, related_posts in topic_posts.items():
        if len(related_posts) >= 1:  # Even 1 post is a topic
            # Sort posts by QUALITY + engagement (hybrid ranking)
            related_posts.sort(key=lambda x: (x.get('quality_score', 0) * 0.6 + (x['score'] / 1000) * 0.4), reverse=True)

            # Calculate quality metrics
            avg_quality = sum(p.get('quality_score', 0.5) for p in related_posts) / len(related_posts)
            avg_engagement = sum(p['score'] for p in related_posts) / len(related_posts)

            # Clean phrase for display
            display_phrase = phrase.title()

            topic_scores.append({
                'topic': display_phrase,
                'count': len(related_posts),
                'avg_engagement': avg_engagement,
                'avg_quality': round(avg_quality, 3),  # New: quality metric
                'top_post': related_posts[0],  # Highest quality + engagement
                'sample_posts': related_posts[:3]
            })

    # Sort by: quality first, then count, then engagement
    topic_scores.sort(key=lambda x: (x['avg_quality'], x['count'], x['avg_engagement']), reverse=True)

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

@app.route('/api/deep_analysis/<country>')
def deep_analysis(country):
    """
    Deep analysis using LLM backend (port 8000)
    Bridges dashboard (fast) with LLM analysis (deep)
    """
    import requests

    try:
        # Query the LLM backend
        llm_url = f'http://localhost:8000/search?query={country}&days=30'
        response = requests.get(llm_url, timeout=120)  # 2 min timeout for LLM

        if response.status_code == 200:
            return jsonify({
                'status': 'success',
                'source': 'llm_backend',
                'data': response.json()
            })
        else:
            return jsonify({
                'status': 'error',
                'error': 'LLM backend unavailable',
                'fallback': f'http://localhost:8000/search?query={country}'
            }), 503
    except requests.exceptions.ConnectionError:
        return jsonify({
            'status': 'error',
            'error': 'LLM backend not running. Start it with: python app_local_llm_OPTIMIZED.py',
            'suggestion': 'Or use app_unified.py to run both backends together'
        }), 503
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/quality_analysis/<country>')
def quality_analysis(country):
    """
    Enhanced country analysis with quality scoring and safety filtering
    Shows only high-quality, verified-safe content
    """
    try:
        # Get posts from database
        all_posts = db.get_posts_by_country(country)

        if not all_posts:
            return jsonify({
                'status': 'no_data',
                'country': country,
                'message': f'No data available for {country}'
            })

        # Filter for high-quality posts (quality_score > 0.5)
        high_quality_posts = [
            post for post in all_posts
            if post.get('quality_score', 0) > 0.5
        ]

        # If no high-quality posts, use all posts
        posts_to_analyze = high_quality_posts if high_quality_posts else all_posts

        # Sort by quality score
        posts_to_analyze.sort(key=lambda x: x.get('quality_score', 0), reverse=True)

        # Extract topics with quality weighting
        top_topics = extract_top_events(posts_to_analyze, limit=5)

        return jsonify({
            'status': 'success',
            'country': country,
            'total_posts': len(all_posts),
            'high_quality_posts': len(high_quality_posts),
            'quality_threshold': 0.5,
            'top_topics': top_topics,
            'posts': posts_to_analyze[:10],  # Top 10 quality posts
            'quality_stats': {
                'avg_quality': sum(p.get('quality_score', 0) for p in posts_to_analyze) / len(posts_to_analyze) if posts_to_analyze else 0,
                'max_quality': max((p.get('quality_score', 0) for p in posts_to_analyze), default=0),
                'min_quality': min((p.get('quality_score', 0) for p in posts_to_analyze), default=0)
            }
        })

    except Exception as e:
        logger.error(f"Error in quality analysis for {country}: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/search')
def search_posts():
    """
    Advanced search with quality filtering and keyword matching
    Query params: q (query), min_quality (default 0.5), limit (default 20)
    """
    try:
        query = request.args.get('q', '').strip()
        min_quality = float(request.args.get('min_quality', 0.5))
        limit = int(request.args.get('limit', 20))

        if not query:
            return jsonify({
                'status': 'error',
                'error': 'Query parameter "q" is required'
            }), 400

        # Normalize query
        normalized_query = normalize_query(query)
        keywords = normalized_query.split()

        # Get all posts from database
        all_posts = []
        for country in ALL_COUNTRIES:
            country_posts = db.get_posts_by_country(country)
            all_posts.extend(country_posts)

        # Filter by quality and keyword relevance
        matching_posts = []
        for post in all_posts:
            quality = post.get('quality_score', 0)
            if quality < min_quality:
                continue

            # Check keyword coverage
            text = post.get('text', '')
            coverage = keyword_coverage_score(text, keywords)

            if coverage > 0:  # At least one keyword matches
                post['keyword_coverage'] = coverage
                post['relevance_score'] = (quality * 0.6 + coverage * 0.4)
                matching_posts.append(post)

        # Sort by relevance
        matching_posts.sort(key=lambda x: x['relevance_score'], reverse=True)

        return jsonify({
            'status': 'success',
            'query': query,
            'normalized_query': normalized_query,
            'keywords': keywords,
            'min_quality': min_quality,
            'total_matches': len(matching_posts),
            'results': matching_posts[:limit]
        })

    except Exception as e:
        logger.error(f"Error in search: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/semantic_search')
def semantic_search_endpoint():
    """
    Semantic search using FAISS vector similarity
    Query params: q (query), limit (default 20)
    """
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 20))

        if not query:
            return jsonify({
                'status': 'error',
                'error': 'Query parameter "q" is required'
            }), 400

        if not FAISS_AVAILABLE:
            return jsonify({
                'status': 'error',
                'error': 'Semantic search not available. Install: pip install sentence-transformers faiss-cpu'
            }), 503

        # Perform semantic search
        search_results = semantic_search(query, top_k=limit * 2)

        # Get actual posts from database
        matching_posts = []
        for result in search_results:
            # Find post by vector_id (this is simplified - in production use proper mapping)
            for country in ALL_COUNTRIES:
                posts = db.get_posts_by_country(country)
                for post in posts:
                    post_hash = int(hash(post.get('id', '')) & 0x7FFFFFFF)
                    if post_hash == result['vector_id']:
                        post['similarity'] = result['similarity']
                        matching_posts.append(post)
                        break
                if len(matching_posts) >= limit:
                    break

        return jsonify({
            'status': 'success',
            'query': query,
            'search_type': 'semantic',
            'total_matches': len(matching_posts),
            'results': matching_posts[:limit]
        })

    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/hybrid_search')
def hybrid_search_endpoint():
    """
    Hybrid search combining BM25 (sparse) + FAISS (dense)
    Query params: q (query), limit (default 20)
    """
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 20))

        if not query:
            return jsonify({
                'status': 'error',
                'error': 'Query parameter "q" is required'
            }), 400

        if not (BM25_AVAILABLE and FAISS_AVAILABLE):
            return jsonify({
                'status': 'error',
                'error': 'Hybrid search requires both BM25 and FAISS. Install: pip install rank-bm25 sentence-transformers faiss-cpu'
            }), 503

        # Perform hybrid search
        search_results = hybrid_search(query, top_k=limit)

        # Get actual posts from database
        matching_posts = []
        all_posts = []
        for country in ALL_COUNTRIES:
            all_posts.extend(db.get_posts_by_country(country))

        for result in search_results:
            post_id = result['post_id']
            for post in all_posts:
                if post.get('id') == post_id:
                    post['bm25_score'] = result['bm25_score']
                    post['faiss_score'] = result['faiss_score']
                    post['combined_score'] = result['combined_score']
                    matching_posts.append(post)
                    break

        return jsonify({
            'status': 'success',
            'query': query,
            'search_type': 'hybrid (BM25 + FAISS)',
            'total_matches': len(matching_posts),
            'results': matching_posts
        })

    except Exception as e:
        logger.error(f"Error in hybrid search: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/advanced_search')
def advanced_search_endpoint():
    """
    Advanced search with multi-signal ranking (6 signals)
    Query params: q (query), min_quality (default 0.5), limit (default 20)
    Uses Reddit Answers Beta-inspired ranking
    """
    try:
        query = request.args.get('q', '').strip()
        min_quality = float(request.args.get('min_quality', 0.5))
        limit = int(request.args.get('limit', 20))

        if not query:
            return jsonify({
                'status': 'error',
                'error': 'Query parameter "q" is required'
            }), 400

        # Normalize query
        normalized_query = normalize_query(query)
        keywords = normalized_query.split()

        # Get all posts from database
        all_posts = []
        for country in ALL_COUNTRIES:
            country_posts = db.get_posts_by_country(country)
            all_posts.extend(country_posts)

        # Filter by minimum quality
        quality_posts = [p for p in all_posts if p.get('quality_score', 0) >= min_quality]

        # Apply multi-signal ranking
        ranked_posts = multi_signal_ranking(quality_posts, query, keywords)

        return jsonify({
            'status': 'success',
            'query': query,
            'normalized_query': normalized_query,
            'keywords': keywords,
            'search_type': 'multi-signal (6 signals)',
            'signals': ['semantic', 'keyword', 'quality', 'recency', 'social', 'trust'],
            'signal_weights': {
                'semantic': 0.25,
                'keyword': 0.20,
                'quality': 0.25,
                'recency': 0.15,
                'social': 0.10,
                'trust': 0.05
            },
            'min_quality': min_quality,
            'total_candidates': len(quality_posts),
            'total_matches': len(ranked_posts),
            'results': ranked_posts[:limit]
        })

    except Exception as e:
        logger.error(f"Error in advanced search: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/rebuild_indexes')
def rebuild_indexes_endpoint():
    """
    Rebuild FAISS and BM25 indexes from scratch
    WARNING: This can take several minutes for large databases
    """
    try:
        results = {}

        # Rebuild BM25
        if BM25_AVAILABLE:
            bm25_success = rebuild_bm25_index()
            results['bm25'] = 'success' if bm25_success else 'failed'
        else:
            results['bm25'] = 'not available'

        # Rebuild FAISS
        if FAISS_AVAILABLE and faiss_index is not None:
            # Get all posts
            all_posts = []
            for country in ALL_COUNTRIES:
                all_posts.extend(db.get_posts_by_country(country))

            # Add all to FAISS
            added = 0
            for post in all_posts:
                if add_to_faiss_index(post.get('id', ''), post.get('text', '')):
                    added += 1

            # Save index
            save_faiss_index()
            results['faiss'] = f'success ({added} vectors added)'
        else:
            results['faiss'] = 'not available'

        return jsonify({
            'status': 'success',
            'indexes_rebuilt': results
        })

    except Exception as e:
        logger.error(f"Error rebuilding indexes: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# ============================================================================
# STARTUP
# ============================================================================
if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🌍 Internet of Emotions - ADVANCED OPTIMIZED Backend")
    logger.info("=" * 60)
    logger.info(f"📍 Max post age: {MAX_POST_AGE_DAYS} days (4 weeks)")
    logger.info(f"🔁 Circular rotation: ALL {len(ALL_COUNTRIES)} countries")
    logger.info(f"🚫 Duplicate prevention: ENABLED")
    logger.info(f"🧹 Auto cleanup: Every {CLEANUP_INTERVAL_HOURS} hour(s) (safety net)")
    logger.info("")
    logger.info("🔒 ADVANCED FEATURES:")
    logger.info(f"  • Safety Filters: {'ENABLED' if DETOXIFY_AVAILABLE else 'DISABLED (install detoxify)'}")
    logger.info(f"  • PII Detection: ENABLED")
    logger.info(f"  • Quality Scoring: ENABLED")
    logger.info(f"  • Keyword Search: ENABLED")
    logger.info(f"  • BM25 Search: {'ENABLED' if BM25_AVAILABLE and bm25_index else 'DISABLED'}")
    logger.info(f"  • FAISS Semantic Search: {'ENABLED' if FAISS_AVAILABLE and faiss_index else 'DISABLED'}")
    logger.info(f"  • Hybrid Search (BM25+FAISS): {'ENABLED' if (BM25_AVAILABLE and FAISS_AVAILABLE) else 'DISABLED'}")
    logger.info(f"  • Multi-Signal Ranking: ENABLED (6 signals)")
    logger.info(f"  • Progress Bars: SUPPRESSED (cleaner logs)")
    logger.info("")
    logger.info("📊 INDEX STATUS:")
    if FAISS_AVAILABLE and faiss_index:
        logger.info(f"  • FAISS vectors: {faiss_index.ntotal}")
    if BM25_AVAILABLE and bm25_index:
        logger.info(f"  • BM25 documents: {len(bm25_doc_ids)}")
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
