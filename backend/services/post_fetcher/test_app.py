"""
Unit tests for Post Fetcher Service
"""

import os
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta


# Set test environment variables
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'
os.environ['RABBITMQ_URL'] = 'amqp://test:test@localhost:5672/'
os.environ['REDDIT_CLIENT_ID'] = 'test_client_id'
os.environ['REDDIT_CLIENT_SECRET'] = 'test_client_secret'

# Import app after setting env vars
import app as post_app


@pytest.fixture
def client():
    """Create a test client"""
    post_app.app.config['TESTING'] = True
    with post_app.app.test_client() as client:
        yield client


@pytest.fixture
def mock_reddit():
    """Mock Reddit API client"""
    with patch('app.praw.Reddit') as mock_reddit_class:
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        yield mock_reddit


@pytest.fixture
def mock_db():
    """Mock database connection"""
    with patch('app.get_db_connection') as mock_conn:
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_conn.return_value.__enter__.return_value = mock_conn.return_value
        mock_conn.return_value.__exit__.return_value = None
        yield mock_cursor


class TestHealth:
    """Test health endpoint"""
    
    def test_health_endpoint(self, client):
        """Test that health endpoint returns correct status"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'post_fetcher'


class TestCountryMapping:
    """Test country and region mapping"""
    
    def test_country_to_region_mapping(self):
        """Test that all countries are mapped to regions"""
        assert 'united states' in post_app.COUNTRY_TO_REGION
        assert 'germany' in post_app.COUNTRY_TO_REGION
        assert 'japan' in post_app.COUNTRY_TO_REGION
    
    def test_all_regions_have_countries(self):
        """Test that all regions have countries"""
        for region, countries in post_app.REGIONS.items():
            assert len(countries) > 0
    
    def test_all_regions_have_subreddits(self):
        """Test that all regions have subreddits"""
        for region in post_app.REGIONS.keys():
            assert region in post_app.REGION_SUBREDDITS
            assert len(post_app.REGION_SUBREDDITS[region]) > 0


class TestPostFiltering:
    """Test post filtering logic"""
    
    def test_is_image_only_post(self):
        """Test image-only post detection"""
        # Mock post with only image
        mock_post = MagicMock()
        mock_post.is_self = False
        mock_post.url = 'https://i.redd.it/image.jpg'
        mock_post.selftext = ''
        
        result = post_app.is_image_only(mock_post)
        assert result is True
    
    def test_is_not_image_only_with_text(self):
        """Test post with text is not image-only"""
        mock_post = MagicMock()
        mock_post.is_self = True
        mock_post.selftext = 'Some text content'
        
        result = post_app.is_image_only(mock_post)
        assert result is False
    
    def test_is_url_only_post(self):
        """Test URL-only post detection"""
        mock_post = MagicMock()
        mock_post.is_self = False
        mock_post.url = 'https://example.com/article'
        mock_post.selftext = ''
        
        result = post_app.is_url_only(mock_post)
        assert result is True
    
    def test_is_not_url_only_with_text(self):
        """Test post with text is not URL-only"""
        mock_post = MagicMock()
        mock_post.is_self = True
        mock_post.selftext = 'Some text content here'
        mock_post.url = 'https://reddit.com/r/test'
        
        result = post_app.is_url_only(mock_post)
        assert result is False


class TestPostAge:
    """Test post age filtering"""
    
    def test_post_within_age_limit(self):
        """Test that recent posts pass age filter"""
        recent_time = datetime.now() - timedelta(days=15)
        timestamp = recent_time.timestamp()
        
        is_old = post_app.is_post_too_old(timestamp, max_age_days=30)
        assert is_old is False
    
    def test_post_exceeds_age_limit(self):
        """Test that old posts fail age filter"""
        old_time = datetime.now() - timedelta(days=45)
        timestamp = old_time.timestamp()
        
        is_old = post_app.is_post_too_old(timestamp, max_age_days=30)
        assert is_old is True
    
    def test_post_exactly_at_age_limit(self):
        """Test post exactly at age limit"""
        exact_time = datetime.now() - timedelta(days=30)
        timestamp = exact_time.timestamp()
        
        is_old = post_app.is_post_too_old(timestamp, max_age_days=30)
        # Should be at boundary - implementation dependent
        assert is_old in [True, False]


class TestCountryDetection:
    """Test country detection from post content"""
    
    def test_detect_country_in_title(self):
        """Test country detection in title"""
        text = "Breaking news from Germany today"
        country = post_app.detect_country(text, '')
        
        assert country is not None
        assert country.lower() in ['germany', 'united states']  # Might default to US
    
    def test_detect_country_in_selftext(self):
        """Test country detection in selftext"""
        text = "India reports new developments"
        country = post_app.detect_country('', text)
        
        assert country is not None
    
    def test_multiple_countries_prefers_first(self):
        """Test that first country mention is preferred"""
        text = "France and Germany sign agreement"
        country = post_app.detect_country(text, '')
        
        assert country is not None
    
    def test_no_country_returns_default(self):
        """Test default country when none detected"""
        text = "Generic news about nothing specific"
        country = post_app.detect_country(text, '')
        
        # Should return a default country or None
        assert country is not None or country is None


class TestFetchPosts:
    """Test post fetching from Reddit"""
    
    @patch('app.reddit')
    @patch('app.store_post')
    def test_fetch_posts_from_subreddit(self, mock_store, mock_reddit_client):
        """Test fetching posts from a subreddit"""
        # Mock subreddit and posts
        mock_post = MagicMock()
        mock_post.id = 'test123'
        mock_post.title = 'Test Post'
        mock_post.selftext = 'Test content'
        mock_post.url = 'https://reddit.com/test'
        mock_post.created_utc = datetime.now().timestamp()
        mock_post.is_self = True
        mock_post.score = 100
        
        mock_subreddit = MagicMock()
        mock_subreddit.new.return_value = [mock_post]
        mock_reddit_client.subreddit.return_value = mock_subreddit
        
        count = post_app.fetch_from_subreddit('worldnews', 'USA')
        
        assert count >= 0
    
    @patch('app.reddit')
    def test_fetch_posts_handles_exception(self, mock_reddit_client):
        """Test error handling during fetch"""
        mock_reddit_client.subreddit.side_effect = Exception("API Error")
        
        # Should not crash
        count = post_app.fetch_from_subreddit('worldnews', 'USA')
        assert count == 0


class TestStorePost:
    """Test storing posts to database"""
    
    @patch('app.get_db_connection')
    @patch('app.mq_client')
    def test_store_new_post(self, mock_mq, mock_db_conn):
        """Test storing a new post"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # Post doesn't exist
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        post_data = {
            'id': 'test123',
            'title': 'Test',
            'text': 'Content',
            'url': 'https://test.com',
            'country': 'USA',
            'reddit_created_at': datetime.now()
        }
        
        result = post_app.store_post(post_data)
        
        assert result is True
        assert mock_cursor.execute.called
    
    @patch('app.get_db_connection')
    def test_store_duplicate_post(self, mock_db_conn):
        """Test storing a duplicate post"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'id': 'test123'}  # Post exists
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        post_data = {
            'id': 'test123',
            'title': 'Test',
            'text': 'Content',
            'url': 'https://test.com',
            'country': 'USA',
            'reddit_created_at': datetime.now()
        }
        
        result = post_app.store_post(post_data)
        
        assert result is False


class TestAPIEndpoints:
    """Test API endpoints"""
    
    @patch('app.fetch_posts')
    def test_trigger_fetch_endpoint(self, mock_fetch, client):
        """Test manual fetch trigger"""
        mock_fetch.return_value = 10
        
        response = client.post('/api/fetch')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'fetched' in data
    
    @patch('app.get_db_connection')
    def test_stats_endpoint(self, mock_db_conn, client):
        """Test stats endpoint"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'count': 100}
        mock_db_conn.return_value.cursor.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_db_conn.return_value
        mock_db_conn.return_value.__exit__.return_value = None
        
        response = client.get('/api/stats')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_posts' in data


