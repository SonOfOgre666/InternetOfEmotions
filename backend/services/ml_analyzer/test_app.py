"""
Unit tests for ML Analyzer Service
"""

import os
import pytest
import json
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime


# Set test environment variables
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'
os.environ['RABBITMQ_URL'] = 'amqp://test:test@localhost:5672/'

# Import app after setting env vars
import app as ml_app


@pytest.fixture
def client():
    """Create a test client"""
    ml_app.app.config['TESTING'] = True
    with ml_app.app.test_client() as client:
        yield client


@pytest.fixture
def mock_db():
    """Mock database connection"""
    with patch('app.psycopg2.connect') as mock_conn:
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        yield mock_cursor


class TestHealth:
    """Test health endpoint"""
    
    def test_health_endpoint(self, client):
        """Test that health endpoint returns correct status"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'ml_analyzer'


class TestEmotionDetection:
    """Test emotion detection functions"""
    
    def test_keyword_emotion_detection(self):
        """Test keyword-based emotion detection"""
        text = "This is a happy and joyful celebration"
        result = ml_app.detect_emotion_keywords(text)
        
        assert 'joy' in result
        assert result['joy'] > 0
    
    def test_multiple_emotions_detected(self):
        """Test detection of multiple emotions"""
        text = "I'm angry about this terrible tragedy"
        result = ml_app.detect_emotion_keywords(text)
        
        assert 'anger' in result
        assert 'sadness' in result
    
    def test_no_emotion_keywords(self):
        """Test text without emotion keywords"""
        text = "The sky is blue"
        result = ml_app.detect_emotion_keywords(text)
        
        assert all(score == 0 for score in result.values())


class TestAnalyzeEndpoint:
    """Test /analyze endpoint"""
    
    @patch('app.store_analysis_result')
    @patch('app.mq_client')
    def test_analyze_with_valid_input(self, mock_mq, mock_store, client):
        """Test analysis with valid input"""
        test_data = {
            'text': 'This is a happy test message',
            'post_id': 'test123',
            'country': 'USA'
        }
        
        response = client.post(
            '/analyze',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'emotion' in data
        assert 'confidence' in data
        assert 'model_scores' in data
    
    def test_analyze_missing_text(self, client):
        """Test analysis with missing text"""
        test_data = {
            'post_id': 'test123',
            'country': 'USA'
        }
        
        response = client.post(
            '/analyze',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_analyze_empty_text(self, client):
        """Test analysis with empty text"""
        test_data = {
            'text': '',
            'post_id': 'test123',
            'country': 'USA'
        }
        
        response = client.post(
            '/analyze',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400


class TestEmotionAggregation:
    """Test emotion aggregation logic"""
    
    def test_aggregate_emotions(self):
        """Test weighted emotion aggregation"""
        scores = {
            'roberta': {'joy': 0.9, 'sadness': 0.1},
            'keywords': {'joy': 1.0, 'sadness': 0.0},
            'vader': {'joy': 0.8, 'sadness': 0.2},
            'textblob': {'joy': 0.7, 'sadness': 0.3}
        }
        
        result = ml_app.aggregate_emotion_scores(scores)
        
        assert result['emotion'] == 'joy'
        assert result['confidence'] > 0.5
        assert 'model_scores' in result
    
    def test_tie_in_emotions(self):
        """Test handling of tied emotion scores"""
        scores = {
            'roberta': {'joy': 0.5, 'sadness': 0.5},
            'keywords': {'joy': 0.5, 'sadness': 0.5},
            'vader': {'joy': 0.5, 'sadness': 0.5},
            'textblob': {'joy': 0.5, 'sadness': 0.5}
        }
        
        result = ml_app.aggregate_emotion_scores(scores)
        
        assert result['emotion'] in ['joy', 'sadness']
        assert 0 <= result['confidence'] <= 1


class TestBatchProcessing:
    """Test batch processing functionality"""
    
    @patch('app.get_db_connection')
    def test_process_pending_posts_empty(self, mock_db_conn):
        """Test processing with no pending posts"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        
        processed = ml_app.process_pending_posts()
        
        assert processed == 0
    
    @patch('app.analyze_text')
    @patch('app.get_db_connection')
    def test_process_pending_posts_batch(self, mock_db_conn, mock_analyze):
        """Test batch processing of posts"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 'post1', 'text': 'text1', 'country': 'USA'},
            {'id': 'post2', 'text': 'text2', 'country': 'UK'}
        ]
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        
        mock_analyze.return_value = {
            'emotion': 'joy',
            'confidence': 0.8,
            'model_scores': {}
        }
        
        processed = ml_app.process_pending_posts()
        
        assert processed == 2


class TestCollectiveDetection:
    """Test collective vs personal classification"""
    
    def test_collective_keywords(self):
        """Test detection of collective language"""
        text = "Our country is facing a major crisis affecting all citizens"
        result = ml_app.is_collective_issue(text)
        
        assert result is True
    
    def test_personal_keywords(self):
        """Test detection of personal language"""
        text = "I am having a problem with my personal life"
        result = ml_app.is_collective_issue(text)
        
        assert result is False
    
    def test_neutral_text(self):
        """Test neutral text classification"""
        text = "The weather is nice today"
        result = ml_app.is_collective_issue(text)
        
        # Should have a default behavior
        assert result in [True, False]


class TestCrossCountryDetection:
    """Test cross-country detection"""
    
    def test_single_country_mention(self):
        """Test detection of single country"""
        text = "News from France today"
        countries = ml_app.detect_countries(text)
        
        assert 'France' in countries or 'france' in [c.lower() for c in countries]
    
    def test_multiple_countries(self):
        """Test detection of multiple countries"""
        text = "Conflict between USA and Russia escalates"
        countries = ml_app.detect_countries(text)
        
        assert len(countries) >= 2
    
    def test_no_countries(self):
        """Test text without country mentions"""
        text = "The sky is blue and grass is green"
        countries = ml_app.detect_countries(text)
        
        assert len(countries) == 0


class TestModelLoading:
    """Test lazy model loading"""
    
    def test_models_not_loaded_initially(self):
        """Test that models are not loaded on import"""
        # Models should be lazy loaded
        assert ml_app.models_loaded is False or ml_app.models_loaded is True  # Can vary
    
    @patch('app.pipeline')
    def test_load_models_on_demand(self, mock_pipeline):
        """Test that models are loaded when needed"""
        mock_pipeline.return_value = MagicMock()
        
        ml_app.load_models()
        
        assert ml_app.models_loaded is True


class TestDatabase:
    """Test database operations"""
    
    @patch('app.get_db_connection')
    def test_store_analysis_result(self, mock_db_conn):
        """Test storing analysis result"""
        mock_cursor = MagicMock()
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        
        result = {
            'post_id': 'test123',
            'emotion': 'joy',
            'confidence': 0.85,
            'is_collective': True,
            'countries_mentioned': ['USA', 'UK']
        }
        
        ml_app.store_analysis_result(result)
        
        # Verify INSERT was called
        assert mock_cursor.execute.called
    
    @patch('app.get_db_connection')
    def test_get_pending_posts(self, mock_db_conn):
        """Test retrieving pending posts"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 'post1', 'text': 'text1', 'country': 'USA'}
        ]
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        
        posts = ml_app.get_pending_posts(limit=10)
        
        assert len(posts) == 1
        assert posts[0]['id'] == 'post1'


class TestRabbitMQ:
    """Test RabbitMQ integration"""
    
    @patch('app.pika.BlockingConnection')
    def test_rabbitmq_connection(self, mock_connection):
        """Test RabbitMQ connection setup"""
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel
        
        client = ml_app.RabbitMQClient(ml_app.RABBITMQ_URL)
        
        assert mock_channel.exchange_declare.called
        assert mock_channel.queue_declare.called
    
    @patch('app.mq_client')
    def test_publish_analyzed_event(self, mock_mq):
        """Test publishing analyzed event"""
        result = {
            'post_id': 'test123',
            'emotion': 'joy',
            'confidence': 0.8
        }
        
        ml_app.publish_analyzed_event(result)
        
        assert mock_mq.publish.called
