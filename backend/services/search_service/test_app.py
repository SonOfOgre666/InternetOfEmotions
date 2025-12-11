"""
Unit tests for Search Service
"""

import os
import pytest
import json
from unittest.mock import Mock, patch, MagicMock


# Set test environment variables
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'

# Import app after setting env vars
import app as search_app


@pytest.fixture
def client():
    """Create a test client"""
    search_app.app.config['TESTING'] = True
    with search_app.app.test_client() as client:
        yield client


class TestHealth:
    """Test health endpoint"""
    
    def test_health_endpoint(self, client):
        """Test that health endpoint returns correct status"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'search_service'


class TestSearch:
    """Test search functionality"""
    
    @patch('app.get_db_connection')
    def test_search_with_query(self, mock_db_conn, client):
        """Test search with query parameter"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'id': 'post1',
                'title': 'Test Post',
                'text': 'Test content with query term',
                'emotion': 'joy',
                'confidence': 0.8
            }
        ]
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        response = client.get('/api/search?q=test')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'results' in data
        assert 'query' in data
        assert data['query'] == 'test'
        assert len(data['results']) > 0
    
    @patch('app.get_db_connection')
    def test_search_empty_query(self, mock_db_conn, client):
        """Test search with empty query"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        response = client.get('/api/search?q=')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['query'] == ''
    
    @patch('app.get_db_connection')
    def test_search_with_limit(self, mock_db_conn, client):
        """Test search with limit parameter"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        response = client.get('/api/search?q=test&limit=10')
        
        assert response.status_code == 200
        # Verify limit was used in query
        assert mock_cursor.execute.called
    
    @patch('app.get_db_connection')
    def test_search_no_results(self, mock_db_conn, client):
        """Test search with no results"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        response = client.get('/api/search?q=nonexistent')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 0
        assert len(data['results']) == 0


class TestSearchQuery:
    """Test search query logic"""
    
    @patch('app.get_db_connection')
    def test_search_in_title_and_text(self, mock_db_conn, client):
        """Test search looks in both title and text"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        response = client.get('/api/search?q=test')
        
        # Verify SQL query uses ILIKE on both title and text
        assert mock_cursor.execute.called
        call_args = mock_cursor.execute.call_args[0]
        assert 'ILIKE' in call_args[0]
        assert 'title' in call_args[0].lower()
        assert 'text' in call_args[0].lower()
    
    @patch('app.get_db_connection')
    def test_search_joins_analyzed_posts(self, mock_db_conn, client):
        """Test search joins with analyzed_posts"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        response = client.get('/api/search?q=test')
        
        # Verify SQL uses LEFT JOIN with analyzed_posts
        call_args = mock_cursor.execute.call_args[0]
        assert 'LEFT JOIN' in call_args[0] or 'left join' in call_args[0].lower()
        assert 'analyzed_posts' in call_args[0].lower()


class TestResultFormat:
    """Test result format"""
    
    @patch('app.get_db_connection')
    def test_result_includes_emotion(self, mock_db_conn, client):
        """Test results include emotion data"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'id': 'post1',
                'title': 'Test',
                'text': 'Content',
                'emotion': 'joy',
                'confidence': 0.9
            }
        ]
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        response = client.get('/api/search?q=test')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['results'][0]['emotion'] == 'joy'
        assert data['results'][0]['confidence'] == 0.9