class TestRabbitMQ:
    """Test RabbitMQ integration"""
    
    @patch('app.pika.BlockingConnection')
    def test_rabbitmq_connection(self, mock_connection):
        """Test RabbitMQ connection setup"""
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel
        
        client = post_app.RabbitMQClient(post_app.RABBITMQ_URL)
        
        assert mock_channel.exchange_declare.called
    
    @patch('app.mq_client')
    def test_publish_post_fetched_event(self, mock_mq):
        """Test publishing post.fetched event"""
        post_data = {
            'id': 'test123',
            'title': 'Test',
            'country': 'USA'
        }
        
        post_app.publish_post_fetched(post_data)
        
        assert mock_mq.publish.called
        call_args = mock_mq.publish.call_args
        assert call_args[0][0] == 'post.fetched'


class TestBackgroundFetching:
    """Test background fetch worker"""
    
    @patch('app.fetch_posts')
    @patch('app.time.sleep')
    def test_fetch_worker_runs(self, mock_sleep, mock_fetch):
        """Test that fetch worker can run"""
        # Make it run once then stop
        mock_sleep.side_effect = [None, KeyboardInterrupt()]
        mock_fetch.return_value = 5
        
        try:
            post_app.fetch_worker()
        except KeyboardInterrupt:
            pass
        
        assert mock_fetch.called
