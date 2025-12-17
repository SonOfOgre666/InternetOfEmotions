"""
Unit tests for ML Analyzer microservice
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add ml-analyzer directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ml-analyzer'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

@pytest.fixture
def app():
    """Create test Flask app"""
    with patch('database.SharedDatabase'):
        import app as ml_app
        ml_app.app.config['TESTING'] = True
        yield ml_app.app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestEmotionAnalyzer:
    """Test emotion analysis functionality"""
    
    def test_analyzer_initialization(self):
        """Test emotion analyzer initialization"""
        from app import EmotionAnalyzer
        with patch('app.pipeline'):
            analyzer = EmotionAnalyzer()
            assert analyzer is not None
    
    @patch('app.EmotionAnalyzer')
    def test_analyze_text_success(self, mock_analyzer, client):
        """Test successful text analysis"""
        mock_instance = Mock()
        mock_instance.analyze_full.return_value = {
            'emotion': {
                'top_emotion': 'joy',
                'confidence': 0.85,
                'all_emotions': {'joy': 0.85, 'sadness': 0.15}
            },
            'is_collective': True
        }
        mock_analyzer.return_value = mock_instance
        
        response = client.post('/analyze', json={'text': 'I am so happy!'})
        assert response.status_code == 200
    
    def test_analyze_missing_text(self, client):
        """Test analysis without text"""
        response = client.post('/analyze', json={})
        assert response.status_code == 400


class TestBatchProcessing:
    """Test batch analysis functionality"""
    
    @patch('app.db')
    @patch('app.analyzer')
    def test_process_pending_posts(self, mock_analyzer, mock_db, client):
        """Test processing pending events"""
        # Mock database responses
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('id1', 'Event Title', 'Event description', 'usa', '2025-12-12T10:00:00', '["post1"]')
        ]
        mock_cursor.execute.return_value = None
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.commit.return_value = None
        mock_db.get_connection.return_value = mock_conn
        
        # Mock analyzer
        mock_analyzer.analyze_full.return_value = {
            'emotion': {
                'top_emotion': 'joy',
                'confidence': 0.9
            },
            'is_collective': True
        }
        
        response = client.post('/process/pending')
        assert response.status_code == 200
        data = response.get_json()
        assert data['processed'] == 1


@pytest.mark.requires_ml
class TestMLModelIntegration:
    """Integration tests requiring ML models"""
    
    @pytest.mark.skip(reason="Requires ML models downloaded")
    def test_real_ml_inference(self):
        """Test actual ML model inference"""
        from app import EmotionAnalyzer
        analyzer = EmotionAnalyzer()
        result = analyzer.analyze_emotion("I am very excited about this!")
        assert result['top_emotion'] in ['joy', 'surprise']
        assert 0 <= result['confidence'] <= 1
