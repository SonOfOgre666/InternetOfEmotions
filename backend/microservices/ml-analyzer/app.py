"""
ML Analyzer Microservice
Emotion analysis for text posts
No collective filtering needed - all posts from news subreddits
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import os
import sys
import json

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from database import SharedDatabase
from config import DB_PATH
from metrics import get_metrics, track_request_metrics, track_processing_time

# Initialize Sentry for error tracking
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

SENTRY_DSN = os.getenv('SENTRY_DSN', '')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,
        environment=os.getenv('ENVIRONMENT', 'production'),
        release=os.getenv('VERSION', '1.0.0')
    )

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Optional heavy ML dependencies: handle absence gracefully for test environments
try:
    import torch
except Exception:
    torch = None

try:
    from transformers import pipeline
except Exception:
    # Provide a placeholder so tests can patch `pipeline` without import errors
    pipeline = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize database
db = SharedDatabase(DB_PATH)


class EmotionAnalyzer:
    """Emotion analysis using RoBERTa + VADER fallback"""

    def __init__(self):
        logger.info("🔥 Loading emotion analysis model...")
        
        self.vader = SentimentIntensityAnalyzer()
        
        # Emotion Analysis (RoBERTa)
        logger.info("  Loading emotion model...")
        try:
            # Ensure pipeline exists and create with CPU if torch unavailable
            device = -1
            if torch is not None:
                try:
                    device = 0 if getattr(torch, 'cuda', None) and torch.cuda.is_available() else -1
                except Exception:
                    device = -1

            if pipeline is None:
                raise RuntimeError("Transformers pipeline not available")

            self.emotion_classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                device=device
            )
            self.emotion_available = True
            logger.info("  ✓ Emotion model loaded (~500MB)")
        except (OSError, ValueError, RuntimeError) as e:
            logger.warning(f"  ⚠️ Emotion model failed to load: {e}")
            self.emotion_classifier = None
            self.emotion_available = False
        except Exception as e:
            logger.error(f"  ❌ Unexpected error loading model: {e}")
            self.emotion_classifier = None
            self.emotion_available = False

        if self.emotion_available:
            logger.info("✓ Emotion model loaded successfully")
            logger.info("💾 Total memory: ~500MB")
        else:
            logger.warning("⚠️ Emotion model unavailable - using VADER fallback only")
        logger.info("ℹ️  No collective filtering - all posts from news subreddits are collective by nature")

    def analyze_emotion(self, text):
        """Analyze text emotion using RoBERTa or fallback methods"""
        try:
            if self.emotion_available and text and len(text) > 10:
                results = self.emotion_classifier(text[:512])

                if results and len(results) > 0:
                    emotions_dict = {}
                    # Pipeline returns a list of dicts like [{'label': 'joy', 'score': 0.99}, ...]
                    for item in results:
                        if isinstance(item, dict) and 'label' in item and 'score' in item:
                            emotions_dict[item['label']] = round(item['score'], 3)

                    if emotions_dict:
                        # Get top emotion
                        top_emotion = max(emotions_dict.items(), key=lambda x: x[1])[0]
                        confidence = emotions_dict[top_emotion]

                        return {
                            'top_emotion': top_emotion,
                            'confidence': round(confidence, 2),
                            'all_emotions': emotions_dict
                        }
        except (ValueError, KeyError) as e:
            logger.error(f"Data format error in emotion analysis: {e}")
        except RuntimeError as e:
            logger.error(f"Model runtime error: {e}")
        except Exception as e:
            logger.exception(f"Unexpected emotion analysis error: {e}")
        
        # Fallback to VADER
        try:
            vader_scores = self.vader.polarity_scores(text)
            
            # Map VADER to emotions
            if vader_scores['compound'] >= 0.5:
                return {'top_emotion': 'joy', 'confidence': 0.6, 'all_emotions': {'joy': 0.6}}
            elif vader_scores['compound'] <= -0.5:
                return {'top_emotion': 'sadness', 'confidence': 0.6, 'all_emotions': {'sadness': 0.6}}
            else:
                return {'top_emotion': 'neutral', 'confidence': 0.5, 'all_emotions': {'neutral': 0.5}}
        except Exception as e:
            logger.error(f"VADER fallback error: {e}")
            return {'top_emotion': 'neutral', 'confidence': 0.3, 'all_emotions': {'neutral': 0.3}}

    def analyze_full(self, text):
        """Analyze emotion only (all news posts are collective by nature)"""
        emotion_result = self.analyze_emotion(text)
        
        return {
            'emotion': emotion_result,
            'is_collective': True  # All posts from news subreddits are collective
        }


# Initialize analyzer
analyzer = EmotionAnalyzer()


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'ml-analyzer',
        'emotion_available': analyzer.emotion_available,
        'note': 'All posts are collective (news subreddits only)'
    })


@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    from flask import Response
    metrics_data, content_type = get_metrics()
    return Response(metrics_data, mimetype=content_type)


@app.route('/analyze', methods=['POST'])
@track_request_metrics
def analyze():
    """Analyze a single post"""
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    result = analyzer.analyze_full(text)
    return jsonify(result)


@app.route('/process/pending', methods=['POST'])
def process_pending():
    """Process all pending events (emotion analysis)"""
    batch_size = request.json.get('batch_size', 100) if request.json else 100
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get events that need emotion analysis
        cursor.execute("""
            SELECT id, title, description, country, event_date, post_ids
            FROM events 
            WHERE is_analyzed = 0
            LIMIT ?
        """, (batch_size,))
        
        events = cursor.fetchall()
        
        if not events:
            return jsonify({'message': 'No pending events', 'processed': 0})
        
        processed = 0
        for event_id, title, description, country, event_date, post_ids in events:
            try:
                # Analyze event description for emotion
                # Description now contains T5-generated summary from event-extractor
                # This summary intelligently combines title + body + blog content
                combined_text = f"{title}. {description}"
                analysis = analyzer.analyze_full(combined_text)
                
                # Update event with emotion data
                cursor.execute('''
                    UPDATE events
                    SET emotion = ?, confidence = ?, is_analyzed = 1
                    WHERE id = ?
                ''', (
                    analysis['emotion']['top_emotion'],
                    analysis['emotion']['confidence'],
                    event_id
                ))
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error analyzing event {event_id}: {e}")
                continue
        
        conn.commit()
        logger.info(f"✅ Processed {processed}/{len(events)} events")
        
        return jsonify({
            'success': True,
            'processed': processed,
            'total': len(events)
        })
        
    except Exception as e:
        logger.error(f"Process error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/stats', methods=['GET'])
def stats():
    """Get processing statistics"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        total_events = cursor.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        analyzed_events = cursor.execute("SELECT COUNT(*) FROM events WHERE is_analyzed = 1").fetchone()[0]
        pending = total_events - analyzed_events
        
        return jsonify({
            'total_events': total_events,
            'analyzed_events': analyzed_events,
            'pending_analysis': pending
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5005))
    app.run(host='0.0.0.0', port=port, debug=False)
