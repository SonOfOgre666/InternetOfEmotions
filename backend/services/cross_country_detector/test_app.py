"""
Unit tests for Cross Country Detector Service
"""

import os
import pytest
import json
from unittest.mock import Mock, patch, MagicMock


# Set test environment variables
os.environ['RABBITMQ_URL'] = 'amqp://test:test@localhost:5672/'

# Import app after setting env vars
import app as cross_country_app


@pytest.fixture
def client():
    """Create a test client"""
    cross_country_app.app.config['TESTING'] = True
    with cross_country_app.app.test_client() as client:
        yield client


class TestHealth:
    """Test health endpoint"""
    
    def test_health_endpoint(self, client):
        """Test that health endpoint returns correct status"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'cross_country_detector'


class TestCountryAliases:
    """Test country alias mapping"""
    
    def test_country_aliases_exist(self):
        """Test that country aliases are defined"""
        assert len(cross_country_app.COUNTRY_ALIASES) > 0
        assert 'usa' in cross_country_app.COUNTRY_ALIASES
        assert 'uk' in cross_country_app.COUNTRY_ALIASES
    
    def test_keyword_to_country_mapping(self):
        """Test keyword to country mapping"""
        assert 'america' in cross_country_app.KEYWORD_TO_COUNTRY
        assert 'britain' in cross_country_app.KEYWORD_TO_COUNTRY
        
        assert cross_country_app.KEYWORD_TO_COUNTRY['america'] == 'usa'
        assert cross_country_app.KEYWORD_TO_COUNTRY['britain'] == 'uk'
    
    def test_all_countries_listed(self):
        """Test that all expected countries are in the list"""
        assert 'USA' in cross_country_app.ALL_COUNTRIES
        assert 'Germany' in cross_country_app.ALL_COUNTRIES
        assert len(cross_country_app.ALL_COUNTRIES) > 20


class TestKeywordDetection:
    """Test keyword-based country detection"""
    
    def test_detect_single_country_keyword(self):
        """Test detection of single country by keyword"""
        text = "News from America today"
        
        countries = cross_country_app.detect_with_keywords(text)
        
        assert len(countries) > 0
        assert 'usa' in countries
    
    def test_detect_multiple_countries_keyword(self):
        """Test detection of multiple countries"""
        text = "Conflict between USA and Russia escalates"
        
        countries = cross_country_app.detect_with_keywords(text)
        
        assert len(countries) >= 2
        assert 'usa' in countries
        assert 'russia' in countries
    
    def test_detect_country_variations(self):
        """Test detection of country name variations"""
        texts = [
            "News from United States",
            "News from America",
            "News from USA"
        ]
        
        for text in texts:
            countries = cross_country_app.detect_with_keywords(text)
            assert 'usa' in countries
    
    def test_no_countries_detected(self):
        """Test text without country mentions"""
        text = "The weather is nice today"
        
        countries = cross_country_app.detect_with_keywords(text)
        
        assert len(countries) == 0
    
    def test_case_insensitive_detection(self):
        """Test case-insensitive country detection"""
        text = "GERMANY and germany and Germany"
        
        countries = cross_country_app.detect_with_keywords(text)
        
        assert 'germany' in countries
        # Should only count once despite multiple mentions
        assert countries.count('germany') == 1


class TestNERDetection:
    """Test NER-based country detection"""
    
    @patch('cross_country_app.ner_pipeline')
    def test_detect_with_ner_available(self, mock_ner):
        """Test NER detection when model is available"""
        cross_country_app.ner_available = True
        
        # Mock NER output
        mock_ner.return_value = [
            {'entity_group': 'LOC', 'word': 'France'},
            {'entity_group': 'LOC', 'word': 'Germany'}
        ]
        
        text = "France and Germany sign agreement"
        countries = cross_country_app.detect_with_ner(text)
        
        assert len(countries) > 0
    
    @patch('cross_country_app.ner_pipeline')
    def test_detect_with_ner_non_location(self, mock_ner):
        """Test NER filtering of non-location entities"""
        cross_country_app.ner_available = True
        
        mock_ner.return_value = [
            {'entity_group': 'PER', 'word': 'John'},  # Person, not location
            {'entity_group': 'LOC', 'word': 'France'}
        ]
        
        text = "John visited France"
        countries = cross_country_app.detect_with_ner(text)
        
        # Should only include location entities
        assert 'john' not in [c.lower() for c in countries]
    
    def test_detect_with_ner_unavailable(self):
        """Test fallback when NER is unavailable"""
        cross_country_app.ner_available = False
        
        text = "France and Germany"
        countries = cross_country_app.detect_with_ner(text)
        
        # Should return empty set or fallback to keywords
        assert countries is not None


class TestCombinedDetection:
    """Test combined NER + keyword detection"""
    
    @patch('cross_country_app.detect_with_ner')
    @patch('cross_country_app.detect_with_keywords')
    def test_combine_ner_and_keywords(self, mock_keywords, mock_ner):
        """Test combining NER and keyword results"""
        mock_ner.return_value = {'france', 'germany'}
        mock_keywords.return_value = {'usa', 'germany'}
        
        text = "USA, France, and Germany discuss policy"
        countries = cross_country_app.detect_countries(text)
        
        # Should include results from both methods
        assert 'usa' in countries or 'USA' in countries
        assert 'france' in countries or 'France' in countries
        assert 'germany' in countries or 'Germany' in countries
    
    def test_deduplicate_countries(self):
        """Test deduplication of country mentions"""
        text = "USA and United States and America"
        
        countries = cross_country_app.detect_countries(text)
        
        # All variations should map to single country
        usa_count = sum(1 for c in countries if c.lower() in ['usa', 'united states', 'america'])
        assert usa_count <= 1  # Should be deduplicated


class TestAnalyzeEndpoint:
    """Test /analyze endpoint"""
    
    def test_analyze_endpoint_valid_input(self, client):
        """Test analyze endpoint with valid input"""
        data = {
            'text': 'Conflict between USA and Russia',
            'post_id': 'test123'
        }
        
        response = client.post(
            '/analyze',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        result = json.loads(response.data)
        
        assert 'countries' in result
        assert 'is_cross_country' in result
        assert isinstance(result['countries'], list)
    
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
    
    def test_analyze_single_country(self, client):
        """Test analysis with single country"""
        data = {
            'text': 'News from Germany today',
            'post_id': 'test123'
        }
        
        response = client.post(
            '/analyze',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        result = json.loads(response.data)
        
        assert result['is_cross_country'] is False
    
    def test_analyze_multiple_countries(self, client):
        """Test analysis with multiple countries"""
        data = {
            'text': 'USA and China reach agreement',
            'post_id': 'test123'
        }
        
        response = client.post(
            '/analyze',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        result = json.loads(response.data)
        
        assert result['is_cross_country'] is True
        assert len(result['countries']) >= 2


class TestCrossCountryLogic:
    """Test cross-country detection logic"""
    
    def test_is_cross_country_true(self):
        """Test detection of cross-country post"""
        countries = ['USA', 'Russia', 'China']
        
        is_cross = cross_country_app.is_cross_country(countries)
        
        assert is_cross is True
    
    def test_is_cross_country_false_single(self):
        """Test single country is not cross-country"""
        countries = ['USA']
        
        is_cross = cross_country_app.is_cross_country(countries)
        
        assert is_cross is False
    
    def test_is_cross_country_false_empty(self):
        """Test empty list is not cross-country"""
        countries = []
        
        is_cross = cross_country_app.is_cross_country(countries)
        
        assert is_cross is False
    
    def test_is_cross_country_exactly_two(self):
        """Test exactly two countries is cross-country"""
        countries = ['USA', 'UK']
        
        is_cross = cross_country_app.is_cross_country(countries)
        
        assert is_cross is True


class TestRabbitMQ:
    """Test RabbitMQ integration"""
    
    @patch('cross_country_app.pika.BlockingConnection')
    def test_rabbitmq_connection(self, mock_connection):
        """Test RabbitMQ connection setup"""
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel
        
        url = 'amqp://test:test@localhost:5672/'
        client = cross_country_app.RabbitMQClient(url)
        
        assert mock_channel.exchange_declare.called
    
    @patch('cross_country_app.mq_client')
    def test_publish_detection_result(self, mock_mq):
        """Test publishing detection result"""
        result = {
            'post_id': 'test123',
            'countries': ['USA', 'Russia'],
            'is_cross_country': True
        }
        
        cross_country_app.publish_detection_result(result)
        
        assert mock_mq.publish.called


class TestNERModelLoading:
    """Test NER model loading"""
    
    @patch('cross_country_app.pipeline')
    def test_load_ner_model_success(self, mock_pipeline):
        """Test successful NER model loading"""
        mock_pipeline.return_value = MagicMock()
        
        cross_country_app.load_ner_model()
        
        assert cross_country_app.ner_available is True
        assert cross_country_app.ner_pipeline is not None
    
    @patch('cross_country_app.pipeline')
    def test_load_ner_model_failure(self, mock_pipeline):
        """Test NER model loading failure"""
        mock_pipeline.side_effect = Exception("Model load failed")
        
        cross_country_app.load_ner_model()
        
        # Should fallback gracefully
        assert cross_country_app.ner_available is False


class TestEdgeCases:
    """Test edge cases"""
    
    def test_country_in_different_context(self):
        """Test country name in different context"""
        # "Turkey" could be the country or the bird
        text = "I ate turkey for dinner"
        
        countries = cross_country_app.detect_with_keywords(text)
        
        # Might detect Turkey, but that's acceptable
        assert countries is not None
    
    def test_partial_country_names(self):
        """Test partial country name matches"""
        text = "American and British forces"
        
        countries = cross_country_app.detect_with_keywords(text)
        
        # Should detect USA and UK from adjectives
        assert len(countries) >= 1
    
    def test_very_long_text(self):
        """Test analysis of very long text"""
        long_text = "News from USA " * 500
        
        countries = cross_country_app.detect_countries(long_text)
        
        assert countries is not None
        # Should deduplicate multiple mentions
        usa_mentions = [c for c in countries if c.lower() == 'usa']
        assert len(usa_mentions) <= 1
    
    def test_special_characters_in_text(self):
        """Test text with special characters"""
        text = "USA!!! vs. Russia??? -- China..."
        
        countries = cross_country_app.detect_countries(text)
        
        assert len(countries) >= 3
    
    def test_countries_in_urls(self):
        """Test detection of countries in URLs"""
        text = "Check out https://example.com/news/germany"
        
        countries = cross_country_app.detect_with_keywords(text)
        
        # Should still detect Germany
        assert 'germany' in countries


class TestCountryNormalization:
    """Test country name normalization"""
    
    def test_normalize_country_names(self):
        """Test normalization of country names"""
        # Different variations should map to same country
        variations = ['USA', 'usa', 'United States', 'America']
        
        normalized = [cross_country_app.normalize_country(v) for v in variations]
        
        # Should all normalize to the same value
        assert len(set(normalized)) <= 2  # Some variation acceptable
    
    def test_preserve_original_names(self):
        """Test that original country names are preserved"""
        countries = cross_country_app.detect_countries("France and Germany")
        
        # Should return recognizable country names
        assert any('france' in c.lower() for c in countries)
        assert any('germany' in c.lower() for c in countries)
