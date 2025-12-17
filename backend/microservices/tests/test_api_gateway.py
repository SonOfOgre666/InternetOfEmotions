"""
Unit tests for API Gateway microservice
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

@pytest.fixture
def app():
    """Create test Flask app"""
    with patch('api_gateway.app.SharedDatabase'):
        from api_gateway import app as flask_app
        flask_app.app.config['TESTING'] = True
        yield flask_app.app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_endpoint(self, client):
        """Test /health endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'api-gateway'
    
    def test_api_health_endpoint(self, client):
        """Test /api/health endpoint"""
        with patch('api_gateway.app.db') as mock_db:
            mock_cursor = Mock()
            mock_cursor.execute = Mock(return_value=Mock())
            mock_cursor.fetchone = Mock(return_value=[100])
            mock_db.get_connection = Mock(return_value=Mock(cursor=Mock(return_value=mock_cursor)))
            
            response = client.get('/api/health')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'healthy'
            assert 'db_posts' in data


class TestEmotionsEndpoint:
    """Test emotions endpoint"""
    
    @patch('api_gateway.app.requests.get')
    def test_get_emotions_success(self, mock_get, client):
        """Test successful emotions retrieval"""
        # Mock aggregator response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={
            'countries': [
                {
                    'country': 'united states',
                    'emotions': {'joy': 0.7, 'sadness': 0.3},
                    'top_emotion': 'joy',
                    'total_posts': 50
                }
            ]
        })
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        response = client.get('/api/emotions')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'emotions' in data
        assert 'count' in data
        assert data['demo_mode'] == False
    
    @patch('api_gateway.app.requests.get')
    def test_get_emotions_service_timeout(self, mock_get, client):
        """Test emotions endpoint with service timeout"""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()
        
        response = client.get('/api/emotions')
        assert response.status_code == 504
        data = json.loads(response.data)
        assert 'error' in data


class TestStatsEndpoint:
    """Test statistics endpoint"""
    
    def test_get_stats_success(self, client):
        """Test successful stats retrieval"""
        with patch('api_gateway.app.db') as mock_db:
            mock_cursor = Mock()
            mock_cursor.execute = Mock(return_value=Mock())
            mock_cursor.fetchone = Mock(side_effect=[[5], [100]])
            mock_cursor.fetchall = Mock(side_effect=[
                [('joy', 50), ('sadness', 30), ('anger', 20)],
                [('united states', 100)]
            ])
            mock_db.get_connection = Mock(return_value=Mock(cursor=Mock(return_value=mock_cursor)))
            
            response = client.get('/api/stats')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'total' in data
            assert 'by_emotion' in data
            assert 'by_country' in data


class TestCountryEndpoint:
    """Test country details endpoint"""
    
    @patch('api_gateway.app.requests.get')
    def test_get_country_details_success(self, mock_get, client):
        """Test successful country details retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={
            'country': 'united states',
            'emotions': {'joy': 0.7},
            'top_emotion': 'joy',
            'total_posts': 50,
            'recent_events': []
        })
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        response = client.get('/api/country/united states')
        assert response.status_code == 200
    
    @patch('api_gateway.app.requests.get')
    def test_get_country_not_found(self, mock_get, client):
        """Test country not found"""
        import requests
        mock_response = Mock()
        mock_response.status_code = 404
        http_error = requests.exceptions.HTTPError()
        http_error.response = mock_response
        mock_get.side_effect = http_error
        
        response = client.get('/api/country/nonexistent')
        assert response.status_code == 404


class TestProcessingEndpoints:
    """Test background processing control endpoints"""
    
    def test_start_processing(self, client):
        """Test starting background processing"""
        response = client.post('/api/process/start')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
    
    def test_stop_processing(self, client):
        """Test stopping background processing"""
        response = client.post('/api/process/stop')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data


@pytest.mark.integration
class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    @patch('api_gateway.app.requests.get')
    def test_circuit_breaker_opens_after_failures(self, mock_get, client):
        """Test circuit breaker opens after repeated failures"""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        # Make multiple failing requests
        for _ in range(6):
            response = client.get('/api/emotions')
            assert response.status_code in [503, 502, 504]
