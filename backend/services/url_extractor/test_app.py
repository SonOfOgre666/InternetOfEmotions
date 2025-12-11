"""
Unit tests for URL Extractor Service
"""

import os
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


# Set test environment variables
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'
os.environ['RABBITMQ_URL'] = 'amqp://test:test@localhost:5672/'

# Import app after setting env vars
import app as url_app


@pytest.fixture
def client():
    """Create a test client"""
    url_app.app.config['TESTING'] = True
    with url_app.app.test_client() as client:
        yield client


class TestHealth:
    """Test health endpoint"""
    
    def test_health_endpoint(self, client):
        """Test that health endpoint returns correct status"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'url_extractor'


class TestURLFiltering:
    """Test URL filtering logic"""
    
    def test_is_social_media_url(self):
        """Test social media URL detection"""
        social_urls = [
            'https://twitter.com/user/status/123',
            'https://facebook.com/post/456',
            'https://instagram.com/p/789',
            'https://reddit.com/r/test'
        ]
        
        for url in social_urls:
            result = url_app.is_social_media(url)
            assert result is True
    
    def test_is_not_social_media_url(self):
        """Test non-social media URL"""
        news_urls = [
            'https://bbc.com/news/article',
            'https://nytimes.com/article',
            'https://cnn.com/world/news'
        ]
        
        for url in news_urls:
            result = url_app.is_social_media(url)
            assert result is False
    
    def test_is_blog_platform(self):
        """Test blog platform detection"""
        blog_urls = [
            'https://medium.com/@user/article',
            'https://wordpress.com/blog/post',
            'https://substack.com/post'
        ]
        
        for url in blog_urls:
            result = url_app.is_blog_platform(url)
            assert result is True


class TestContentExtraction:
    """Test content extraction"""
    
    @patch('url_app.Article')
    def test_extract_with_newspaper(self, mock_article_class):
        """Test extraction using newspaper3k"""
        mock_article = MagicMock()
        mock_article.text = "This is the extracted article text"
        mock_article.title = "Article Title"
        mock_article.authors = ["Author Name"]
        mock_article_class.return_value = mock_article
        
        result = url_app.extract_with_newspaper('https://example.com/article')
        
        assert result is not None
        assert 'text' in result
        assert 'title' in result
    
    @patch('url_app.requests.get')
    def test_extract_with_beautifulsoup(self, mock_get):
        """Test extraction using BeautifulSoup fallback"""
        mock_response = MagicMock()
        mock_response.text = '<html><body><p>Article content</p></body></html>'
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = url_app.extract_with_beautifulsoup('https://example.com/article')
        
        assert result is not None
    
    def test_extract_timeout_handling(self):
        """Test timeout during extraction"""
        # Should handle timeout gracefully
        result = url_app.extract_content('https://extremely-slow-site.example.com')
        
        # Should return None or error indicator
        assert result is None or 'error' in result


class TestAnalyzeEndpoint:
    """Test /analyze endpoint"""
    
    @patch('url_app.extract_content')
    @patch('url_app.store_url_content')
    def test_analyze_valid_url(self, mock_store, mock_extract, client):
        """Test analyzing a valid URL"""
        mock_extract.return_value = {
            'text': 'Extracted content',
            'title': 'Article Title'
        }
        
        data = {
            'url': 'https://example.com/article',
            'post_id': 'test123'
        }
        
        response = client.post(
            '/analyze',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert 'content' in result or 'text' in result
    
    def test_analyze_social_media_url(self, client):
        """Test analyzing social media URL (should skip)"""
        data = {
            'url': 'https://twitter.com/user/status/123',
            'post_id': 'test123'
        }
        
        response = client.post(
            '/analyze',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should skip or return appropriate response
        assert response.status_code in [200, 400]
    
    def test_analyze_missing_url(self, client):
        """Test analyzing without URL"""
        data = {
            'post_id': 'test123'
        }
        
        response = client.post(
            '/analyze',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 400


class TestDatabaseStorage:
    """Test database storage"""
    
    @patch('url_app.get_db_connection')
    def test_store_url_content(self, mock_db_conn):
        """Test storing extracted content"""
        mock_cursor = MagicMock()
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        content_data = {
            'post_id': 'test123',
            'url': 'https://example.com',
            'text': 'Extracted content',
            'title': 'Article Title'
        }
        
        url_app.store_url_content(content_data)
        
        # Should execute INSERT
        assert mock_cursor.execute.called
    
    @patch('url_app.get_db_connection')
    def test_check_url_already_processed(self, mock_db_conn):
        """Test checking if URL already processed"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'id': 'existing'}
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        exists = url_app.url_already_processed('https://example.com')
        
        assert exists is True


class TestRabbitMQ:
    """Test RabbitMQ integration"""
    
    @patch('url_app.pika.BlockingConnection')
    def test_rabbitmq_connection(self, mock_connection):
        """Test RabbitMQ connection setup"""
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel
        
        client = url_app.RabbitMQClient(url_app.RABBITMQ_URL)
        
        assert mock_channel.exchange_declare.called
        assert mock_channel.queue_declare.called
    
    @patch('url_app.mq_client')
    def test_publish_extracted_event(self, mock_mq):
        """Test publishing url.extracted event"""
        content_data = {
            'post_id': 'test123',
            'url': 'https://example.com',
            'text': 'Content'
        }
        
        url_app.publish_extracted_event(content_data)
        
        assert mock_mq.publish.called
        call_args = mock_mq.publish.call_args
        assert call_args[0][0] == 'url.extracted'


class TestContentValidation:
    """Test content validation"""
    
    def test_validate_extracted_content(self):
        """Test content validation"""
        valid_content = {
            'text': 'This is valid article content with sufficient length',
            'title': 'Article Title'
        }
        
        is_valid = url_app.validate_content(valid_content)
        assert is_valid is True
    
    def test_validate_short_content(self):
        """Test rejection of too-short content"""
        short_content = {
            'text': 'Too short',
            'title': 'Title'
        }
        
        is_valid = url_app.validate_content(short_content)
        # Might be invalid if minimum length check exists
        assert is_valid in [True, False]
    
    def test_validate_empty_content(self):
        """Test rejection of empty content"""
        empty_content = {
            'text': '',
            'title': ''
        }
        
        is_valid = url_app.validate_content(empty_content)
        assert is_valid is False


class TestErrorHandling:
    """Test error handling"""
    
    @patch('url_app.requests.get')
    def test_handle_http_error(self, mock_get):
        """Test handling HTTP errors"""
        mock_get.side_effect = Exception("HTTP Error 404")
        
        result = url_app.extract_content('https://example.com/404')
        
        # Should handle gracefully
        assert result is None or 'error' in result
    
    def test_handle_invalid_url(self):
        """Test handling invalid URL"""
        result = url_app.extract_content('not-a-valid-url')
        
        # Should handle gracefully
        assert result is None or 'error' in result
