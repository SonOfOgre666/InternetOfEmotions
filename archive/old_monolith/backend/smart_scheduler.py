"""
Smart Scheduler - Intelligent Resource Management
Maximizes efficiency with minimal resources through smart logic and prioritization
"""

import time
import heapq
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class SmartScheduler:
    """
    Intelligent scheduler that:
    1. Prioritizes high-value countries
    2. Adapts collection frequency based on activity
    3. Batches work efficiently
    4. Avoids redundant processing
    5. Manages resources dynamically
    """

    def __init__(self, db, all_countries):
        self.db = db
        self.all_countries = all_countries

        # Priority queue: (priority_score, country)
        self.priority_queue = []

        # Track country metrics
        self.country_metrics = defaultdict(lambda: {
            'last_fetch': None,
            'post_rate': 0.0,  # Posts per hour
            'importance': 1.0,  # Based on population, activity, etc.
            'success_rate': 1.0,
            'consecutive_failures': 0
        })

        # Adaptive timing
        self.min_interval = 30  # seconds
        self.max_interval = 600  # seconds
        self.current_interval = 120  # Start at 2 minutes

        # Smart batching
        self.optimal_batch_size = 3
        self.max_batch_size = 10

        # Initialize priorities
        self._initialize_country_priorities()

    def _initialize_country_priorities(self):
        """
        Assign importance scores based on:
        - Population (larger = more important)
        - Reddit activity (more active subs = higher priority)
        - Geographic region diversity
        """
        # High-priority countries (large population, high Reddit activity)
        high_priority = {
            'usa': 10.0, 'india': 9.0, 'china': 8.0, 'brazil': 7.0,
            'uk': 9.0, 'canada': 8.0, 'australia': 7.0, 'germany': 7.0,
            'france': 6.0, 'japan': 6.0, 'south korea': 6.0, 'russia': 6.0,
            'mexico': 5.0, 'spain': 5.0, 'italy': 5.0, 'turkey': 5.0
        }

        # Medium priority (moderate activity)
        medium_priority = {
            'poland': 4.0, 'netherlands': 4.0, 'sweden': 4.0, 'argentina': 4.0,
            'indonesia': 4.0, 'philippines': 4.0, 'thailand': 4.0,
            'south africa': 4.0, 'egypt': 4.0, 'nigeria': 4.0
        }

        # Default priority for all others
        for country in self.all_countries:
            country_lower = country.lower()

            if country_lower in high_priority:
                self.country_metrics[country]['importance'] = high_priority[country_lower]
            elif country_lower in medium_priority:
                self.country_metrics[country]['importance'] = medium_priority[country_lower]
            else:
                self.country_metrics[country]['importance'] = 2.0  # Low priority

        logger.info(f"✓ Initialized priorities for {len(self.all_countries)} countries")

    def calculate_priority_score(self, country: str) -> float:
        """
        Calculate dynamic priority score for a country
        Higher score = should be fetched sooner

        Score components:
        1. Data need (how empty is the database?)
        2. Importance (population, activity)
        3. Success rate (avoid wasting time on failing countries)
        4. Time since last fetch
        5. Post rate trend (active countries get more frequent updates)
        """
        metrics = self.country_metrics[country]

        # 1. Data need (0-10 scale)
        raw_count = self.db.get_raw_post_count(country)
        analyzed_count = self.db.get_country_post_count(country)

        if raw_count < 20:
            data_need = 10.0  # Critical need
        elif raw_count < 50:
            data_need = 7.0   # High need
        elif raw_count < 100:
            data_need = 4.0   # Medium need
        else:
            data_need = 1.0   # Low need

        # 2. Importance (pre-calculated)
        importance = metrics['importance']

        # 3. Success rate penalty
        success_penalty = metrics['success_rate']
        if metrics['consecutive_failures'] > 3:
            success_penalty *= 0.5  # Reduce priority for failing countries

        # 4. Time decay (longer since last fetch = higher priority)
        time_decay = 1.0
        if metrics['last_fetch']:
            hours_since = (datetime.now() - metrics['last_fetch']).total_seconds() / 3600
            time_decay = min(hours_since / 24, 3.0)  # Max 3x boost after 24 hours
        else:
            time_decay = 5.0  # Never fetched = very high priority

        # 5. Activity boost (trending countries)
        activity_boost = 1.0 + min(metrics['post_rate'] / 10, 2.0)

        # Combined score
        score = (data_need * 2.0 +  # Data need weighted highest
                importance * 1.5 +
                time_decay * 1.0) * success_penalty * activity_boost

        return score

    def get_next_batch(self) -> List[str]:
        """
        Get next batch of countries to fetch, intelligently sized and prioritized
        Returns: List of country names to fetch
        """
        # Rebuild priority queue
        self.priority_queue = []

        for country in self.all_countries:
            score = self.calculate_priority_score(country)
            # Negative score for max-heap behavior (highest priority first)
            heapq.heappush(self.priority_queue, (-score, country))

        # Determine optimal batch size based on queue state
        high_priority_count = sum(
            1 for score, _ in self.priority_queue
            if -score > 15.0  # High priority threshold
        )

        if high_priority_count > 10:
            batch_size = self.max_batch_size  # Many urgent countries
        elif high_priority_count > 5:
            batch_size = 6
        elif high_priority_count > 0:
            batch_size = self.optimal_batch_size
        else:
            batch_size = 2  # Just maintenance mode

        # Extract top N countries
        batch = []
        for _ in range(min(batch_size, len(self.priority_queue))):
            if self.priority_queue:
                score, country = heapq.heappop(self.priority_queue)
                batch.append(country)
                logger.debug(f"  {country}: priority={-score:.2f}")

        return batch

    def update_metrics(self, country: str, result: Dict):
        """
        Update country metrics after fetch attempt
        Learns from success/failure to adapt strategy
        """
        metrics = self.country_metrics[country]
        metrics['last_fetch'] = datetime.now()

        if result.get('error'):
            # Failure
            metrics['consecutive_failures'] += 1
            metrics['success_rate'] *= 0.9  # Decay success rate
        else:
            # Success
            posts_fetched = result.get('stored', 0)

            if posts_fetched > 0:
                metrics['consecutive_failures'] = 0
                metrics['success_rate'] = min(metrics['success_rate'] * 1.1, 1.0)

                # Update post rate
                if metrics['last_fetch']:
                    hours = (datetime.now() - metrics['last_fetch']).total_seconds() / 3600
                    if hours > 0:
                        metrics['post_rate'] = posts_fetched / hours
            else:
                # No posts found (not an error, but not useful)
                metrics['consecutive_failures'] += 1

        logger.debug(f"Updated metrics for {country}: {metrics}")

    def calculate_adaptive_interval(self) -> int:
        """
        Calculate next sleep interval based on system state
        More work pending = shorter interval
        Idle system = longer interval
        """
        # Count urgent countries
        urgent_count = sum(
            1 for country in self.all_countries
            if self.calculate_priority_score(country) > 15.0
        )

        # Count unanalyzed posts
        unanalyzed = self.db.get_unanalyzed_count()

        if urgent_count > 20 or unanalyzed > 200:
            # System overloaded - work faster
            interval = self.min_interval
        elif urgent_count > 10 or unanalyzed > 100:
            # Moderate load
            interval = 60
        elif urgent_count > 5 or unanalyzed > 50:
            # Light load
            interval = 120
        else:
            # Idle - slow down to conserve resources
            interval = self.max_interval

        self.current_interval = interval
        return interval

    def should_skip_cycle(self) -> bool:
        """
        Determine if we should skip this cycle entirely
        Smart logic: don't waste CPU if nothing to do
        """
        # Check if any country needs immediate attention
        max_priority = max(
            self.calculate_priority_score(country)
            for country in self.all_countries
        )

        # Skip if all countries are well-stocked
        if max_priority < 5.0:
            logger.info("⏸ All countries well-stocked, skipping cycle")
            return True

        return False

    def get_stats(self) -> Dict:
        """Get scheduler statistics"""
        total_countries = len(self.all_countries)

        priority_distribution = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }

        for country in self.all_countries:
            score = self.calculate_priority_score(country)
            if score > 20:
                priority_distribution['critical'] += 1
            elif score > 10:
                priority_distribution['high'] += 1
            elif score > 5:
                priority_distribution['medium'] += 1
            else:
                priority_distribution['low'] += 1

        return {
            'total_countries': total_countries,
            'priority_distribution': priority_distribution,
            'current_interval': self.current_interval,
            'avg_success_rate': sum(m['success_rate'] for m in self.country_metrics.values()) / total_countries
        }


