"""
Unit tests for API Gateway Service
"""

import os
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app import app, SERVICES


@pytest.fixture
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestHealth:
    """Test health endpoint"""
    
    def test_health_endpoint(self, client):
        """Test that health endpoint returns correct status"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'api_gateway'
        assert 'timestamp' in data
        assert 'services' in data
        assert len(data['services']) > 0


class TestProxy:
    """Test proxy functionality"""
    
    @patch('app.requests.request')
    def test_proxy_successful_request(self, mock_request, client):
        """Test successful proxy request"""
        # Mock successful response
        mock_response = Mock()
        mock_response.content = b'{"result": "success"}'
        mock_response.status_code = 200
        mock_response.raw.headers.items.return_value = [('Content-Type', 'application/json')]
        mock_request.return_value = mock_response
        
        response = client.get('/api/stats/stats')
        assert response.status_code == 200
        assert b'success' in response.data
    
    def test_proxy_service_not_found(self, client):
        """Test proxy with invalid service name"""
        response = client.get('/api/invalid_service/endpoint')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Service not found' in data['error']
        assert 'available' in data
    
    @patch('app.requests.request')
    def test_proxy_timeout(self, mock_request, client):
        """Test proxy timeout handling"""
        import requests
        mock_request.side_effect = requests.exceptions.Timeout()
        
        response = client.get('/api/stats/stats')
        assert response.status_code == 504
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'timeout' in data['error'].lower()
    
    @patch('app.requests.request')
    def test_proxy_connection_error(self, mock_request, client):
        """Test proxy connection error handling"""
        import requests
        mock_request.side_effect = requests.exceptions.ConnectionError()
        
        response = client.get('/api/stats/stats')
        assert response.status_code == 503
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'unavailable' in data['error'].lower()
    
    @patch('app.requests.request')
    def test_proxy_post_request(self, mock_request, client):
        """Test proxy POST request"""
        mock_response = Mock()
        mock_response.content = b'{"created": true}'
        mock_response.status_code = 201
        mock_response.raw.headers.items.return_value = []
        mock_request.return_value = mock_response
        
        response = client.post(
            '/api/ml_analyzer/analyze',
            data=json.dumps({'text': 'test'}),
            content_type='application/json'
        )
        assert response.status_code == 201
    
    @patch('app.requests.request')
    def test_proxy_generic_exception(self, mock_request, client):
        """Test proxy generic exception handling"""
        mock_request.side_effect = Exception("Generic error")
        
        response = client.get('/api/stats/stats')
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert 'error' in data


class TestDirectRoutes:
    """Test convenience routes"""
    
    @patch('app.requests.request')
    def test_get_emotions_route(self, mock_request, client):
        """Test /api/emotions route"""
        mock_response = Mock()
        mock_response.content = b'{"countries": []}'
        mock_response.status_code = 200
        mock_response.raw.headers.items.return_value = []
        mock_request.return_value = mock_response
        
        response = client.get('/api/emotions')
        assert response.status_code == 200
    
    @patch('app.requests.request')
    def test_get_stats_route(self, mock_request, client):
        """Test /api/stats route"""
        mock_response = Mock()
        mock_response.content = b'{"total": 0}'
        mock_response.status_code = 200
        mock_response.raw.headers.items.return_value = []
        mock_request.return_value = mock_response
        
        response = client.get('/api/stats')
        assert response.status_code == 200
    
    @patch('app.requests.request')
    def test_search_route(self, mock_request, client):
        """Test /api/search route"""
        mock_response = Mock()
        mock_response.content = b'{"results": []}'
        mock_response.status_code = 200
        mock_response.raw.headers.items.return_value = []
        mock_request.return_value = mock_response
        
        response = client.get('/api/search')
        assert response.status_code == 200
    
    @patch('app.requests.request')
    def test_posts_stream_route(self, mock_request, client):
        """Test /api/posts/stream route"""
        mock_response = Mock()
        mock_response.content = b'data: {}\n\n'
        mock_response.status_code = 200
        mock_response.raw.headers.items.return_value = [('Content-Type', 'text/event-stream')]
        mock_request.return_value = mock_response
        
        response = client.get('/api/posts/stream')
        assert response.status_code == 200


class TestServices:
    """Test service configuration"""
    
    def test_all_services_configured(self):
        """Test that all expected services are configured"""
        expected_services = [
            'post_fetcher', 'url_extractor', 'ml_analyzer', 'db_cleanup',
            'country_aggregation', 'cache', 'search', 'stats', 'scheduler',
            'collective_analyzer', 'cross_country_detector'
        ]
        
        for service in expected_services:
            assert service in SERVICES
            assert SERVICES[service].startswith('http://')
