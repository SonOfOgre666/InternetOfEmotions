"""
Pytest configuration and fixtures for microservices tests
"""
import pytest
import os
import sys
from unittest.mock import MagicMock

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
# Add data-fetcher module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data-fetcher'))

@pytest.fixture
def mock_database():
    """Mock database connection"""
    from unittest.mock import Mock
    db = Mock()
    db.get_connection = Mock(return_value=Mock())
    return db

@pytest.fixture
def mock_reddit():
    """Mock Reddit API client"""
    reddit = MagicMock()
    reddit.user.me = MagicMock(return_value=None)
    return reddit

@pytest.fixture
def test_config():
    """Test configuration"""
    return {
        'DB_PATH': ':memory:',
        'REDDIT_CLIENT_ID': 'test_id',
        'REDDIT_CLIENT_SECRET': 'test_secret',
        'REDDIT_USER_AGENT': 'test_agent',
        'MAX_POST_AGE_DAYS': 28,
    }

@pytest.fixture
def sample_post():
    """Sample Reddit post data"""
    return {
        'id': 'test123',
        'text': 'This is a test post about exciting news!',
        'country': 'united states',
        'timestamp': '2025-12-12T10:00:00',
        'source': 'r/worldnews',
        'url': 'https://reddit.com/r/worldnews/test',
        'author': 'test_user',
        'score': 100,
        'num_comments': 25,
        'subreddit': 'worldnews',
        'coords': [40.7128, -74.0060]
    }

@pytest.fixture
def sample_country_data():
    """Sample country aggregation data"""
    return {
        'country': 'united states',
        'emotions': {
            'joy': 0.7,
            'sadness': 0.1,
            'anger': 0.1,
            'fear': 0.05,
            'surprise': 0.05
        },
        'top_emotion': 'joy',
        'total_posts': 50
    }
