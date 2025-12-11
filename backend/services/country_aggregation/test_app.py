"""
Unit tests for Country Aggregation Service
"""

import os
import pytest
import json
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from collections import Counter


# Set test environment variables
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'
os.environ['RABBITMQ_URL'] = 'amqp://test:test@localhost:5672/'

# Import app after setting env vars
import app as country_app


@pytest.fixture
def client():
    """Create a test client"""
    country_app.app.config['TESTING'] = True
    with country_app.app.test_client() as client:
        yield client


@pytest.fixture
def aggregator():
    """Create an aggregator instance"""
    return country_app.CountryEmotionAggregator()


@pytest.fixture
def sample_posts():
    """Sample posts for testing"""
    return [
        {
            'id': 'post1',
            'emotion': 'joy',
            'confidence': 0.8,
            'country': 'USA'
        },
        {
            'id': 'post2',
            'emotion': 'joy',
            'confidence': 0.9,
            'country': 'USA'
        },
        {
            'id': 'post3',
            'emotion': 'sadness',
            'confidence': 0.7,
            'country': 'USA'
        }
    ]


class TestHealth:
    """Test health endpoint"""
    
    def test_health_endpoint(self, client):
        """Test that health endpoint returns correct status"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'country_aggregation'


class TestCountryCoordinates:
    """Test country coordinates mapping"""
    
    def test_country_coords_exist(self):
        """Test that country coordinates are loaded"""
        from country_coordinates import COUNTRY_COORDS
        
        assert len(COUNTRY_COORDS) > 0
        assert 'USA' in COUNTRY_COORDS or 'United States' in COUNTRY_COORDS


class TestEmotionAggregator:
    """Test emotion aggregation algorithms"""
    
    def test_aggregator_initialization(self, aggregator):
        """Test aggregator initializes with emotion intensities"""
        assert aggregator.emotion_intensity is not None
        assert 'anger' in aggregator.emotion_intensity
        assert 'joy' in aggregator.emotion_intensity
    
    def test_aggregate_empty_posts(self, aggregator):
        """Test aggregation with empty post list"""
        result = aggregator.aggregate([])
        assert result is None
    
    def test_aggregate_single_post(self, aggregator):
        """Test aggregation with single post"""
        posts = [
            {'emotion': 'joy', 'confidence': 0.8}
        ]
        
        result = aggregator.aggregate(posts)
        
        assert result is not None
        assert 'emotion' in result
        assert result['emotion'] == 'joy'
    
    def test_aggregate_majority_wins(self, aggregator, sample_posts):
        """Test that majority emotion wins"""
        result = aggregator.aggregate(sample_posts)
        
        assert result is not None
        assert result['emotion'] == 'joy'  # 2 joy vs 1 sadness
    
    def test_aggregate_includes_confidence(self, aggregator, sample_posts):
        """Test that result includes confidence score"""
        result = aggregator.aggregate(sample_posts)
        
        assert 'confidence' in result
        assert 0 <= result['confidence'] <= 1
    
    def test_aggregate_includes_method(self, aggregator, sample_posts):
        """Test that result includes aggregation method"""
        result = aggregator.aggregate(sample_posts)
        
        assert 'method' in result
        assert result['method'] in ['majority', 'weighted', 'intensity', 'median']


class TestMajorityVoting:
    """Test majority voting algorithm"""
    
    def test_clear_majority(self, aggregator):
        """Test clear majority case"""
        posts = [
            {'emotion': 'joy', 'confidence': 0.8},
            {'emotion': 'joy', 'confidence': 0.7},
            {'emotion': 'joy', 'confidence': 0.9},
            {'emotion': 'sadness', 'confidence': 0.6}
        ]
        
        result = aggregator._majority_vote(posts)
        assert result == 'joy'
    
    def test_tie_breaking(self, aggregator):
        """Test tie breaking in majority vote"""
        posts = [
            {'emotion': 'joy', 'confidence': 0.8},
            {'emotion': 'sadness', 'confidence': 0.8}
        ]
        
        result = aggregator._majority_vote(posts)
        # Should return one of the tied emotions
        assert result in ['joy', 'sadness']


class TestWeightedAggregation:
    """Test weighted aggregation algorithm"""
    
    def test_weighted_by_confidence(self, aggregator):
        """Test weighting by confidence scores"""
        posts = [
            {'emotion': 'joy', 'confidence': 0.9},  # High confidence
            {'emotion': 'sadness', 'confidence': 0.3},  # Low confidence
            {'emotion': 'sadness', 'confidence': 0.3}
        ]
        
        result = aggregator._weighted_aggregate(posts)
        # High confidence joy should win despite fewer votes
        assert result == 'joy'


class TestIntensityWeighting:
    """Test intensity-based aggregation"""
    
    def test_intensity_weights(self, aggregator):
        """Test that emotions have proper intensity weights"""
        assert aggregator.emotion_intensity['anger'] > aggregator.emotion_intensity['neutral']
        assert aggregator.emotion_intensity['fear'] > aggregator.emotion_intensity['surprise']
    
    def test_intensity_aggregation(self, aggregator):
        """Test aggregation using intensity weights"""
        posts = [
            {'emotion': 'anger', 'confidence': 0.7},  # High intensity
            {'emotion': 'neutral', 'confidence': 0.9},  # Low intensity but high confidence
            {'emotion': 'neutral', 'confidence': 0.8}
        ]
        
        result = aggregator._intensity_weighted(posts)
        # Anger has high intensity so might win
        assert result in ['anger', 'neutral']


class TestMedianAggregation:
    """Test median-based aggregation"""
    
    def test_median_emotion(self, aggregator):
        """Test median emotion selection"""
        posts = [
            {'emotion': 'joy', 'confidence': 0.9},
            {'emotion': 'joy', 'confidence': 0.8},
            {'emotion': 'sadness', 'confidence': 0.7},
            {'emotion': 'anger', 'confidence': 0.6},
            {'emotion': 'fear', 'confidence': 0.5}
        ]
        
        result = aggregator._median_emotion(posts)
        assert result is not None


class TestCountryUpdate:
    """Test country-level emotion update"""
    
    @patch('app.get_db_connection')
    @patch('app.mq_client')
    def test_update_country_emotion(self, mock_mq, mock_db_conn):
        """Test updating country emotion"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'emotion': 'joy', 'confidence': 0.8},
            {'emotion': 'joy', 'confidence': 0.9}
        ]
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        country_app.update_country_emotion('USA')
        
        # Should query posts and update country emotion
        assert mock_cursor.execute.called
    
    @patch('app.get_db_connection')
    def test_update_country_no_posts(self, mock_db_conn):
        """Test updating country with no posts"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        # Should handle gracefully
        country_app.update_country_emotion('UNKNOWN')


class TestAPIEndpoints:
    """Test API endpoints"""
    
    @patch('app.get_db_connection')
    def test_get_countries_endpoint(self, mock_db_conn, client):
        """Test getting all countries"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'country': 'USA',
                'emotion': 'joy',
                'confidence': 0.8,
                'post_count': 10,
                'updated_at': datetime.now()
            }
        ]
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        response = client.get('/api/countries')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'countries' in data
        assert len(data['countries']) > 0
    
    @patch('app.get_db_connection')
    def test_get_single_country_endpoint(self, mock_db_conn, client):
        """Test getting single country data"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'country': 'USA',
            'emotion': 'joy',
            'confidence': 0.8,
            'post_count': 10
        }
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        response = client.get('/api/countries/USA')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['country'] == 'USA'
    
    @patch('app.get_db_connection')
    def test_get_nonexistent_country(self, mock_db_conn, client):
        """Test getting nonexistent country"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        response = client.get('/api/countries/UNKNOWN')
        
        assert response.status_code == 404


