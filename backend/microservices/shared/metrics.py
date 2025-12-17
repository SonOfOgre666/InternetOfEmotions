"""
Shared Prometheus Metrics Module
Provides basic metrics for all microservices
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
import time


# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# Processing metrics
processing_time_seconds = Histogram(
    'processing_time_seconds',
    'Time spent processing tasks',
    ['task_type']
)

processing_errors_total = Counter(
    'processing_errors_total',
    'Total processing errors',
    ['task_type', 'error_type']
)

# Database metrics
database_queries_total = Counter(
    'database_queries_total',
    'Total database queries',
    ['operation']
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration',
    ['operation']
)

# Service health metrics
service_up = Gauge(
    'service_up',
    'Service health status (1=up, 0=down)'
)

# Circuit breaker metrics
circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half-open)',
    ['service']
)

circuit_breaker_failures_total = Counter(
    'circuit_breaker_failures_total',
    'Total circuit breaker failures',
    ['service']
)


def track_request_metrics(f):
    """Decorator to track HTTP request metrics"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        method = 'unknown'
        endpoint = f.__name__
        
        # Try to get request context
        try:
            from flask import request
            method = request.method
            endpoint = request.endpoint or f.__name__
        except (ImportError, RuntimeError):
            pass
        
        start_time = time.time()
        status = 500
        
        try:
            result = f(*args, **kwargs)
            
            # Extract status code from response
            if isinstance(result, tuple):
                status = result[1] if len(result) > 1 else 200
            else:
                status = 200
            
            return result
        except Exception as e:
            status = 500
            raise
        finally:
            duration = time.time() - start_time
            http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    
    return wrapper


def track_processing_time(task_type):
    """Decorator to track processing time"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = f(*args, **kwargs)
                return result
            except Exception as e:
                error_type = type(e).__name__
                processing_errors_total.labels(task_type=task_type, error_type=error_type).inc()
                raise
            finally:
                duration = time.time() - start_time
                processing_time_seconds.labels(task_type=task_type).observe(duration)
        
        return wrapper
    return decorator


def get_metrics():
    """Get current metrics in Prometheus format"""
    return generate_latest(), CONTENT_TYPE_LATEST


# Initialize service as up
service_up.set(1)
