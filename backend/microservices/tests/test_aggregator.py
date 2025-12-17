"""
Unit tests for Aggregator microservice
"""
import pytest
from unittest.mock import Mock, patch
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

@pytest.fixture
def app():
    """Create test Flask app"""
    with patch('aggregator.app.SharedDatabase'):
        from aggregator import app as flask_app
        flask_app.app.config['TESTING'] = True
        yield flask_app.app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestAggregator:
    """Test country emotion aggregation"""
    
    def test_aggregate_country_with_data(self, sample_country_data):
        """Test aggregating country with posts"""
        from aggregator.app import CountryEmotionAggregator
        
        with patch('aggregator.app.db') as mock_db:
            mock_cursor = Mock()
            mock_cursor.execute = Mock()
            mock_cursor.fetchall = Mock(return_value=[
                ('joy', 0.9),
                ('joy', 0.8),
                ('sadness', 0.3)
            ])
            mock_db.get_connection.return_value.cursor.return_value = mock_cursor
            
            aggregator = CountryEmotionAggregator()
            result = aggregator.aggregate_country('united states')
            
            assert result is not None
            assert result['country'] == 'united states'
            assert 'emotions' in result
            assert 'top_emotion' in result
    
    def test_aggregate_country_no_data(self):
        """Test aggregating country without data"""
        from aggregator.app import CountryEmotionAggregator
        
        with patch('aggregator.app.db') as mock_db:
            mock_cursor = Mock()
            mock_cursor.fetchall = Mock(return_value=[])
            mock_db.get_connection.return_value.cursor.return_value = mock_cursor
            
            aggregator = CountryEmotionAggregator()
            result = aggregator.aggregate_country('nonexistent')
            
            assert result is None


class TestAggregationEndpoints:
    """Test aggregation API endpoints"""
    
    @patch('aggregator.app.aggregator')
    def test_aggregate_country_endpoint(self, mock_agg, client):
        """Test country aggregation endpoint"""
        mock_agg.aggregate_country.return_value = {
            'country': 'united states',
            'emotions': {'joy': 0.7},
            'top_emotion': 'joy',
            'total_events': 50
        }
        
        response = client.post('/aggregate/country/united states')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['country'] == 'united states'
    
    @patch('aggregator.app.aggregator')
    def test_aggregate_all_endpoint(self, mock_agg, client):
        """Test aggregate all countries endpoint"""
        mock_agg.aggregate_all_countries.return_value = [
            {'country': 'usa', 'emotions': {'joy': 0.7}, 'top_emotion': 'joy', 'total_events': 50},
            {'country': 'uk', 'emotions': {'sadness': 0.6}, 'top_emotion': 'sadness', 'total_events': 30}
        ]
        
        response = client.post('/aggregate/all')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['aggregated_countries'] == 2
    
    @patch('aggregator.app.db')
    def test_get_country_emotions(self, mock_db, client):
        """Test getting country emotions"""
        mock_cursor = Mock()
        mock_cursor.execute = Mock()
        mock_cursor.fetchone = Mock(return_value=[
            'united states',
            '{"joy": 0.7}',
            'joy',
            50,
            '2025-12-12T10:00:00'
        ])
        mock_cursor.fetchall = Mock(return_value=[])
        mock_db.get_connection.return_value.cursor.return_value = mock_cursor
        
        response = client.get('/country/united states')
        assert response.status_code == 200


class TestCountriesEndpoint:
    """Test get all countries endpoint"""
    
    @patch('aggregator.app.db')
    def test_get_all_countries(self, mock_db, client):
        """Test getting all aggregated countries"""
        mock_db.execute_query.return_value = [
            ('usa', '{"joy": 0.7}', 'joy', 50, '2025-12-12'),
            ('uk', '{"sadness": 0.6}', 'sadness', 30, '2025-12-12')
        ]
        
        response = client.get('/countries')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'countries' in data
        assert data['total'] == 2
