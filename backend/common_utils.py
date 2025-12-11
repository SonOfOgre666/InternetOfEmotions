"""
Common Utilities for Internet of Emotions Microservices

Reusable functions and classes used across multiple services.
"""

import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import pika
import json
from typing import Callable, Dict, Any
from functools import wraps
import time

from config import (
    DATABASE_URL, 
    RABBITMQ_URL, 
    RABBITMQ_EXCHANGE, 
    RABBITMQ_EXCHANGE_TYPE,
    LOG_FORMAT,
    LOG_LEVEL
)

# ============================================================================
# LOGGING
# ============================================================================

def setup_logger(service_name: str) -> logging.Logger:
    """
    Setup standardized logger for a service
    
    Args:
        service_name: Name of the service (e.g., 'post_fetcher')
    
    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=f'%(asctime)s - [{service_name.upper()}] - %(levelname)s - %(message)s'
    )
    return logging.getLogger(service_name)

# ============================================================================
# DATABASE
# ============================================================================

def get_db_connection():
    """
    Get PostgreSQL database connection with RealDictCursor
    
    Returns:
        psycopg2 connection object
    """
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def execute_query(query: str, params: tuple = None, fetch: bool = True) -> list:
    """
    Execute a database query with automatic connection handling
    
    Args:
        query: SQL query string
        params: Query parameters tuple
        fetch: Whether to fetch results
    
    Returns:
        List of results if fetch=True, else None
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if fetch:
                return cur.fetchall()
            conn.commit()
    finally:
        conn.close()

# ============================================================================
# MESSAGE QUEUE
# ============================================================================

class RabbitMQClient:
    """
    Standardized RabbitMQ client for pub/sub messaging
    
    Usage:
        mq = RabbitMQClient('my_service')
        mq.publish('post.fetched', {'id': 123})
        mq.consume(callback_function)
    """
    
    def __init__(self, queue_name: str):
        """
        Initialize RabbitMQ client
        
        Args:
            queue_name: Name for the consumer queue
        """
        self.queue_name = queue_name
        self.url = RABBITMQ_URL
        self.exchange = RABBITMQ_EXCHANGE
        self.connection = None
        self.channel = None
        self.connect()
    
    def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = pika.BlockingConnection(pika.URLParameters(self.url))
            self.channel = self.connection.channel()
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange=self.exchange,
                exchange_type=RABBITMQ_EXCHANGE_TYPE,
                durable=True
            )
            
            # Declare queue
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to RabbitMQ: {e}")
    
    def publish(self, routing_key: str, message: Dict[Any, Any]):
        """
        Publish a message to the exchange
        
        Args:
            routing_key: Routing key (e.g., 'post.fetched')
            message: Dictionary to publish as JSON
        """
        try:
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent
                    content_type='application/json'
                )
            )
        except Exception as e:
            # Reconnect and retry once
            self.connect()
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
    
    def bind_queue(self, routing_key: str):
        """
        Bind queue to exchange with routing key
        
        Args:
            routing_key: Routing pattern (e.g., 'post.*' or 'post.fetched')
        """
        self.channel.queue_bind(
            exchange=self.exchange,
            queue=self.queue_name,
            routing_key=routing_key
        )
    
    def consume(self, callback: Callable):
        """
        Start consuming messages
        
        Args:
            callback: Function to handle messages (ch, method, properties, body)
        """
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=callback,
            auto_ack=False
        )
        self.channel.start_consuming()
    
    def close(self):
        """Close connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()

# ============================================================================
# DECORATORS
# ============================================================================

def retry(max_attempts: int = 3, delay: float = 1.0):
    """
    Retry decorator for functions that may fail temporarily
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (attempt + 1))
            raise last_exception
        return wrapper
    return decorator

def measure_time(logger: logging.Logger):
    """
    Decorator to measure and log function execution time
    
    Args:
        logger: Logger instance to use
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start
            logger.info(f"{func.__name__} completed in {duration:.2f}s")
            return result
        return wrapper
    return decorator

# ============================================================================
# HEALTH CHECK
# ============================================================================

def create_health_response(service_name: str, extra_info: Dict = None) -> Dict:
    """
    Create standardized health check response
    
    Args:
        service_name: Name of the service
        extra_info: Additional info to include
    
    Returns:
        Health check dictionary
    """
    from datetime import datetime
    
    response = {
        'status': 'healthy',
        'service': service_name,
        'timestamp': datetime.now().isoformat(),
    }
    
    if extra_info:
        response.update(extra_info)
    
    return response
