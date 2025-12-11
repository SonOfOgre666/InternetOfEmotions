"""
Post Database - SQLite storage for accumulating posts
Integrates country-level emotion aggregation
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict
from collections import defaultdict
from country_emotion_aggregator import CountryEmotionAggregator


class PostDatabase:
    """Database for storing and managing posts"""

    def __init__(self, db_path='posts.db'):
        self.db_path = db_path
        self.aggregator = CountryEmotionAggregator()  # Initialize aggregator
        self.init_database()
    
    def get_connection(self):
        """Get thread-local database connection for thread safety"""
        import threading
        if not hasattr(self, '_local'):
            self._local = threading.local()
        
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            # Enable Write-Ahead Logging for concurrent reads/writes
            self._local.conn.execute('PRAGMA journal_mode=WAL')
            self._local.conn.execute('PRAGMA synchronous=NORMAL')
        
        return self._local.conn

    def init_database(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Raw posts table - fetched from Reddit but not yet analyzed
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS raw_posts (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                country TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                source TEXT,
                url TEXT,
                author TEXT,
                score INTEGER,
                num_comments INTEGER,
                subreddit TEXT,
                coords_lat REAL,
                coords_lon REAL,
                fetched_at TEXT NOT NULL,
                analyzed BOOLEAN DEFAULT 0
            )
        ''')

        # Analyzed posts table - after ML processing
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                country TEXT NOT NULL,
                emotion TEXT NOT NULL,
                confidence REAL,
                timestamp TEXT NOT NULL,
                source TEXT,
                url TEXT,
                author TEXT,
                score INTEGER,
                num_comments INTEGER,
                subreddit TEXT,
                coords_lat REAL,
                coords_lon REAL,
                is_collective BOOLEAN DEFAULT 0,
                cluster_id INTEGER,
                created_at TEXT NOT NULL
            )
        ''')

        # Country statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS country_stats (
                country TEXT PRIMARY KEY,
                total_posts INTEGER DEFAULT 0,
                last_updated TEXT,
                dominant_emotion TEXT,
                emotion_distribution TEXT,
                ready_for_display BOOLEAN DEFAULT 0
            )
        ''')

        # Post clusters table (for pattern detection)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clusters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country TEXT NOT NULL,
                topic TEXT,
                post_count INTEGER DEFAULT 0,
                keywords TEXT,
                created_at TEXT NOT NULL
            )
        ''')

        # Create indexes for posts
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_country ON posts(country)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON posts(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_collective ON posts(is_collective)')
        
        # Create indexes for raw_posts
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_raw_country ON raw_posts(country)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_raw_analyzed ON raw_posts(analyzed)')

        conn.commit()

    def add_post(self, post: Dict) -> bool:
        """Add a post to database"""
        try:
            cursor = self.get_connection().cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO posts (
                    id, text, country, emotion, confidence, timestamp,
                    source, url, author, score, num_comments, subreddit,
                    coords_lat, coords_lon, is_collective, cluster_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                post['id'],
                post['text'],
                post['country'],
                post['emotion'],
                post.get('confidence', 0.5),
                post['timestamp'],
                post.get('source', ''),
                post.get('url', ''),
                post.get('author', ''),
                post.get('score', 0),
                post.get('num_comments', 0),
                post.get('subreddit', ''),
                post['coords'][0] if 'coords' in post else 0,
                post['coords'][1] if 'coords' in post else 0,
                post.get('is_collective', False),
                post.get('cluster_id'),
                datetime.now().isoformat()
            ))

            self.get_connection().commit()
            self._update_country_stats(post['country'])
            return True

        except Exception as e:
            print(f"Error adding post: {e}")
            return False

    def add_raw_post(self, post: Dict) -> bool:
        """Add a raw post from Reddit (not yet analyzed)"""
        try:
            cursor = self.get_connection().cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO raw_posts (
                    id, text, country, timestamp, source, url, author,
                    score, num_comments, subreddit, coords_lat, coords_lon,
                    fetched_at, analyzed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                post['id'],
                post['text'],
                post['country'],
                post['timestamp'],
                post.get('source', ''),
                post.get('url', ''),
                post.get('author', ''),
                post.get('score', 0),
                post.get('num_comments', 0),
                post.get('subreddit', ''),
                post['coords'][0] if 'coords' in post else 0,
                post['coords'][1] if 'coords' in post else 0,
                datetime.now().isoformat(),
                False
            ))

            self.get_connection().commit()
            return True

        except Exception as e:
            print(f"Error adding raw post: {e}")
            return False

    def get_unanalyzed_posts(self, limit: int = 50) -> List[Dict]:
        """Get raw posts that haven't been analyzed yet"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            SELECT * FROM raw_posts
            WHERE analyzed = 0
            ORDER BY fetched_at ASC
            LIMIT ?
        ''', (limit,))

        posts = []
        for row in cursor.fetchall():
            posts.append({
                'id': row[0],
                'text': row[1],
                'country': row[2],
                'timestamp': row[3],
                'source': row[4],
                'url': row[5],
                'author': row[6],
                'score': row[7],
                'num_comments': row[8],
                'subreddit': row[9],
                'coords': (row[10], row[11])
            })

        return posts

    def mark_post_analyzed(self, post_id: str) -> bool:
        """Mark a raw post as analyzed"""
        try:
            cursor = self.get_connection().cursor()
            cursor.execute('UPDATE raw_posts SET analyzed = 1 WHERE id = ?', (post_id,))
            self.get_connection().commit()
            return True
        except Exception as e:
            print(f"Error marking post as analyzed: {e}")
            return False

    def get_raw_post_count(self, country: str = None) -> int:
        """Get number of raw posts (optionally for specific country)"""
        cursor = self.get_connection().cursor()
        if country:
            cursor.execute('SELECT COUNT(*) FROM raw_posts WHERE country = ?', (country,))
        else:
            cursor.execute('SELECT COUNT(*) FROM raw_posts')
        return cursor.fetchone()[0]

    def get_unanalyzed_count(self) -> int:
        """Get number of unanalyzed posts"""
        cursor = self.get_connection().cursor()
        cursor.execute('SELECT COUNT(*) FROM raw_posts WHERE analyzed = 0')
        return cursor.fetchone()[0]

    def get_posts_by_country(self, country: str, limit: int = 1000, collective_only: bool = True, max_age_days: int = None) -> List[Dict]:
        """
        Get posts for a country (filtered by is_collective flag to exclude personal posts)

        Args:
            country: Country name
            limit: Maximum number of posts to return
            collective_only: If True, only return collective posts (not personal)
            max_age_days: Maximum age of posts in days (None = no age filter, all posts)

        NOTE: Age filtering is now done during Reddit fetch, not during query.
        Posts in DB are already filtered, so we display all stored posts.
        """
        from datetime import datetime, timedelta

        cursor = self.get_connection().cursor()

        if collective_only:
            # Only return posts about country-level issues (filter out personal posts)
            # NO age filter - posts are already age-filtered during fetch
            if max_age_days is None:
                # No age filter - return all stored posts
                cursor.execute('''
                    SELECT * FROM posts
                    WHERE country = ?
                      AND is_collective = 1
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (country, limit))
            else:
                # Optional age filter (for backwards compatibility)
                cutoff_date = (datetime.now() - timedelta(days=max_age_days)).isoformat()
                cursor.execute('''
                    SELECT * FROM posts
                    WHERE country = ?
                      AND is_collective = 1
                      AND timestamp > ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (country, cutoff_date, limit))
        else:
            # Return all posts (including personal ones)
            if max_age_days is None:
                cursor.execute('''
                    SELECT * FROM posts
                    WHERE country = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (country, limit))
            else:
                cutoff_date = (datetime.now() - timedelta(days=max_age_days)).isoformat()
                cursor.execute('''
                    SELECT * FROM posts
                    WHERE country = ?
                      AND timestamp > ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (country, cutoff_date, limit))

        posts = []
        for row in cursor.fetchall():
            posts.append(self._row_to_post(row))

        return posts

    def get_country_post_count(self, country: str) -> int:
        """Get number of posts for a country"""
        cursor = self.get_connection().cursor()
        cursor.execute('SELECT COUNT(*) FROM posts WHERE country = ?', (country,))
        return cursor.fetchone()[0]

    def get_collective_posts(self, country: str, min_cluster_size: int = 5) -> List[Dict]:
        """Get posts identified as collective issues"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            SELECT * FROM posts
            WHERE country = ? AND is_collective = 1
            AND cluster_id IN (
                SELECT cluster_id FROM posts
                WHERE country = ? AND cluster_id IS NOT NULL
                GROUP BY cluster_id
                HAVING COUNT(*) >= ?
            )
            ORDER BY timestamp DESC
        ''', (country, country, min_cluster_size))

        posts = []
        for row in cursor.fetchall():
            posts.append(self._row_to_post(row))

        return posts

    def get_countries_ready_for_display(self, min_posts: int = 100) -> List[str]:
        """Get countries with enough posts to display"""
        cursor = self.get_connection().cursor()
        cursor.execute('''
            SELECT country FROM posts
            GROUP BY country
            HAVING COUNT(*) >= ?
        ''', (min_posts,))

        return [row[0] for row in cursor.fetchall()]

    def get_country_emotion_distribution(self, country: str, collective_only: bool = True, max_age_days: int = None) -> Dict[str, int]:
        """
        Get emotion distribution for a country (filtered by is_collective to exclude personal posts)

        Args:
            country: Country name
            collective_only: If True, only count collective posts
            max_age_days: Maximum age of posts in days (None = no age filter)

        NOTE: Age filtering is now done during Reddit fetch, not during query.
        """
        from datetime import datetime, timedelta

        cursor = self.get_connection().cursor()

        if collective_only:
            if max_age_days is None:
                # No age filter - use all stored posts
                cursor.execute('''
                    SELECT emotion, COUNT(*) as count
                    FROM posts
                    WHERE country = ?
                      AND is_collective = 1
                    GROUP BY emotion
                ''', (country,))
            else:
                # Optional age filter (backwards compatibility)
                cutoff_date = (datetime.now() - timedelta(days=max_age_days)).isoformat()
                cursor.execute('''
                    SELECT emotion, COUNT(*) as count
                    FROM posts
                    WHERE country = ?
                      AND is_collective = 1
                      AND timestamp > ?
                    GROUP BY emotion
                ''', (country, cutoff_date))
        else:
            if max_age_days is None:
                cursor.execute('''
                    SELECT emotion, COUNT(*) as count
                    FROM posts
                    WHERE country = ?
                    GROUP BY emotion
                ''', (country,))
            else:
                cutoff_date = (datetime.now() - timedelta(days=max_age_days)).isoformat()
                cursor.execute('''
                    SELECT emotion, COUNT(*) as count
                    FROM posts
                    WHERE country = ?
                      AND timestamp > ?
                    GROUP BY emotion
                ''', (country, cutoff_date))

        distribution = {}
        for row in cursor.fetchall():
            distribution[row[0]] = row[1]

        return distribution

    def cleanup_old_posts(self, days: int = 30, max_posts_per_country: int = 200):
        """
        Remove posts older than specified days AND enforce per-country limit
        Default: 30 days (keep last month only) + 200 posts max per country
        
        Args:
            days: Maximum age of posts in days
            max_posts_per_country: Maximum number of posts to keep per country (keeps newest)
        """
        from datetime import datetime, timedelta
        
        cursor = self.get_connection().cursor()
        total_deleted = 0
        
        # 1. Delete posts older than X days (time-based cleanup)
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('SELECT COUNT(*) FROM posts WHERE timestamp < ?', (cutoff_date,))
        old_posts_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM raw_posts WHERE timestamp < ?', (cutoff_date,))
        old_raw_count = cursor.fetchone()[0]
        
        if old_posts_count > 0 or old_raw_count > 0:
            print(f"🧹 Cleaning up old posts: {old_posts_count} analyzed, {old_raw_count} raw (older than {days} days)")
            
            cursor.execute('DELETE FROM posts WHERE timestamp < ?', (cutoff_date,))
            cursor.execute('DELETE FROM raw_posts WHERE timestamp < ?', (cutoff_date,))
            total_deleted += old_posts_count + old_raw_count
        
        # 2. Enforce per-country limit (keep only newest N posts per country)
        cursor.execute('SELECT DISTINCT country FROM posts')
        countries = [row[0] for row in cursor.fetchall()]
        
        country_cleanup_count = 0
        for country in countries:
            # Count posts for this country
            cursor.execute('SELECT COUNT(*) FROM posts WHERE country = ?', (country,))
            count = cursor.fetchone()[0]
            
            if count > max_posts_per_country:
                excess = count - max_posts_per_country
                
                # Delete oldest posts beyond the limit
                cursor.execute('''
                    DELETE FROM posts 
                    WHERE id IN (
                        SELECT id FROM posts 
                        WHERE country = ?
                        ORDER BY timestamp ASC
                        LIMIT ?
                    )
                ''', (country, excess))
                
                country_cleanup_count += excess
                print(f"  🗑️ {country}: Removed {excess} excess posts (kept newest {max_posts_per_country})")
        
        if country_cleanup_count > 0:
            total_deleted += country_cleanup_count
            print(f"✓ Per-country limit enforced: Removed {country_cleanup_count} excess posts")
        
        if total_deleted > 0:
            self.get_connection().commit()
            print(f"✓ Total cleanup: Removed {total_deleted} posts")
        
        return total_deleted
        return old_posts_count + old_raw_count

    def _update_country_stats(self, country: str):
        """Update country statistics"""
        post_count = self.get_country_post_count(country)
        emotion_dist = self.get_country_emotion_distribution(country)

        # Find dominant emotion
        dominant_emotion = max(emotion_dist.items(), key=lambda x: x[1])[0] if emotion_dist else 'neutral'

        cursor = self.get_connection().cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO country_stats (
                country, total_posts, last_updated, dominant_emotion,
                emotion_distribution, ready_for_display
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            country,
            post_count,
            datetime.now().isoformat(),
            dominant_emotion,
            json.dumps(emotion_dist),
            post_count >= 5  # Ready if >= 5 posts (matches MIN_POSTS_PER_COUNTRY)
        ))

        self.get_connection().commit()

    def get_all_country_stats(self) -> List[Dict]:
        """Get statistics for all countries"""
        cursor = self.get_connection().cursor()
        cursor.execute('SELECT * FROM country_stats WHERE ready_for_display = 1')

        stats = []
        for row in cursor.fetchall():
            stats.append({
                'country': row[0],
                'total_posts': row[1],
                'last_updated': row[2],
                'dominant_emotion': row[3],
                'emotion_distribution': json.loads(row[4]) if row[4] else {},
                'ready_for_display': bool(row[5])
            })

        return stats

    def get_country_aggregated_emotion(self, country: str, collective_only: bool = True) -> Dict:
        """
        Get aggregated emotion for a country using ML-powered algorithms
        Combines emotions from collective posts to determine ONE dominant emotion
        (Filters out personal posts to focus on country-level issues)
        """
        posts = self.get_posts_by_country(country, limit=10000, collective_only=collective_only)

        if not posts:
            return {
                'country': country,
                'dominant_emotion': 'neutral',
                'confidence': 0.0,
                'total_posts': 0,
                'method': 'empty'
            }

        # Use aggregation algorithms
        result = self.aggregator.aggregate_country_emotions(posts)

        return {
            'country': country,
            'dominant_emotion': result['dominant_emotion'],
            'confidence': result['confidence'],
            'total_posts': len(posts),
            'distribution': result['distribution'],
            'weighted_scores': result['weighted_scores'],
            'method': result['method'],
            'algorithm_votes': result['algorithm_votes'],
            'details': result['details']
        }

    def _row_to_post(self, row) -> Dict:
        """Convert database row to post dictionary"""
        return {
            'id': row[0],
            'text': row[1],
            'country': row[2],
            'emotion': row[3],
            'confidence': row[4],
            'timestamp': row[5],
            'source': row[6],
            'url': row[7],
            'author': row[8],
            'score': row[9],
            'num_comments': row[10],
            'subreddit': row[11],
            'coords': [row[12], row[13]],
            'is_collective': bool(row[14]),
            'cluster_id': row[15],
            'created_at': row[16] if len(row) > 16 else None  # Handle created_at field
        }

    def close(self):
        """Close database connection"""
        if self.conn:
            self.get_connection().close()


# Test
if __name__ == '__main__':
    db = PostDatabase('test_posts.db')

    # Test adding posts
    test_post = {
        'id': 'test123',
        'text': 'Test post about water scarcity',
        'country': 'USA',
        'emotion': 'sadness',
        'confidence': 0.8,
        'timestamp': datetime.now().isoformat(),
        'coords': [37.0902, -95.7129],
        'source': 'r/usa'
    }

    db.add_post(test_post)
    print(f"USA posts: {db.get_country_post_count('USA')}")
    print(f"Ready countries: {db.get_countries_ready_for_display(min_posts=1)}")

    db.close()
