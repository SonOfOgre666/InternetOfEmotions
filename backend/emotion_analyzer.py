from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import torch
from transformers import pipeline

class EmotionAnalyzer:
    """
    Multi-model emotion analyzer combining:
    1. Hugging Face RoBERTa-based emotion classification (Pre-trained ML model)
    2. VADER sentiment analysis
    3. TextBlob sentiment analysis
    4. Keyword-based detection
    """

    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        
        # Initialize pre-trained emotion classifier (RoBERTa-based)
        print("🤖 Loading pre-trained emotion classification model (j-hartmann/emotion-english-distilroberta-base)...")
        try:
            self.emotion_classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                device=0 if torch.cuda.is_available() else -1  # GPU if available
            )
            self.ml_model_available = True
            print("✓ ML emotion classifier loaded successfully")
        except Exception as e:
            print(f"⚠ ML emotion classifier failed to load: {e}")
            self.emotion_classifier = None
            self.ml_model_available = False

        # Emotion keywords dictionary
        self.emotion_keywords = {
            'joy': ['happy', 'joy', 'excited', 'amazing', 'wonderful', 'great', 'love', 'awesome',
                   'fantastic', 'excellent', 'brilliant', 'perfect', 'beautiful', 'delighted',
                   '😊', '😄', '😃', '🎉', '❤️', '🥰', '😍', '🎊'],
            'sadness': ['sad', 'depressed', 'unhappy', 'miserable', 'crying', 'tears', 'awful',
                       'terrible', 'horrible', 'disappointed', 'heartbroken', 'lonely', 'hurt',
                       '😢', '😭', '😞', '☹️', '💔'],
            'anger': ['angry', 'mad', 'furious', 'rage', 'hate', 'annoyed', 'frustrated',
                     'irritated', 'outraged', 'pissed', 'disgusted', 'livid',
                     '😠', '😡', '🤬', '😤'],
            'fear': ['scared', 'afraid', 'terrified', 'fear', 'worried', 'anxious', 'nervous',
                    'panic', 'frightened', 'alarmed', 'concerned', 'stress',
                    '😨', '😰', '😱', '😧'],
            'surprise': ['surprised', 'shock', 'amazed', 'astonished', 'wow', 'omg', 'unbelievable',
                        'unexpected', 'stunning', 'incredible', 'mind-blowing',
                        '😮', '😲', '🤯', '😳'],
        }

    def detect_keywords(self, text):
        """Detect emotion based on keywords"""
        text_lower = text.lower()
        emotion_scores = {emotion: 0 for emotion in self.emotion_keywords}

        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    emotion_scores[emotion] += 1

        max_score = max(emotion_scores.values())
        if max_score > 0:
            return max(emotion_scores.items(), key=lambda x: x[1])[0], max_score / 10
        return None, 0

    def analyze_vader(self, text):
        """Analyze sentiment using VADER"""
        scores = self.vader.polarity_scores(text)

        # Map VADER scores to emotions
        if scores['compound'] >= 0.5:
            return 'joy', scores['compound']
        elif scores['compound'] <= -0.5:
            if scores['neg'] > 0.3:
                return 'anger', abs(scores['compound'])
            else:
                return 'sadness', abs(scores['compound'])
        elif scores['neu'] > 0.7:
            return 'neutral', scores['neu']
        else:
            return 'neutral', 0.5

    def analyze_textblob(self, text):
        """Analyze sentiment using TextBlob"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            if polarity >= 0.3:
                return 'joy', polarity
            elif polarity <= -0.3:
                return 'sadness', abs(polarity)
            else:
                return 'neutral', 0.5
        except:
            return 'neutral', 0.5

    def analyze(self, text):
        """
        Comprehensive emotion analysis combining 4 methods:
        1. ML Model (Pre-trained RoBERTa-based classifier) - MOST ACCURATE
        2. Keyword detection
        3. VADER sentiment analysis
        4. TextBlob sentiment analysis
        
        Returns: dict with emotion, confidence, and details
        """
        if not text or len(text.strip()) < 3:
            return {
                'emotion': 'neutral',
                'confidence': 0.0,
                'method': 'default'
            }

        # Method 0: ML-based emotion classification (HIGHEST PRIORITY - Most Accurate)
        ml_emotion = None
        ml_confidence = 0.0
        if self.ml_model_available:
            try:
                # Truncate text to 512 tokens (RoBERTa max)
                text_truncated = text[:512]
                ml_result = self.emotion_classifier(text_truncated)
                # ml_result is a list: [{'label': 'emotion', 'score': confidence}]
                ml_emotion = ml_result[0]['label']
                ml_confidence = ml_result[0]['score']
            except Exception as e:
                pass  # Fall back to other methods

        # Method 1: Keyword detection
        keyword_emotion, keyword_confidence = self.detect_keywords(text)

        # Method 2: VADER analysis
        vader_emotion, vader_confidence = self.analyze_vader(text)

        # Method 3: TextBlob analysis
        textblob_emotion, textblob_confidence = self.analyze_textblob(text)

        # Combine results with weighted average
        emotions = {}

        # ML model gets highest weight (3x) - most accurate pre-trained model
        if ml_emotion:
            emotions[ml_emotion] = emotions.get(ml_emotion, 0) + ml_confidence * 3.0

        # Keyword detection (2x weight)
        if keyword_emotion:
            emotions[keyword_emotion] = emotions.get(keyword_emotion, 0) + keyword_confidence * 2.0

        # VADER (1x weight)
        emotions[vader_emotion] = emotions.get(vader_emotion, 0) + vader_confidence * 1.0

        # TextBlob (0.8x weight)
        emotions[textblob_emotion] = emotions.get(textblob_emotion, 0) + textblob_confidence * 0.8

        # Determine final emotion
        if emotions:
            final_emotion = max(emotions.items(), key=lambda x: x[1])
            
            # Normalize confidence: if ML model participated, use its confidence, else average
            if ml_emotion:
                confidence = ml_confidence  # Use ML model's confidence (most reliable)
            else:
                confidence = min(final_emotion[1] / 4, 1.0)  # Average of all methods

            return {
                'emotion': final_emotion[0],
                'confidence': round(confidence, 2),
                'method': 'combined_with_ml' if ml_emotion else 'combined_without_ml',
                'details': {
                    'ml_model': {'emotion': ml_emotion, 'confidence': round(ml_confidence, 2)} if ml_emotion else None,
                    'keyword': keyword_emotion,
                    'vader': vader_emotion,
                    'textblob': textblob_emotion
                }
            }

        return {
            'emotion': 'neutral',
            'confidence': 0.5,
            'method': 'fallback'
        }

# Test function
if __name__ == '__main__':
    analyzer = EmotionAnalyzer()

    test_texts = [
        "I'm so happy and excited about this amazing news!",
        "This is terrible. I'm so angry about what happened.",
        "Feeling really sad and lonely today.",
        "Wow! I can't believe this is happening!",
        "I'm worried and scared about the future.",
        "The weather is nice today."
    ]

    print("Emotion Analysis Tests:\n")
    for text in test_texts:
        result = analyzer.analyze(text)
        print(f"Text: {text}")
        print(f"Emotion: {result['emotion'].upper()} (confidence: {result['confidence']})")
        print(f"Details: {result['details']}\n")
