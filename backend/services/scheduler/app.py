"""
Smart Scheduler Service
Microservice for intelligent country prioritization and resource management

Responsibilities:
- Prioritizes countries based on data need, activity, and importance
- Manages adaptive fetch intervals
- Provides batch recommendations via API
- Tracks country metrics and success rates
- Publishes scheduling events to RabbitMQ
"""

import os
import sys
import time
import heapq
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import pika
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@postgres:5432/internet_of_emotions')
RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@rabbitmq:5672/')

# All countries to monitor
ALL_COUNTRIES = [
    'USA', 'UK', 'Canada', 'Australia', 'India', 'Germany', 'France', 'Japan',
    'Brazil', 'Mexico', 'Spain', 'Italy', 'Netherlands', 'Sweden', 'Norway',
    'Denmark', 'Finland', 'Poland', 'Russia', 'China', 'South Korea', 'Indonesia',
    'Philippines', 'Thailand', 'Vietnam', 'Malaysia', 'Singapore', 'Turkey',
    'Egypt', 'South Africa', 'Nigeria', 'Kenya', 'Argentina', 'Chile', 'Colombia',
    'Peru', 'Venezuela', 'New Zealand', 'Ireland', 'Switzerland', 'Austria',
    'Belgium', 'Greece', 'Portugal', 'Czech Republic', 'Hungary', 'Romania',
    'Ukraine', 'Israel', 'Saudi Arabia', 'UAE', 'Pakistan', 'Bangladesh'
]


class SmartScheduler:
    """
    Intelligent scheduler that prioritizes countries and manages fetch cycles
    """

    def __init__(self):
        self.all_countries = ALL_COUNTRIES

        # Track country metrics
        self.country_metrics = defaultdict(lambda: {
            'last_fetch': None,
            'post_rate': 0.0,
            'importance': 1.0,
            'success_rate': 1.0,
            'consecutive_failures': 0
        })

        # Adaptive timing
        self.min_interval = 30
        self.max_interval = 600
        self.current_interval = 120

        # Smart batching
        self.optimal_batch_size = 3
        self.max_batch_size = 10

        # Initialize priorities
        self._initialize_country_priorities()

    def _initialize_country_priorities(self):
        """Assign importance scores based on population and Reddit activity"""
        high_priority = {
            'usa': 10.0, 'india': 9.0, 'china': 8.0, 'brazil': 7.0,
            'uk': 9.0, 'canada': 8.0, 'australia': 7.0, 'germany': 7.0,
            'france': 6.0, 'japan': 6.0, 'south korea': 6.0, 'russia': 6.0,
            'mexico': 5.0, 'spain': 5.0, 'italy': 5.0, 'turkey': 5.0
        }

        medium_priority = {
            'poland': 4.0, 'netherlands': 4.0, 'sweden': 4.0, 'argentina': 4.0,
            'indonesia': 4.0, 'philippines': 4.0, 'thailand': 4.0,
            'south africa': 4.0, 'egypt': 4.0, 'nigeria': 4.0
        }

        for country in self.all_countries:
            country_lower = country.lower()
            if country_lower in high_priority:
                self.country_metrics[country]['importance'] = high_priority[country_lower]
            elif country_lower in medium_priority:
                self.country_metrics[country]['importance'] = medium_priority[country_lower]
            else:
                self.country_metrics[country]['importance'] = 2.0

        logger.info(f"✓ Initialized priorities for {len(self.all_countries)} countries")

    def calculate_priority_score(self, country: str, db_conn) -> float:
        """
        Calculate dynamic priority score for a country
        Higher score = should be fetched sooner
        """
        metrics = self.country_metrics[country]

        # 1. Data need (0-10 scale)
        raw_count = self._get_raw_post_count(country, db_conn)

        if raw_count < 20:
            data_need = 10.0
        elif raw_count < 50:
            data_need = 7.0
        elif raw_count < 100:
            data_need = 4.0
        else:
            data_need = 1.0

        # 2. Importance
        importance = metrics['importance']

        # 3. Success rate penalty
        success_penalty = metrics['success_rate']
        if metrics['consecutive_failures'] > 3:
            success_penalty *= 0.5

        # 4. Time decay
        time_decay = 1.0
        if metrics['last_fetch']:
            hours_since = (datetime.now() - metrics['last_fetch']).total_seconds() / 3600
            time_decay = min(hours_since / 24, 3.0)
        else:
            time_decay = 5.0

        # 5. Activity boost
        activity_boost = 1.0 + min(metrics['post_rate'] / 10, 2.0)

        # Combined score
        score = (data_need * 2.0 +
                importance * 1.5 +
                time_decay * 1.0) * success_penalty * activity_boost

        return score

    def get_next_batch(self, db_conn, batch_size: Optional[int] = None) -> List[str]:
        """Get next batch of countries to fetch"""
        priority_queue = []

        for country in self.all_countries:
            score = self.calculate_priority_score(country, db_conn)
            heapq.heappush(priority_queue, (-score, country))

        # Determine batch size
        if batch_size is None:
            high_priority_count = sum(1 for score, _ in priority_queue if -score > 15.0)

            if high_priority_count > 10:
                batch_size = self.max_batch_size
            elif high_priority_count > 5:
                batch_size = 6
            elif high_priority_count > 0:
                batch_size = self.optimal_batch_size
            else:
                batch_size = 2

        # Extract top N countries
        batch = []
        for _ in range(min(batch_size, len(priority_queue))):
            if priority_queue:
                score, country = heapq.heappop(priority_queue)
                batch.append(country)
                logger.debug(f"  {country}: priority={-score:.2f}")

        return batch

    def update_metrics(self, country: str, posts_fetched: int, error: bool = False):
        """Update country metrics after fetch attempt"""
        metrics = self.country_metrics[country]
        metrics['last_fetch'] = datetime.now()

        if error:
            metrics['consecutive_failures'] += 1
            metrics['success_rate'] *= 0.9
        else:
            if posts_fetched > 0:
                metrics['consecutive_failures'] = 0
                metrics['success_rate'] = min(metrics['success_rate'] * 1.1, 1.0)

                if metrics['last_fetch']:
                    hours = (datetime.now() - metrics['last_fetch']).total_seconds() / 3600
                    if hours > 0:
                        metrics['post_rate'] = posts_fetched / hours
            else:
                metrics['consecutive_failures'] += 1

    def get_stats(self, db_conn) -> Dict:
        """Get scheduler statistics"""
        priority_distribution = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}

        for country in self.all_countries:
            score = self.calculate_priority_score(country, db_conn)
            if score > 20:
                priority_distribution['critical'] += 1
            elif score > 10:
                priority_distribution['high'] += 1
            elif score > 5:
                priority_distribution['medium'] += 1
            else:
                priority_distribution['low'] += 1

        return {
            'total_countries': len(self.all_countries),
            'priority_distribution': priority_distribution,
            'current_interval': self.current_interval,
            'avg_success_rate': sum(m['success_rate'] for m in self.country_metrics.values()) / len(self.all_countries)
        }

    def _get_raw_post_count(self, country: str, db_conn) -> int:
        """Get count of raw posts for a country"""
        try:
            with db_conn.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM raw_posts WHERE LOWER(country) = LOWER(%s)",
                    (country,)
                )
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting raw post count: {e}")
            return 0


