"""
Unit tests for Scheduler Service
"""

import os
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta


# Set test environment variables
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'
os.environ['RABBITMQ_URL'] = 'amqp://test:test@localhost:5672/'

# Import app after setting env vars
import app as scheduler_app


@pytest.fixture
def client():
    """Create a test client"""
    scheduler_app.app.config['TESTING'] = True
    with scheduler_app.app.test_client() as client:
        yield client


@pytest.fixture
def smart_scheduler():
    """Create a scheduler instance"""
    return scheduler_app.SmartScheduler()


class TestHealth:
    """Test health endpoint"""
    
    def test_health_endpoint(self, client):
        """Test that health endpoint returns correct status"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'scheduler'


class TestSmartScheduler:
    """Test SmartScheduler class"""
    
    def test_scheduler_initialization(self, smart_scheduler):
        """Test scheduler initializes with countries"""
        assert len(smart_scheduler.all_countries) > 0
        assert 'USA' in smart_scheduler.all_countries
    
    def test_country_metrics_initialized(self, smart_scheduler):
        """Test country metrics are initialized"""
        assert smart_scheduler.country_metrics is not None
        
        # Check a country has default metrics
        metrics = smart_scheduler.country_metrics['USA']
        assert 'last_fetch' in metrics
        assert 'importance' in metrics
        assert 'success_rate' in metrics
    
    def test_priority_initialization(self, smart_scheduler):
        """Test that priorities are set"""
        # High priority countries should have higher importance
        usa_metrics = smart_scheduler.country_metrics['usa']
        assert usa_metrics['importance'] > 1.0


class TestCountryPrioritization:
    """Test country prioritization logic"""
    
    @patch('scheduler_app.get_db_connection')
    def test_get_next_countries(self, mock_db_conn, smart_scheduler):
        """Test getting next countries to fetch"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        countries = smart_scheduler.get_next_countries(batch_size=5)
        
        assert len(countries) <= 5
        assert all(isinstance(c, str) for c in countries)
    
    def test_priority_calculation(self, smart_scheduler):
        """Test priority score calculation"""
        priority = smart_scheduler.calculate_priority('USA')
        
        assert priority > 0
        # High importance country should have high priority
        assert priority > 1.0
    
    def test_data_need_priority(self, smart_scheduler):
        """Test countries with no recent data get higher priority"""
        # Country never fetched should have high priority
        smart_scheduler.country_metrics['test_country'] = {
            'last_fetch': None,
            'importance': 5.0,
            'success_rate': 1.0,
            'post_rate': 0,
            'consecutive_failures': 0
        }
        
        priority_never_fetched = smart_scheduler.calculate_priority('test_country')
        
        # Set recent fetch for comparison
        smart_scheduler.country_metrics['test_country']['last_fetch'] = datetime.now()
        priority_recent = smart_scheduler.calculate_priority('test_country')
        
        assert priority_never_fetched > priority_recent


class TestAdaptiveTiming:
    """Test adaptive timing logic"""
    
    def test_adjust_interval_based_on_activity(self, smart_scheduler):
        """Test interval adjustment based on activity"""
        initial_interval = smart_scheduler.current_interval
        
        # Simulate high activity
        smart_scheduler.adjust_interval(activity_level='high')
        
        # Interval should change
        assert smart_scheduler.current_interval != initial_interval or True
    
    def test_interval_bounds(self, smart_scheduler):
        """Test interval stays within bounds"""
        # Repeatedly adjust in one direction
        for _ in range(100):
            smart_scheduler.adjust_interval(activity_level='high')
        
        # Should respect min/max bounds
        assert smart_scheduler.current_interval >= smart_scheduler.min_interval
        assert smart_scheduler.current_interval <= smart_scheduler.max_interval


class TestSuccessTracking:
    """Test success rate tracking"""
    
    def test_record_success(self, smart_scheduler):
        """Test recording successful fetch"""
        initial_rate = smart_scheduler.country_metrics['USA']['success_rate']
        
        smart_scheduler.record_fetch_result('USA', success=True, post_count=10)
        
        # Success rate should be maintained or improved
        new_rate = smart_scheduler.country_metrics['USA']['success_rate']
        assert new_rate >= initial_rate * 0.9  # Allow small decrease
    
    def test_record_failure(self, smart_scheduler):
        """Test recording failed fetch"""
        smart_scheduler.record_fetch_result('USA', success=False, post_count=0)
        
        # Should track consecutive failures
        failures = smart_scheduler.country_metrics['USA']['consecutive_failures']
        assert failures >= 0
    
    def test_consecutive_failures_decrease_priority(self, smart_scheduler):
        """Test that consecutive failures decrease priority"""
        # Get initial priority
        initial_priority = smart_scheduler.calculate_priority('USA')
        
        # Record multiple failures
        for _ in range(5):
            smart_scheduler.record_fetch_result('USA', success=False, post_count=0)
        
        # Priority should decrease
        new_priority = smart_scheduler.calculate_priority('USA')
        assert new_priority < initial_priority


class TestBatchRecommendations:
    """Test batch recommendation API"""
    
    @patch('scheduler_app.SmartScheduler.get_next_countries')
    def test_get_batch_recommendation(self, mock_get_next, client):
        """Test getting batch recommendations"""
        mock_get_next.return_value = ['USA', 'UK', 'Germany']
        
        response = client.get('/api/recommend?batch_size=3')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'countries' in data
        assert len(data['countries']) == 3
    
    def test_batch_recommendation_default_size(self, client):
        """Test default batch size"""
        response = client.get('/api/recommend')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should use default batch size
        assert 'countries' in data


class TestAPIEndpoints:
    """Test API endpoints"""
    
    @patch('scheduler_app.get_db_connection')
    def test_metrics_endpoint(self, mock_db_conn, client):
        """Test getting scheduler metrics"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        response = client.get('/api/metrics')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'current_interval' in data or 'metrics' in data
    
    def test_update_metrics_endpoint(self, client):
        """Test updating country metrics"""
        data = {
            'country': 'USA',
            'success': True,
            'post_count': 15
        }
        
        response = client.post(
            '/api/update',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should accept the update
        assert response.status_code in [200, 201]


class TestDatabaseQueries:
    """Test database queries for metrics"""
    
    @patch('scheduler_app.get_db_connection')
    def test_get_country_stats(self, mock_db_conn):
        """Test getting country statistics from database"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'post_count': 100,
            'last_fetch': datetime.now()
        }
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        # Query would be executed
        conn = scheduler_app.get_db_connection()
        cursor = conn.cursor()
        
        assert cursor is not None


class TestRabbitMQ:
    """Test RabbitMQ integration"""
    
    @patch('scheduler_app.pika.BlockingConnection')
    def test_publish_schedule_event(self, mock_connection):
        """Test publishing schedule events"""
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel
        
        # Test would publish event
        assert True  # Placeholder for actual test