class SmartMLProcessor:
    """
    Intelligent ML processing that:
    1. Loads models only when needed
    2. Batches efficiently
    3. Prioritizes high-value posts
    4. Caches results
    """

    def __init__(self):
        self.models_loaded = False
        self.models = None
        self.last_used = None
        self.idle_timeout = 600  # Unload after 10 minutes idle

        # Cache for recent results
        self.result_cache = {}
        self.cache_size = 1000

    def load_models_lazy(self):
        """Load ML models only when needed (lazy loading)"""
        if self.models_loaded:
            self.last_used = time.time()
            return

        logger.info("🤖 Loading ML models (on-demand)...")
        from emotion_analyzer import EmotionAnalyzer
        from collective_analyzer import CollectiveAnalyzer
        from cross_country_detector import CrossCountryDetector
        from multimodal_analyzer import MultimodalAnalyzer

        self.models = {
            'emotion': EmotionAnalyzer(),
            'collective': CollectiveAnalyzer(),
            'cross_country': CrossCountryDetector(),
            'multimodal': MultimodalAnalyzer()
        }

        self.models_loaded = True
        self.last_used = time.time()
        logger.info("✓ ML models loaded and ready")

    def unload_models_if_idle(self):
        """Unload models if idle for too long (save 4GB RAM)"""
        if not self.models_loaded:
            return

        idle_time = time.time() - self.last_used

        if idle_time > self.idle_timeout:
            logger.info(f"💤 Unloading idle ML models (idle for {idle_time/60:.1f} minutes)")
            self.models = None
            self.models_loaded = False
            import gc
            gc.collect()  # Force garbage collection
            logger.info("✓ ML models unloaded, RAM freed")

    def process_batch_smart(self, posts: List[Dict], db) -> int:
        """
        Process posts with smart batching and caching
        Returns: Number of posts successfully processed
        """
        if not posts:
            return 0

        # Load models on-demand
        self.load_models_lazy()

        processed_count = 0

        # Smart batching: Group similar posts for efficient processing
        posts_by_country = defaultdict(list)
        for post in posts:
            posts_by_country[post['country']].append(post)

        # Process country by country (better cache locality)
        for country, country_posts in posts_by_country.items():
            logger.info(f"🔬 Processing {len(country_posts)} posts for {country}")

            for post in country_posts:
                try:
                    # Check cache first
                    cache_key = f"{post['id']}:{post['text'][:50]}"

                    if cache_key in self.result_cache:
                        # Cache hit!
                        post_data = self.result_cache[cache_key]
                        logger.debug(f"✓ Cache hit for {post['id']}")
                    else:
                        # Cache miss - analyze
                        emotion_result = self.models['emotion'].analyze(post['text'])
                        collective_result = self.models['collective'].analyze_post(post['text'])
                        cross_country_result = self.models['cross_country'].detect_countries(post['text'])
                        cross_analysis = self.models['cross_country'].get_cross_country_analysis(
                            post['country'],
                            cross_country_result['countries']
                        )
                        media_analysis = self.models['multimodal'].analyze_reddit_media(post)

                        # Build result
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

                        # Cache result
                        if len(self.result_cache) < self.cache_size:
                            self.result_cache[cache_key] = post_data

                    # Store in database
                    if db.add_post(post_data):
                        db.mark_post_analyzed(post['id'])
                        processed_count += 1

                        # Handle cross-country posts
                        if post_data['is_cross_country'] and post_data['primary_subject_country']:
                            subject_country = post_data['primary_subject_country']
                            cross_post = post_data.copy()
                            cross_post['country'] = subject_country
                            cross_post['source_country'] = post['country']
                            cross_post['is_cross_country_reference'] = True
                            db.add_post(cross_post)

                except Exception as e:
                    logger.warning(f"Error processing post {post.get('id')}: {e}")
                    db.mark_post_analyzed(post['id'])
                    continue

        # Update last used time
        self.last_used = time.time()

        return processed_count


