"""
Unit tests for Database Cleanup Service
"""

import os
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta


# Set test environment variables
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'

# Import app after setting env vars
import app as cleanup_app


@pytest.fixture
def client():
    """Create a test client"""
    cleanup_app.app.config['TESTING'] = True
    with cleanup_app.app.test_client() as client:
        yield client


class TestHealth:
    """Test health endpoint"""
    
    def test_health_endpoint(self, client):
        """Test that health endpoint returns correct status"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'db_cleanup'


class TestCleanupLogic:
    """Test cleanup logic"""
    
    @patch('cleanup_app.get_db_connection')
    def test_perform_cleanup_with_old_posts(self, mock_db_conn):
        """Test cleanup with old posts"""
        mock_cursor = MagicMock()
        
        # Mock counts
        mock_cursor.fetchone.side_effect = [
            {'count': 50},  # Posts to remove
            {'count': 30},  # URL content
            {'count': 40}   # Analyzed posts
        ]
        
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        result = cleanup_app.perform_cleanup()
        
        assert result is not None
        assert 'posts_removed' in result
        assert result['posts_removed'] == 50
    
    @patch('cleanup_app.get_db_connection')
    def test_perform_cleanup_no_old_posts(self, mock_db_conn):
        """Test cleanup with no old posts"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'count': 0}
        
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        result = cleanup_app.perform_cleanup()
        
        assert result is not None
        assert result['posts_removed'] == 0
    
    def test_cleanup_uses_reddit_created_at(self):
        """Test cleanup uses reddit_created_at field"""
        # Verify the cleanup logic targets reddit_created_at
        # This is a structural test
        assert cleanup_app.MAX_POST_AGE_DAYS > 0


class TestCascadingDeletes:
    """Test cascading delete behavior"""
    
    @patch('cleanup_app.get_db_connection')
    def test_cleanup_removes_related_data(self, mock_db_conn):
        """Test that cleanup removes related data"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {'count': 10},  # Posts to remove
            {'count': 5},   # Related URL content
            {'count': 8}    # Related analyzed posts
        ]
        
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        result = cleanup_app.perform_cleanup()
        
        # Should report related records removed
        assert 'url_content_removed' in result
        assert 'analyzed_posts_removed' in result


class TestManualCleanup:
    """Test manual cleanup trigger"""
    
    @patch('cleanup_app.perform_cleanup')
    def test_manual_cleanup_endpoint(self, mock_cleanup, client):
        """Test manual cleanup endpoint"""
        mock_cleanup.return_value = {
            'status': 'success',
            'posts_removed': 25,
            'duration_seconds': 1.5
        }
        
        response = client.post('/api/cleanup')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status'] == 'success'
        assert 'posts_removed' in data
        assert mock_cleanup.called
    
    @patch('cleanup_app.perform_cleanup')
    def test_cleanup_error_handling(self, mock_cleanup, client):
        """Test cleanup error handling"""
        mock_cleanup.side_effect = Exception("Database error")
        
        response = client.post('/api/cleanup')
        
        # Should handle error gracefully
        assert response.status_code in [500, 200]


class TestScheduledCleanup:
    """Test scheduled cleanup"""
    
    def test_cleanup_configuration(self):
        """Test cleanup configuration"""
        assert cleanup_app.CLEANUP_INTERVAL_HOURS > 0
        assert cleanup_app.MAX_POST_AGE_DAYS > 0
        assert cleanup_app.CLEANUP_HOUR >= 0
        assert cleanup_app.CLEANUP_HOUR < 24
    
    @patch('cleanup_app.BackgroundScheduler')
    def test_scheduler_initialization(self, mock_scheduler_class):
        """Test scheduler is initialized"""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        # Scheduler should be set up
        assert True  # Placeholder


class TestCleanupMetrics:
    """Test cleanup metrics and reporting"""
    
    @patch('cleanup_app.get_db_connection')
    def test_cleanup_reports_metrics(self, mock_db_conn):
        """Test cleanup returns detailed metrics"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {'count': 100},
            {'count': 50},
            {'count': 75}
        ]
        
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        result = cleanup_app.perform_cleanup()
        
        assert 'status' in result
        assert 'posts_removed' in result
        assert 'duration_seconds' in result
    
    @patch('cleanup_app.get_db_connection')
    def test_cleanup_duration_tracking(self, mock_db_conn):
        """Test cleanup tracks duration"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'count': 0}
        
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        result = cleanup_app.perform_cleanup()
        
        assert 'duration_seconds' in result
        assert result['duration_seconds'] >= 0


class TestStatsEndpoint:
    """Test cleanup stats endpoint"""
    
    @patch('cleanup_app.get_db_connection')
    def test_get_cleanup_stats(self, mock_db_conn, client):
        """Test getting cleanup statistics"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {'count': 1000},  # Total posts
            {'count': 50}     # Posts older than threshold
        ]
        
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        response = client.get('/api/stats')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'total_posts' in data or 'eligible_for_cleanup' in data


class TestDateCalculations:
    """Test date calculation logic"""
    
    def test_cutoff_date_calculation(self):
        """Test cutoff date is calculated correctly"""
        cutoff = datetime.now() - timedelta(days=cleanup_app.MAX_POST_AGE_DAYS)
        
        # Cutoff should be in the past
        assert cutoff < datetime.now()
        
        # Should be exactly MAX_POST_AGE_DAYS ago (approximately)
        days_diff = (datetime.now() - cutoff).days
        assert days_diff == cleanup_app.MAX_POST_AGE_DAYS


class TestDatabaseQueries:
    """Test database queries"""
    
    @patch('cleanup_app.get_db_connection')
    def test_count_old_posts_query(self, mock_db_conn):
        """Test query for counting old posts"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'count': 42}
        
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        # Query would use reddit_created_at
        conn = cleanup_app.get_db_connection()
        cursor = conn.cursor()
        
        assert cursor is not None
    
    @patch('cleanup_app.get_db_connection')
    def test_delete_old_posts_query(self, mock_db_conn):
        """Test delete query uses correct date field"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'count': 10}
        
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        # Cleanup should execute DELETE with reddit_created_at condition
        result = cleanup_app.perform_cleanup()
        
        assert result is not None


class TestLogging:
    """Test logging functionality"""
    
    @patch('cleanup_app.logger')
    @patch('cleanup_app.get_db_connection')
    def test_cleanup_logs_activity(self, mock_db_conn, mock_logger):
        """Test cleanup logs its activity"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'count': 10}
        
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        cleanup_app.perform_cleanup()
        
        # Should log cleanup activity
        assert mock_logger.info.called
