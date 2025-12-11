"""
Database Cleanup Service
Microservice #4: Automatic removal of old posts

Features:
- Scheduled cleanup every 24 hours (configurable)
- Removes posts where reddit_created_at > 30 days
- Cascading deletes for related data
- Cleanup logs and metrics
- Manual trigger via API
"""

import os
import logging
import time
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from apscheduler.schedulers.background import BackgroundScheduler

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - [DB_CLEANUP] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 5004))
DATABASE_URL = os.getenv('DATABASE_URL')
CLEANUP_INTERVAL_HOURS = int(os.getenv('CLEANUP_INTERVAL_HOURS', 24))
MAX_POST_AGE_DAYS = int(os.getenv('MAX_POST_AGE_DAYS', 30))
CLEANUP_HOUR = int(os.getenv('CLEANUP_HOUR', 3))  # 3 AM

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# ============================================================================
# DATABASE
# ============================================================================

def get_db_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# ============================================================================
# CLEANUP LOGIC
# ============================================================================

def perform_cleanup() -> dict:
    """
    Remove posts older than MAX_POST_AGE_DAYS (based on reddit_created_at)
    Cascading deletes handle related tables (url_content, analyzed_posts)
    """
    logger.info(f"🧹 Starting cleanup: removing posts older than {MAX_POST_AGE_DAYS} days...")
    start_time = time.time()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cutoff_date = datetime.now() - timedelta(days=MAX_POST_AGE_DAYS)

        # Count posts to be removed
        cursor.execute("""
            SELECT COUNT(*) as count FROM raw_posts
            WHERE reddit_created_at < %s
        """, (cutoff_date,))
        posts_to_remove = cursor.fetchone()['count']

        if posts_to_remove == 0:
            logger.info("✓ No old posts to remove")
            duration = time.time() - start_time
            return {
                'status': 'success',
                'posts_removed': 0,
                'url_content_removed': 0,
                'analyzed_posts_removed': 0,
                'duration_seconds': round(duration, 2)
            }

        # Count related records (before deletion)
        cursor.execute("""
            SELECT COUNT(*) as count FROM url_content uc
            JOIN raw_posts rp ON uc.post_id = rp.id
            WHERE rp.reddit_created_at < %s
        """, (cutoff_date,))
        url_content_count = cursor.fetchone()['count']

        cursor.execute("""
            SELECT COUNT(*) as count FROM analyzed_posts ap
            JOIN raw_posts rp ON ap.post_id = rp.id
            WHERE rp.reddit_created_at < %s
        """, (cutoff_date,))
        analyzed_posts_count = cursor.fetchone()['count']

        # Delete old posts (cascade will handle related tables)
        cursor.execute("""
            DELETE FROM raw_posts
            WHERE reddit_created_at < %s
        """, (cutoff_date,))

        posts_removed = cursor.rowcount
        conn.commit()

        duration = time.time() - start_time

        # Log cleanup
        cursor.execute("""
            INSERT INTO cleanup_logs (
                cleanup_timestamp, posts_removed, url_content_removed,
                analyzed_posts_removed, duration_seconds, status
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            datetime.now(),
            posts_removed,
            url_content_count,
            analyzed_posts_count,
            duration,
            'success'
        ))
        conn.commit()

        logger.info(f"✓ Cleanup complete: removed {posts_removed} posts, "
                   f"{url_content_count} url_content, {analyzed_posts_count} analyzed_posts "
                   f"in {duration:.2f}s")

        return {
            'status': 'success',
            'posts_removed': posts_removed,
            'url_content_removed': url_content_count,
            'analyzed_posts_removed': analyzed_posts_count,
            'duration_seconds': round(duration, 2),
            'cutoff_date': cutoff_date.isoformat()
        }

    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Cleanup failed: {e}")

        # Log failure
        try:
            cursor.execute("""
                INSERT INTO cleanup_logs (cleanup_timestamp, status, error_message)
                VALUES (%s, %s, %s)
            """, (datetime.now(), 'failed', str(e)))
            conn.commit()
        except:
            pass

        return {
            'status': 'failed',
            'error': str(e)
        }
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# SCHEDULER
# ============================================================================

def scheduled_cleanup():
    """Scheduled cleanup job"""
    logger.info("⏰ Scheduled cleanup triggered")
    result = perform_cleanup()
    logger.info(f"Cleanup result: {result}")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(
    scheduled_cleanup,
    'cron',
    hour=CLEANUP_HOUR,
    minute=0,
    id='daily_cleanup'
)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'db_cleanup',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/cleanup/trigger', methods=['POST'])
def trigger_cleanup():
    """Manually trigger cleanup"""
    logger.info("📨 Manual cleanup triggered via API")
    result = perform_cleanup()
    return jsonify(result)

@app.route('/api/cleanup/status', methods=['GET'])
def cleanup_status():
    """Get last cleanup statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get last 10 cleanup logs
    cursor.execute("""
        SELECT * FROM cleanup_logs
        ORDER BY cleanup_timestamp DESC
        LIMIT 10
    """)
    logs = [dict(row) for row in cursor.fetchall()]

    # Get current old posts count
    cutoff_date = datetime.now() - timedelta(days=MAX_POST_AGE_DAYS)
    cursor.execute("""
        SELECT COUNT(*) as count FROM raw_posts
        WHERE reddit_created_at < %s
    """, (cutoff_date,))
    pending_cleanup = cursor.fetchone()['count']

    cursor.close()
    conn.close()

    return jsonify({
        'last_cleanup': logs[0] if logs else None,
        'recent_cleanups': logs,
        'pending_cleanup_count': pending_cleanup,
        'max_post_age_days': MAX_POST_AGE_DAYS
    })

@app.route('/api/cleanup/schedule', methods=['GET'])
def get_schedule():
    """Get cleanup schedule"""
    next_run = scheduler.get_job('daily_cleanup').next_run_time if scheduler.get_job('daily_cleanup') else None

    return jsonify({
        'interval_hours': CLEANUP_INTERVAL_HOURS,
        'cleanup_hour': CLEANUP_HOUR,
        'max_post_age_days': MAX_POST_AGE_DAYS,
        'next_run': next_run.isoformat() if next_run else None,
        'scheduler_running': scheduler.running
    })

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🧹 Database Cleanup Service")
    logger.info("=" * 60)
    logger.info(f"📅 Cleanup interval: Every {CLEANUP_INTERVAL_HOURS} hours")
    logger.info(f"⏰ Cleanup time: {CLEANUP_HOUR}:00")
    logger.info(f"📍 Max post age: {MAX_POST_AGE_DAYS} days")
    logger.info("=" * 60)

    # Start scheduler
    scheduler.start()
    logger.info("✓ Scheduler started")

    # Optionally run cleanup on startup
    # perform_cleanup()

    logger.info(f"🚀 Starting Flask server on port {SERVICE_PORT}")
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False, threaded=True)