class SmartCacheManager:
    """
    Intelligent caching for expensive operations
    Caches country aggregations, stats, etc.
    """

    def __init__(self):
        self.cache = {}
        self.cache_times = {}
        self.cache_ttl = {
            'emotions': 30,          # 30 seconds (map data - refresh frequently)
            'country_emotion': 120,  # 2 minutes
            'country_stats': 60,     # 1 minute
            'global_stats': 30,      # 30 seconds
            'country_posts': 180     # 3 minutes
        }

    def get(self, cache_type: str, key: str):
        """Get cached value if still valid"""
        cache_key = f"{cache_type}:{key}"

        if cache_key not in self.cache:
            return None

        # Check if expired
        age = time.time() - self.cache_times[cache_key]
        ttl = self.cache_ttl.get(cache_type, 60)

        if age > ttl:
            # Expired
            del self.cache[cache_key]
            del self.cache_times[cache_key]
            return None

        logger.debug(f"✓ Cache hit: {cache_key} (age: {age:.1f}s)")
        return self.cache[cache_key]

    def set(self, cache_type: str, key: str, value):
        """Store value in cache"""
        cache_key = f"{cache_type}:{key}"
        self.cache[cache_key] = value
        self.cache_times[cache_key] = time.time()
        logger.debug(f"✓ Cached: {cache_key}")

    def clear_expired(self):
        """Clear all expired entries"""
        now = time.time()
        expired_keys = []

        for cache_key, cache_time in self.cache_times.items():
            cache_type = cache_key.split(':')[0]
            ttl = self.cache_ttl.get(cache_type, 60)

            if now - cache_time > ttl:
                expired_keys.append(cache_key)

        for key in expired_keys:
            del self.cache[key]
            del self.cache_times[key]

        if expired_keys:
            logger.debug(f"🧹 Cleared {len(expired_keys)} expired cache entries")

    def get_stats(self):
        """Get cache statistics"""
        return {
            'entries': len(self.cache),
            'types': len(set(k.split(':')[0] for k in self.cache.keys())),
            'oldest_entry_age': max(
                (time.time() - t for t in self.cache_times.values()),
                default=0
            )
        }
