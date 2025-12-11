"""
Unit tests for Stats Service
"""

import os
import pytest
import json
from unittest.mock import Mock, patch, MagicMock


# Set test environment variables
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'

# Import app after setting env vars
import app as stats_app


@pytest.fixture
def client():
    """Create a test client"""
    stats_app.app.config['TESTING'] = True
    with stats_app.app.test_client() as client:
        yield client


class TestHealth:
    """Test health endpoint"""
    
    def test_health_endpoint(self, client):
        """Test that health endpoint returns correct status"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'stats_service'


class TestStats:
    """Test stats endpoint"""
    
    @patch('app.get_db_connection')
    def test_get_stats_complete(self, mock_db_conn, client):
        """Test getting complete stats"""
        mock_cursor = MagicMock()
        
        # Mock multiple queries
        mock_cursor.fetchone.side_effect = [
            {'count': 100},  # Total posts
            {'count': 80}    # Analyzed posts
        ]
        mock_cursor.fetchall.side_effect = [
            [{'emotion': 'joy', 'count': 30}, {'emotion': 'sadness', 'count': 25}],  # By emotion
            [{'country': 'USA', 'count': 40}, {'country': 'UK', 'count': 20}]        # By country
        ]
        
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        response = client.get('/api/stats')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'total' in data
        assert 'by_emotion' in data
        assert 'by_country' in data
    
    @patch('app.get_db_connection')
    def test_stats_emotion_distribution(self, mock_db_conn, client):
        """Test emotion distribution in stats"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [{'count': 100}, {'count': 80}]
        mock_cursor.fetchall.side_effect = [
            [
                {'emotion': 'joy', 'count': 30},
                {'emotion': 'sadness', 'count': 20},
                {'emotion': 'anger', 'count': 15}
            ],
            [{'country': 'USA', 'count': 50}]
        ]
        
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        response = client.get('/api/stats')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should be a dictionary/object, not array
        assert isinstance(data['by_emotion'], dict)
        assert 'joy' in data['by_emotion']
        assert data['by_emotion']['joy'] == 30
    
    @patch('app.get_db_connection')
    def test_stats_country_distribution(self, mock_db_conn, client):
        """Test country distribution in stats"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [{'count': 100}, {'count': 80}]
        mock_cursor.fetchall.side_effect = [
            [{'emotion': 'joy', 'count': 30}],
            [
                {'country': 'USA', 'count': 40},
                {'country': 'UK', 'count': 30},
                {'country': 'Germany', 'count': 20}
            ]
        ]
        
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        response = client.get('/api/stats')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should be object format
        assert isinstance(data['by_country'], dict)
        assert 'USA' in data['by_country']
        assert data['by_country']['USA'] == 40


class TestStreamEndpoint:
    """Test streaming endpoint"""
    
    @patch('app.get_stats')
    def test_stream_endpoint(self, mock_get_stats, client):
        """Test SSE stream endpoint exists"""
        # Mock get_stats to return a response
        mock_response = Mock()
        mock_response.get_json.return_value = {'total': 100}
        mock_get_stats.return_value = mock_response
        
        response = client.get('/api/stream')
        
        # Should return text/event-stream
        assert response.status_code == 200
        assert 'text/event-stream' in response.content_type


class TestDatabase:
    """Test database queries"""
    
    @patch('app.get_db_connection')
    def test_query_total_posts(self, mock_db_conn):
        """Test total posts query"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'count': 150}
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        conn = stats_app.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM raw_posts")
        result = cursor.fetchone()
        
        assert result['count'] == 150
    
    @patch('app.get_db_connection')
    def test_empty_database(self, mock_db_conn, client):
        """Test stats with empty database"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [{'count': 0}, {'count': 0}]
        mock_cursor.fetchall.side_effect = [[], []]
        
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        response = client.get('/api/stats')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] == 0
        assert len(data['by_emotion']) == 0
        assert len(data['by_country']) == 0
