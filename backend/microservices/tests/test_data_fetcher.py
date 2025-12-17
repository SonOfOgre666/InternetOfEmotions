"""
Unit tests for Data Fetcher microservice
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add data-fetcher directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data-fetcher'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

@pytest.fixture
def app():
    """Create test Flask app"""
    with patch('database.SharedDatabase'), \
         patch('app.reddit'):
        import importlib
        import app as data_fetcher_app
        importlib.reload(data_fetcher_app)
        data_fetcher_app.app.config['TESTING'] = True
        yield data_fetcher_app.app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestHealthEndpoint:
    """Test health check"""
    
    def test_health(self, client):
        """Test health endpoint"""
        response = client.get('/health')
        assert response.status_code == 200


class TestFetchEndpoints:
    """Test Reddit fetching functionality"""
    
    @patch('app.store_raw_posts')
    @patch('app.search_regional_subreddits')
    def test_fetch_country_success(self, mock_search, mock_store, client):
        """Test successful country fetching"""
        mock_search.return_value = [
            {
                'post_id': 'test123',
                'text': 'Test post',
                'country': 'united states',
                'timestamp': '2025-12-12T10:00:00',
                'post_type': 'text',
                'media_url': None,
                'link_url': None,
                'needs_extraction': 0
            }
        ]
        mock_store.return_value = 1
        
        response = client.post('/fetch/country', json={'country': 'united states'})
        assert response.status_code == 200
        data = response.get_json()
        assert data['stored_count'] == 1
    
    def test_fetch_country_missing_param(self, client):
        """Test fetch without country parameter"""
        response = client.post('/fetch/country', json={})
        assert response.status_code == 400


class TestHelperFunctions:
    """Test helper functions"""
    
    def test_get_country_region(self):
        """Test country to region mapping"""
        import sys
        from unittest.mock import Mock, patch
        
        # Mock the database module before importing app
        mock_db = Mock()
        sys.modules['database'] = mock_db
        
        try:
            with patch('app.COUNTRY_TO_REGION', {'germany': 'europe', 'united states': 'americas'}):
                from app import get_country_region
                assert get_country_region('germany') == 'europe'
                assert get_country_region('united states') == 'americas'
                assert get_country_region('unknown') == 'worldnews'  # default
        finally:
            # Clean up
            if 'database' in sys.modules:
                del sys.modules['database']
    
    def test_search_regional_subreddits(self):
        """Test searching regional subreddits"""
        import sys
        from unittest.mock import Mock, patch
        
        # Mock the database module before importing app
        mock_db = Mock()
        sys.modules['database'] = mock_db
        
        try:
            with patch('app.reddit') as mock_reddit:
                
                # Mock Reddit objects
                mock_subreddit = Mock()
                mock_submission = Mock()
                mock_submission.id = 'test123'
                mock_submission.title = 'Test Title'
                mock_submission.selftext = 'Test content'
                import time
                mock_submission.created_utc = int(time.time())  # Recent
                mock_submission.is_self = True
                
                mock_search_results = [mock_submission]
                mock_subreddit.search.return_value = mock_search_results
                mock_reddit.subreddit.return_value = mock_subreddit
                
                with patch('app.REGION_SUBREDDITS', {'europe': ['worldnews']}):
                    from app import search_regional_subreddits
                    posts = search_regional_subreddits('germany', limit=10)
                    
                    assert len(posts) == 1
                    assert posts[0]['post_id'] == 'test123'
                    assert posts[0]['country'] == 'germany'
        finally:
            # Clean up
            if 'database' in sys.modules:
                del sys.modules['database']
    
    def test_classify_and_extract_post_text_only(self):
        """Test classifying text-only posts"""
        import sys
        from unittest.mock import Mock
        
        # Mock the database module before importing app
        mock_db = Mock()
        sys.modules['database'] = mock_db
        
        try:
            mock_submission = Mock()
            mock_submission.is_self = True
            mock_submission.selftext = 'This is a text post content'
            mock_submission.title = 'Test Title'
            mock_submission.id = 'test123'
            import time
            mock_submission.created_utc = int(time.time())
            
            from app import classify_and_extract_post
            result = classify_and_extract_post(mock_submission, 'usa')
            
            assert result is not None
            assert result['post_type'] == 'text'
            assert 'Test Title. This is a text post content' in result['text']
            assert result['needs_extraction'] == 0
        finally:
            # Clean up
            if 'database' in sys.modules:
                del sys.modules['database']
    
    def test_classify_and_extract_post_with_blog_link(self):
        """Test classifying posts with blog links"""
        import sys
        from unittest.mock import Mock
        
        # Mock the database module before importing app
        mock_db = Mock()
        sys.modules['database'] = mock_db
        
        try:
            mock_submission = Mock()
            mock_submission.is_self = True
            mock_submission.selftext = 'Check this article: https://bbc.com/news/test'
            mock_submission.title = 'News Title'
            mock_submission.id = 'test123'
            import time
            mock_submission.created_utc = int(time.time())
            
            from app import classify_and_extract_post
            result = classify_and_extract_post(mock_submission, 'uk')
            
            assert result is not None
            assert result['post_type'] == 'link'
            assert result['link_url'] == 'https://bbc.com/news/test'
            assert result['needs_extraction'] == 1
        finally:
            # Clean up
            if 'database' in sys.modules:
                del sys.modules['database']
    
    def test_classify_and_extract_post_link_post(self):
        """Test classifying external link posts"""
        import sys
        from unittest.mock import Mock, patch
        
        # Mock the database module before importing app
        mock_db = Mock()
        sys.modules['database'] = mock_db
        
        try:
            with patch('app.datetime') as mock_datetime:
                mock_datetime.fromtimestamp.return_value.isoformat.return_value = '2025-12-12T10:00:00'
                
                mock_submission = Mock()
                mock_submission.is_self = False
                mock_submission.url = 'https://cnn.com/article'
                mock_submission.title = 'Breaking News'
                mock_submission.id = 'test123'
                import time
                mock_submission.created_utc = int(time.time())
                mock_submission.permalink = '/r/news/test123'
                
                from app import classify_and_extract_post
                result = classify_and_extract_post(mock_submission, 'usa')
                
                assert result is not None
                assert result['post_type'] == 'link'
                assert result['link_url'] == 'https://cnn.com/article'
                assert result['needs_extraction'] == 1
        finally:
            # Clean up
            if 'database' in sys.modules:
                del sys.modules['database']
    
    def test_classify_and_extract_post_ignore_images(self):
        """Test ignoring image posts"""
        import sys
        from unittest.mock import Mock
        
        # Mock the database module before importing app
        mock_db = Mock()
        sys.modules['database'] = mock_db
        
        try:
            mock_submission = Mock()
            mock_submission.url = 'https://example.com/image.jpg'
            mock_submission.title = 'Image Post'
            mock_submission.selftext = ''
            mock_submission.is_self = False
            
            from app import classify_and_extract_post
            result = classify_and_extract_post(mock_submission, 'usa')
            assert result is None
        finally:
            # Clean up
            if 'database' in sys.modules:
                del sys.modules['database']
    
    def test_classify_and_extract_post_ignore_videos(self):
        """Test ignoring video posts"""
        import sys
        from unittest.mock import Mock
        
        # Mock the database module before importing app
        mock_db = Mock()
        sys.modules['database'] = mock_db
        
        try:
            mock_submission = Mock()
            mock_submission.url = 'https://v.redd.it/video'
            mock_submission.title = 'Video Post'
            mock_submission.selftext = ''
            mock_submission.is_self = False
            
            from app import classify_and_extract_post
            result = classify_and_extract_post(mock_submission, 'usa')
            assert result is None
        finally:
            # Clean up
            if 'database' in sys.modules:
                del sys.modules['database']
    
    def test_classify_and_extract_post_ignore_social_media(self):
        """Test ignoring social media links"""
        import sys
        from unittest.mock import Mock
        
        # Mock the database module before importing app
        mock_db = Mock()
        sys.modules['database'] = mock_db
        
        try:
            mock_submission = Mock()
            mock_submission.url = 'https://twitter.com/user/status/123'
            mock_submission.title = 'Social Media Post'
            mock_submission.selftext = ''
            mock_submission.is_self = False
            
            from app import classify_and_extract_post
            result = classify_and_extract_post(mock_submission, 'usa')
            assert result is None
        finally:
            # Clean up
            if 'database' in sys.modules:
                del sys.modules['database']
    
    @patch('app.db')
    def test_store_post_success(self, mock_db):
        """Test successful post storage"""
        from app import store_post
        
        mock_db.execute_commit.return_value = None
        
        post_data = {
            'post_id': 'test123',
            'text': 'Test post',
            'country': 'usa',
            'timestamp': '2025-12-12T10:00:00',
            'post_type': 'text',
            'media_url': None,
            'link_url': None,
            'needs_extraction': 0
        }
        
        result = store_post(post_data)
        assert result is True
        mock_db.execute_commit.assert_called_once()
    
    @patch('app.db')
    def test_store_post_failure(self, mock_db):
        """Test post storage failure"""
        from app import store_post
        
        mock_db.execute_commit.side_effect = Exception("DB Error")
        
        post_data = {
            'post_id': 'test123',
            'text': 'Test post',
            'country': 'usa',
            'timestamp': '2025-12-12T10:00:00'
        }
        
        result = store_post(post_data)
        assert result is False
    
    @patch('app.store_post')
    def test_store_raw_posts(self, mock_store_post):
        """Test storing multiple posts"""
        from app import store_raw_posts
        
        mock_store_post.return_value = True
        
        posts = [
            {'post_id': '1', 'text': 'Post 1'},
            {'post_id': '2', 'text': 'Post 2'},
            {'post_id': '3', 'text': 'Post 3'}
        ]
        
        stored_count = store_raw_posts(posts)
        assert stored_count == 3
        assert mock_store_post.call_count == 3


class TestRemainingEndpoints:
    """Test remaining Flask endpoints"""
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
        assert 'timestamp' in data
    
    @patch('app.search_regional_subreddits')
    @patch('app.store_raw_posts')
    def test_fetch_endpoint_success(self, mock_store, mock_search, client):
        """Test /fetch endpoint success"""
        mock_search.return_value = [
            {'post_id': '1', 'text': 'Post 1', 'country': 'usa', 'timestamp': '2025-12-12T10:00:00'},
            {'post_id': '2', 'text': 'Post 2', 'country': 'usa', 'timestamp': '2025-12-12T10:00:00'}
        ]
        mock_store.return_value = 2
        
        response = client.post('/fetch', json={'countries': ['usa'], 'limit': 10})
        assert response.status_code == 200
        data = response.get_json()
        assert data['fetched_count'] == 2
        assert data['stored_count'] == 2
    
    def test_fetch_endpoint_missing_country(self, client):
        """Test /fetch endpoint without country"""
        response = client.post('/fetch', json={'limit': 10})
        assert response.status_code == 400
    
    @patch('app.store_raw_posts')
    @patch('app.search_regional_subreddits')
    @patch('app.rotation')
    def test_fetch_next_batch_endpoint(self, mock_rotation, mock_search, mock_store, client):
        """Test /fetch/next-batch endpoint"""
        # Mock rotation to return countries batch (not posts)
        mock_rotation.get_next_batch.return_value = (['usa', 'uk'], 0, 2)
        
        # Mock search to return posts
        mock_search.return_value = [
            {'post_id': '1', 'text': 'Batch post 1', 'country': 'usa', 'timestamp': '2025-12-12T10:00:00'},
            {'post_id': '2', 'text': 'Batch post 2', 'country': 'usa', 'timestamp': '2025-12-12T10:00:00'}
        ]
        mock_store.return_value = 2
        
        response = client.post('/fetch/next-batch')
        assert response.status_code == 200
        data = response.get_json()
        assert 'batch' in data
        assert data['batch'] == ['usa', 'uk']
        assert data['cycle_number'] == 0
    
    @patch('app.db')
    @patch('app.rotation')
    def test_stats_endpoint(self, mock_rotation, mock_db, client):
        """Test /stats endpoint"""
        mock_rotation.get_stats.return_value = {
            'cycle_number': 5,
            'current_index': 100,
            'total_countries': 195,
            'progress_percent': 51.3,
            'countries_remaining': 95
        }
        mock_db.execute_query.return_value = [(250,)]
        
        response = client.get('/stats')
        assert response.status_code == 200
        data = response.get_json()
        assert data['cycle_number'] == 5
        assert data['current_index'] == 100
        assert data['total_raw_posts'] == 250


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @patch('app.store_raw_posts')
    @patch('app.search_regional_subreddits')
    def test_fetch_country_reddit_api_error(self, mock_search, mock_store, client):
        """Test handling Reddit API errors"""
        mock_search.side_effect = Exception("Reddit API Error")
        mock_store.return_value = 0
        
        response = client.post('/fetch/country', json={'country': 'usa'})
        assert response.status_code == 500
    
    @patch('app.store_raw_posts')
    @patch('app.search_regional_subreddits')
    def test_fetch_endpoint_storage_failure(self, mock_search, mock_store, client):
        """Test handling database storage failures"""
        mock_search.return_value = [
            {'post_id': '1', 'text': 'Post 1', 'country': 'usa', 'timestamp': '2025-12-12T10:00:00'}
        ]
        mock_store.return_value = 0  # Failed to store
        
        response = client.post('/fetch', json={'countries': ['usa']})
        assert response.status_code == 500
    
    @patch('app.rotation')
    def test_fetch_next_batch_rotation_error(self, mock_rotation, client):
        """Test handling rotation errors"""
        mock_rotation.get_next_batch.side_effect = Exception("Rotation Error")
        
        response = client.post('/fetch/next-batch')
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
    
    def test_invalid_json_request(self, client):
        """Test handling invalid JSON requests"""
        response = client.post('/fetch', data='invalid json')
        assert response.status_code == 400


class TestIntegration:
    """Integration tests for full workflows"""
    
    @patch('app.MAX_POST_AGE_DAYS', 28)
    @patch('app.REGION_SUBREDDITS', {'europe': ['worldnews']})
    @patch('app.COUNTRY_TO_REGION', {'germany': 'europe'})
    @patch('app.reddit')
    @patch('app.db')
    def test_full_reddit_fetch_workflow(self, mock_db, mock_reddit):
        """Test complete Reddit fetch to database storage workflow"""
        from app import search_regional_subreddits, store_raw_posts
        import time
        
        # Mock Reddit submission
        mock_submission = Mock()
        mock_submission.id = 'int123'
        mock_submission.title = 'Integration Test Post'
        mock_submission.selftext = 'This is a test post for integration testing purposes'
        mock_submission.created_utc = int(time.time())  # Recent timestamp
        mock_submission.url = 'https://reddit.com/r/test/int123'
        mock_submission.is_self = True
        
        # Mock subreddit search
        mock_subreddit = Mock()
        mock_subreddit.search.return_value = [mock_submission]
        mock_reddit.subreddit.return_value = mock_subreddit
        
        # Mock database
        mock_db.execute_commit.return_value = None
        
        # Step 1: Search for posts
        posts = search_regional_subreddits('germany', limit=5)
        assert len(posts) == 1
        assert posts[0]['post_id'] == 'int123'
        
        # Step 2: Store posts
        stored_count = store_raw_posts(posts)
        assert stored_count == 1
        
        # Verify database was called
        assert mock_db.execute_commit.call_count == 1
    
    def test_circular_rotation_integration(self):
        """Test CircularRotation class integration"""
        from app import CircularRotation
        
        # Create rotation with small country list
        countries = ['usa', 'uk', 'france']
        rotation = CircularRotation(countries)
        rotation.countries_per_batch = 2
        
        # Test batch retrieval
        batch, cycle, index = rotation.get_next_batch()
        assert len(batch) == 2
        assert batch == ['usa', 'uk']
        assert index == 2
        
        # Test stats
        stats = rotation.get_stats()
        assert stats['current_index'] == 2
        assert stats['total_countries'] == 3


class TestCircularRotation:
    """Test circular rotation functionality"""
    
    def test_rotation_initialization(self):
        """Test circular rotation init"""
        from app import CircularRotation
        countries = ['usa', 'uk', 'france']
        rotation = CircularRotation(countries)
        
        assert rotation.current_index == 0
        assert rotation.cycle_number == 0
        assert len(rotation.countries) == 3
    
    def test_rotation_get_next_batch(self):
        """Test getting next batch"""
        from app import CircularRotation
        countries = ['a', 'b', 'c', 'd', 'e']
        rotation = CircularRotation(countries)
        rotation.countries_per_batch = 2
        
        batch, cycle, index = rotation.get_next_batch()
        assert len(batch) == 2
        assert index == 2
    
    def test_rotation_wraps_around(self):
        """Test rotation wraps around at end"""
        from app import CircularRotation
        countries = ['a', 'b', 'c']
        rotation = CircularRotation(countries)
        rotation.countries_per_batch = 5
        
        batch, cycle, index = rotation.get_next_batch()
        assert cycle == 1  # Should have wrapped
        assert index == 2  # Should restart from beginning
    
    def test_rotation_get_stats(self):
        """Test getting rotation statistics"""
        from app import CircularRotation
        countries = ['a', 'b', 'c', 'd', 'e']
        rotation = CircularRotation(countries)
        rotation.current_index = 3
        rotation.cycle_number = 2
        
        stats = rotation.get_stats()
        assert stats['cycle_number'] == 2
        assert stats['current_index'] == 3
        assert stats['total_countries'] == 5
        assert stats['progress_percent'] == 60.0
        assert stats['countries_remaining'] == 2


@pytest.mark.requires_reddit
class TestRedditIntegration:
    """Integration tests requiring Reddit API"""
    
    @pytest.mark.skip(reason="Requires valid Reddit credentials")
    def test_real_reddit_fetch(self, client):
        """Test actual Reddit API call"""
        # This would require real credentials
        pass