class TestRabbitMQ:
    """Test RabbitMQ integration"""
    
    @patch('app.pika.BlockingConnection')
    def test_rabbitmq_connection(self, mock_connection):
        """Test RabbitMQ connection setup"""
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel
        
        client = country_app.RabbitMQClient(country_app.RABBITMQ_URL)
        
        assert mock_channel.exchange_declare.called
        assert mock_channel.queue_declare.called
        assert mock_channel.queue_bind.called
    
    @patch('app.mq_client')
    def test_publish_country_updated_event(self, mock_mq):
        """Test publishing country.updated event"""
        country_data = {
            'country': 'USA',
            'emotion': 'joy',
            'confidence': 0.8
        }
        
        country_app.publish_country_updated(country_data)
        
        assert mock_mq.publish.called
        call_args = mock_mq.publish.call_args
        assert call_args[0][0] == 'country.updated'


class TestEventProcessing:
    """Test event processing"""
    
    @patch('app.update_country_emotion')
    def test_process_analyzed_event(self, mock_update):
        """Test processing post.analyzed event"""
        event_data = {
            'post_id': 'test123',
            'country': 'USA',
            'emotion': 'joy',
            'confidence': 0.8
        }
        
        # Mock the callback
        channel = MagicMock()
        method = MagicMock()
        method.delivery_tag = 'tag123'
        properties = MagicMock()
        body = json.dumps(event_data)
        
        country_app.on_post_analyzed(channel, method, properties, body)
        
        assert mock_update.called


class TestDatabaseOperations:
    """Test database operations"""
    
    @patch('app.get_db_connection')
    def test_get_country_posts(self, mock_db_conn):
        """Test retrieving posts for a country"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 'post1', 'emotion': 'joy', 'confidence': 0.8}
        ]
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        posts = country_app.get_country_posts('USA')
        
        assert len(posts) > 0
        assert posts[0]['emotion'] == 'joy'
    
    @patch('app.get_db_connection')
    def test_store_country_emotion(self, mock_db_conn):
        """Test storing country emotion"""
        mock_cursor = MagicMock()
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        emotion_data = {
            'country': 'USA',
            'emotion': 'joy',
            'confidence': 0.85,
            'post_count': 10
        }
        
        country_app.store_country_emotion(emotion_data)
        
        # Should execute INSERT or UPDATE
        assert mock_cursor.execute.called
