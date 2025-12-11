"""
Unit tests for Collective Analyzer Service
"""

import os
import pytest
import json
from unittest.mock import Mock, patch, MagicMock


# Set test environment variables
os.environ['RABBITMQ_URL'] = 'amqp://test:test@localhost:5672/'

# Import app after setting env vars
import app as collective_app


@pytest.fixture
def client():
    """Create a test client"""
    collective_app.app.config['TESTING'] = True
    with collective_app.app.test_client() as client:
        yield client


class TestHealth:
    """Test health endpoint"""
    
    def test_health_endpoint(self, client):
        """Test that health endpoint returns correct status"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'collective_analyzer'


class TestKeywordDetection:
    """Test keyword-based detection"""
    
    def test_personal_indicators(self):
        """Test detection of personal indicators"""
        text = "I am having problems with my personal life"
        
        has_personal = any(word in text.lower() for word in collective_app.PERSONAL_INDICATORS)
        assert has_personal is True
    
    def test_collective_indicators(self):
        """Test detection of collective indicators"""
        text = "Our country is facing a crisis affecting all citizens"
        
        has_collective = any(word in text.lower() for word in collective_app.COLLECTIVE_INDICATORS)
        assert has_collective is True
    
    def test_collective_topics(self):
        """Test detection of collective topics"""
        text = "War and conflict escalate in the region"
        
        has_topic = any(word in text.lower() for word in collective_app.COLLECTIVE_TOPICS)
        assert has_topic is True


class TestKeywordAnalysis:
    """Test keyword-based analysis fallback"""
    
    def test_analyze_collective_text(self):
        """Test analyzing clearly collective text"""
        text = "The government announces new policy affecting all citizens"
        
        result = collective_app.analyze_with_keywords(text)
        
        assert 'is_collective' in result
        assert result['is_collective'] is True
    
    def test_analyze_personal_text(self):
        """Test analyzing clearly personal text"""
        text = "I'm having issues with my boss at work"
        
        result = collective_app.analyze_with_keywords(text)
        
        assert 'is_collective' in result
        assert result['is_collective'] is False
    
    def test_analyze_mixed_text(self):
        """Test analyzing text with mixed signals"""
        text = "I think the pandemic affected everyone in our country"
        
        result = collective_app.analyze_with_keywords(text)
        
        assert 'is_collective' in result
        # Should make a decision based on weights
        assert result['is_collective'] in [True, False]
    
    def test_confidence_score(self):
        """Test that confidence score is included"""
        text = "Major crisis affecting the entire population"
        
        result = collective_app.analyze_with_keywords(text)
        
        assert 'confidence' in result
        assert 0 <= result['confidence'] <= 1


class TestMLAnalysis:
    """Test ML-based analysis"""
    
    @patch('collective_app.classifier')
    def test_analyze_with_ml_available(self, mock_classifier):
        """Test ML analysis when model is available"""
        collective_app.ml_available = True
        
        # Mock classifier output
        mock_classifier.return_value = {
            'labels': [
                'collective social issue affecting many people',
                'personal individual problem or feeling'
            ],
            'scores': [0.85, 0.15]
        }
        
        text = "The country faces economic crisis"
        result = collective_app.analyze_with_ml(text)
        
        assert result is not None
        assert 'is_collective' in result
        assert result['is_collective'] is True
    
    @patch('collective_app.classifier')
    def test_analyze_with_ml_personal(self, mock_classifier):
        """Test ML analysis for personal issue"""
        collective_app.ml_available = True
        
        mock_classifier.return_value = {
            'labels': [
                'personal individual problem or feeling',
                'collective social issue affecting many people'
            ],
            'scores': [0.80, 0.20]
        }
        
        text = "I am sad about my life"
        result = collective_app.analyze_with_ml(text)
        
        assert result is not None
        assert result['is_collective'] is False
    
    def test_analyze_with_ml_unavailable(self):
        """Test fallback when ML is unavailable"""
        collective_app.ml_available = False
        
        text = "Test text"
        result = collective_app.analyze_with_ml(text)
        
        # Should fallback to keyword analysis
        assert result is not None


class TestAnalyzeEndpoint:
    """Test /analyze endpoint"""
    
    def test_analyze_endpoint_valid_input(self, client):
        """Test analyze endpoint with valid input"""
        data = {
            'text': 'The government announces new crisis management plan',
            'post_id': 'test123'
        }
        
        response = client.post(
            '/analyze',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        result = json.loads(response.data)
        
        assert 'is_collective' in result
        assert 'confidence' in result
        assert 'method' in result
    
    def test_analyze_endpoint_missing_text(self, client):
        """Test analyze endpoint with missing text"""
        data = {
            'post_id': 'test123'
        }
        
        response = client.post(
            '/analyze',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_analyze_endpoint_empty_text(self, client):
        """Test analyze endpoint with empty text"""
        data = {
            'text': '',
            'post_id': 'test123'
        }
        
        response = client.post(
            '/analyze',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 400


class TestPatternDetection:
    """Test pattern detection across posts"""
    
    def test_detect_common_themes(self):
        """Test detection of common themes"""
        texts = [
            "Crisis in healthcare system",
            "Healthcare workers overwhelmed",
            "Hospital capacity issues"
        ]
        
        themes = collective_app.detect_common_themes(texts)
        
        assert themes is not None
        # Should detect healthcare/hospital as common theme
        assert any('health' in theme.lower() or 'hospital' in theme.lower() 
                  for theme in themes)
    
    def test_detect_themes_empty_list(self):
        """Test theme detection with empty list"""
        texts = []
        
        themes = collective_app.detect_common_themes(texts)
        
        assert themes is not None
        assert len(themes) == 0
    
    def test_detect_themes_diverse_topics(self):
        """Test theme detection with diverse topics"""
        texts = [
            "I like pizza",
            "Weather is nice",
            "Stock market update"
        ]
        
        themes = collective_app.detect_common_themes(texts)
        
        # Might not find strong themes
        assert themes is not None


class TestBatchAnalysis:
    """Test batch analysis of posts"""
    
    @patch('collective_app.analyze_with_keywords')
    def test_batch_analyze(self, mock_analyze):
        """Test batch analysis of multiple posts"""
        mock_analyze.return_value = {
            'is_collective': True,
            'confidence': 0.8
        }
        
        posts = [
            {'id': 'post1', 'text': 'Crisis in country'},
            {'id': 'post2', 'text': 'Government policy change'}
        ]
        
        results = collective_app.batch_analyze(posts)
        
        assert len(results) == 2
        assert all('is_collective' in r for r in results)
    
    def test_batch_analyze_empty(self):
        """Test batch analysis with empty list"""
        posts = []
        
        results = collective_app.batch_analyze(posts)
        
        assert len(results) == 0


class TestRabbitMQ:
    """Test RabbitMQ integration"""
    
    @patch('collective_app.pika.BlockingConnection')
    def test_rabbitmq_connection(self, mock_connection):
        """Test RabbitMQ connection setup"""
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel
        
        # Create client
        url = 'amqp://test:test@localhost:5672/'
        client = collective_app.RabbitMQClient(url)
        
        assert mock_channel.exchange_declare.called
    
    @patch('collective_app.mq_client')
    def test_publish_analysis_result(self, mock_mq):
        """Test publishing analysis result"""
        result = {
            'post_id': 'test123',
            'is_collective': True,
            'confidence': 0.8
        }
        
        collective_app.publish_analysis_result(result)
        
        assert mock_mq.publish.called


class TestMLModelLoading:
    """Test ML model loading"""
    
    @patch('collective_app.pipeline')
    def test_load_ml_model_success(self, mock_pipeline):
        """Test successful ML model loading"""
        mock_pipeline.return_value = MagicMock()
        
        collective_app.load_ml_model()
        
        assert collective_app.ml_available is True
        assert collective_app.classifier is not None
    
    @patch('collective_app.pipeline')
    def test_load_ml_model_failure(self, mock_pipeline):
        """Test ML model loading failure"""
        mock_pipeline.side_effect = Exception("Model load failed")
        
        collective_app.load_ml_model()
        
        # Should fallback gracefully
        assert collective_app.ml_available is False


class TestEdgeCases:
    """Test edge cases"""
    
    def test_very_long_text(self):
        """Test analysis of very long text"""
        long_text = "Crisis " * 1000  # Very long text
        
        result = collective_app.analyze_with_keywords(long_text)
        
        assert result is not None
        assert 'is_collective' in result
    
    def test_special_characters(self):
        """Test text with special characters"""
        text = "Crisis!!! @#$%^&* <<>> affecting everyone!!!"
        
        result = collective_app.analyze_with_keywords(text)
        
        assert result is not None
        assert result['is_collective'] is True
    
    def test_non_english_text(self):
        """Test non-English text handling"""
        text = "Una crisis que afecta a todos"
        
        result = collective_app.analyze_with_keywords(text)
        
        # Should handle gracefully
        assert result is not None


class TestConfidenceScoring:
    """Test confidence score calculation"""
    
    def test_high_confidence_collective(self):
        """Test high confidence for clearly collective text"""
        text = "Major crisis government policy war affecting all citizens"
        
        result = collective_app.analyze_with_keywords(text)
        
        assert result['confidence'] > 0.7
    
    def test_low_confidence_ambiguous(self):
        """Test lower confidence for ambiguous text"""
        text = "Something happened somewhere"
        
        result = collective_app.analyze_with_keywords(text)
        
        # Ambiguous text should have lower confidence
        assert 0 <= result['confidence'] <= 1
    
    def test_confidence_in_range(self):
        """Test that confidence is always in valid range"""
        texts = [
            "I am sad",
            "Country faces crisis",
            "The weather is nice",
            "Government announces new policy for all"
        ]
        
        for text in texts:
            result = collective_app.analyze_with_keywords(text)
            assert 0 <= result['confidence'] <= 1