# Global scheduler instance
scheduler = SmartScheduler()


def get_db_connection():
    """Create database connection"""
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise


def publish_event(event_type: str, data: dict):
    """Publish event to RabbitMQ"""
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        channel.exchange_declare(exchange='posts_exchange', exchange_type='topic', durable=True)

        message = json.dumps(data)
        channel.basic_publish(
            exchange='posts_exchange',
            routing_key=f'scheduler.{event_type}',
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )

        connection.close()
        logger.info(f"Published event: scheduler.{event_type}")
    except Exception as e:
        logger.error(f"Error publishing event: {e}")


# API Endpoints

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'scheduler',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/batch/next', methods=['GET'])
def get_next_batch():
    """Get next batch of countries to fetch"""
    try:
        batch_size = request.args.get('size', type=int)
        
        db_conn = get_db_connection()
        batch = scheduler.get_next_batch(db_conn, batch_size)
        db_conn.close()

        # Publish event
        publish_event('batch.generated', {
            'countries': batch,
            'size': len(batch),
            'timestamp': datetime.now().isoformat()
        })

        return jsonify({
            'success': True,
            'batch': batch,
            'size': len(batch)
        })
    except Exception as e:
        logger.error(f"Error getting next batch: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/metrics/update', methods=['POST'])
def update_metrics():
    """Update metrics for a country after fetch"""
    try:
        data = request.json
        country = data.get('country')
        posts_fetched = data.get('posts_fetched', 0)
        error = data.get('error', False)

        if not country:
            return jsonify({'success': False, 'error': 'Country required'}), 400

        scheduler.update_metrics(country, posts_fetched, error)

        return jsonify({
            'success': True,
            'country': country,
            'metrics': dict(scheduler.country_metrics[country])
        })
    except Exception as e:
        logger.error(f"Error updating metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/stats', methods=['GET'])
def get_stats():
    """Get scheduler statistics"""
    try:
        db_conn = get_db_connection()
        stats = scheduler.get_stats(db_conn)
        db_conn.close()

        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/priorities', methods=['GET'])
def get_priorities():
    """Get priority scores for all countries"""
    try:
        db_conn = get_db_connection()
        
        priorities = {}
        for country in scheduler.all_countries:
            priorities[country] = {
                'score': scheduler.calculate_priority_score(country, db_conn),
                'metrics': dict(scheduler.country_metrics[country])
            }
        
        db_conn.close()

        # Sort by score
        sorted_priorities = dict(sorted(
            priorities.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        ))

        return jsonify({
            'success': True,
            'priorities': sorted_priorities
        })
    except Exception as e:
        logger.error(f"Error getting priorities: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("🚀 Starting Smart Scheduler Service")
    logger.info(f"Monitoring {len(ALL_COUNTRIES)} countries")
    app.run(host='0.0.0.0', port=5000, debug=False)
