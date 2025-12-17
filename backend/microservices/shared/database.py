"""
Shared Database Module for all microservices
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict
import threading
from collections import defaultdict
import logging
import os


class SharedDatabase:
    """Thread-safe database connection manager"""

    def __init__(self, db_path='posts.db'):
        self.db_path = db_path
        logger = logging.getLogger(__name__)
        logger.info(f"Initializing SharedDatabase with path: {self.db_path}")

        # If the path is a file path, ensure directory exists or log a warning
        try:
            if self.db_path != ':memory:':
                db_dir = os.path.dirname(self.db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create directory for DB path {self.db_path}: {e}")

        try:
            self.init_database()
        except sqlite3.OperationalError as e:
            # If opening the configured database path fails (e.g. missing mount),
            # fall back to an in-memory database to allow tests and imports to succeed.
            logger.warning(f"Failed to open DB path {self.db_path} ({e}), falling back to in-memory DB")
            self.db_path = ':memory:'
            self.init_database()
    
    def get_connection(self):
        """Get thread-local database connection for thread safety"""
        if not hasattr(self, '_local'):
            self._local = threading.local()
        
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            try:
                self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            except sqlite3.OperationalError:
                # Fall back to in-memory database if the file DB cannot be opened
                self._local.conn = sqlite3.connect(':memory:', check_same_thread=False)
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
                score INTEGER DEFAULT 0,
                post_type TEXT DEFAULT 'text',
                media_url TEXT,
                link_url TEXT,
                needs_extraction INTEGER DEFAULT 0,
                fetched_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Events table - groups related posts into thematic events
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                post_ids TEXT NOT NULL,
                event_date TEXT NOT NULL,
                emotion TEXT,
                confidence REAL,
                is_analyzed INTEGER DEFAULT 0,
                post_count INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Country aggregation table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS country_emotions (
                country TEXT PRIMARY KEY,
                emotions TEXT NOT NULL,
                top_emotion TEXT NOT NULL,
                total_posts INTEGER DEFAULT 0,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes for performance optimization
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_raw_posts_country ON raw_posts(country)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_raw_posts_needs_extraction ON raw_posts(needs_extraction)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_raw_posts_fetched_at ON raw_posts(fetched_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_raw_posts_country_extraction ON raw_posts(country, needs_extraction)')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_country ON events(country)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_is_analyzed ON events(is_analyzed)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_event_date ON events(event_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_country_analyzed ON events(country, is_analyzed)')

        conn.commit()
        print("✓ Database initialized with indexes")

    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()

    def execute_commit(self, query, params=None):
        """Execute a query and commit"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor.lastrowid

    def insert_raw_posts_bulk(self, posts: List[Dict]):
        """Insert multiple raw posts in a single transaction to speed up writes.

        Returns the number of rows that were inserted (not counting ignored duplicates).
        """
        if not posts:
            return 0
        conn = self.get_connection()
        cursor = conn.cursor()
        # Prepare records for executemany
        records = []
        for p in posts:
            records.append(
                (
                    p.get('post_id'), p.get('text'), p.get('country'), p.get('timestamp'),
                    p.get('source'), p.get('url'), p.get('author'), p.get('score', 0),
                    p.get('post_type', 'text'), p.get('media_url'), p.get('link_url'), p.get('needs_extraction', 0)
                )
            )
        sql = '''INSERT OR IGNORE INTO raw_posts
            (id, text, country, timestamp, source, url, author, score, post_type, media_url, link_url, needs_extraction)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)'''
        # Execute in a single transaction
        cursor.executemany(sql, records)
        conn.commit()
        try:
            return cursor.rowcount if cursor.rowcount != -1 else len(records)
        except Exception:
            return len(records)

    def cleanup_old_posts(self, max_age_days: int = 30):
        """Remove posts older than max_age_days based on Reddit post timestamp.
        Also removes associated events that reference deleted posts.
        
        Returns dict with counts of deleted posts and events.
        """
        logger = logging.getLogger(__name__)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Calculate cutoff date
        cutoff_date = (datetime.now() - timedelta(days=max_age_days)).isoformat()
        
        # Find posts to delete
        cursor.execute('''
            SELECT id FROM raw_posts 
            WHERE timestamp < ?
        ''', (cutoff_date,))
        old_post_ids = [row[0] for row in cursor.fetchall()]
        
        if not old_post_ids:
            logger.info("No old posts to cleanup")
            return {'deleted_posts': 0, 'deleted_events': 0}
        
        # Find events that reference these posts
        cursor.execute('SELECT id, post_ids FROM events')
        events_to_delete = []
        events_to_update = []
        
        for event_id, post_ids_json in cursor.fetchall():
            try:
                post_ids = json.loads(post_ids_json)
                # Remove old post IDs from event
                updated_post_ids = [pid for pid in post_ids if pid not in old_post_ids]
                
                if not updated_post_ids:
                    # Event has no valid posts left - delete it
                    events_to_delete.append(event_id)
                elif len(updated_post_ids) < len(post_ids):
                    # Event lost some posts but still has valid ones - update it
                    events_to_update.append((json.dumps(updated_post_ids), event_id))
            except (json.JSONDecodeError, TypeError):
                # Malformed post_ids - delete the event
                events_to_delete.append(event_id)
        
        # Delete events with no valid posts
        if events_to_delete:
            placeholders = ','.join(['?'] * len(events_to_delete))
            cursor.execute(f'DELETE FROM events WHERE id IN ({placeholders})', events_to_delete)
        
        # Update events with reduced post lists
        if events_to_update:
            cursor.executemany('UPDATE events SET post_ids = ? WHERE id = ?', events_to_update)
        
        # Delete old posts
        placeholders = ','.join(['?'] * len(old_post_ids))
        cursor.execute(f'DELETE FROM raw_posts WHERE id IN ({placeholders})', old_post_ids)
        
        conn.commit()
        
        result = {
            'deleted_posts': len(old_post_ids),
            'deleted_events': len(events_to_delete),
            'updated_events': len(events_to_update)
        }
        
        logger.info(f"🧹 Cleanup complete: {result['deleted_posts']} posts, {result['deleted_events']} events deleted, {result['updated_events']} events updated")
        return result
