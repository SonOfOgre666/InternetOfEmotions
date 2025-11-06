"""
Collective Intelligence Analyzer
Determines if posts represent individual feelings or collective/country-level issues
Uses ML/NLP models for accurate classification
"""

import re
from typing import Dict, List
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import numpy as np
import torch
from transformers import pipeline

class CollectiveAnalyzer:
    """
    Analyzes posts to determine if they represent:
    1. Personal/individual issues (filter out)
    2. Collective issues affecting many people (keep)
    
    Uses zero-shot classification for intelligent detection
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)
        )

        # Initialize zero-shot classifier for collective vs personal detection
        print("🤖 Loading collective intelligence classifier...")
        try:
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",  # Strong zero-shot model
                device=0 if torch.cuda.is_available() else -1
            )
            self.ml_available = True
            print("✓ Collective intelligence classifier loaded successfully")
        except Exception as e:
            print(f"⚠ ML classifier failed to load: {e}")
            print("  Falling back to keyword-based detection")
            self.classifier = None
            self.ml_available = False

        # Fallback: Keywords for when ML model unavailable
        self.personal_indicators = [
            'my', 'i am', 'i\'m', 'my life', 'my problem', 'my situation',
            'i feel', 'i think', 'personally', 'my family', 'my friend',
            'my job', 'my boss', 'my relationship', 'my wife', 'my husband'
        ]

        self.collective_indicators = [
            'we', 'us', 'our', 'people', 'everyone', 'many', 'most',
            'all of us', 'citizens', 'population', 'community', 'society',
            'country', 'nation', 'government', 'crisis', 'emergency',
            'widespread', 'epidemic', 'shortage', 'conflict', 'war'
        ]

        self.collective_topics = [
            'war', 'conflict', 'crisis', 'disaster', 'emergency',
            'shortage', 'scarcity', 'inflation', 'unemployment',
            'protest', 'election', 'policy', 'law', 'regulation',
            'epidemic', 'pandemic', 'outbreak', 'violence', 'terrorism',
            'corruption', 'scandal', 'infrastructure', 'water crisis',
            'power outage', 'fuel shortage', 'food shortage'
        ]

    def analyze_post(self, text: str) -> Dict:
        """
        Analyze if a post represents personal or collective issue
        
        Uses ML model (primary) with keyword fallback (secondary)
        
        Returns: {
            'is_collective': bool,
            'collective_score': float (0-1),
            'reason': str,
            'method': str
        }
        """
        if not text or len(text.strip()) < 10:
            return {
                'is_collective': False,
                'collective_score': 0.0,
                'reason': 'Text too short',
                'method': 'validation'
            }

        # Try ML-based classification first (more accurate)
        if self.ml_available:
            return self._analyze_with_ml(text)
        else:
            # Fallback to keyword-based
            return self._analyze_with_keywords(text)

    def _analyze_with_ml(self, text: str) -> Dict:
        """
        Use zero-shot classification to determine if post is collective
        
        This is much more accurate than keyword matching!
        """
        try:
            # Define candidate labels for classification
            candidate_labels = [
                "collective social issue affecting many people",
                "personal individual problem or feeling",
                "country-level crisis or emergency",
                "private family or relationship matter"
            ]
            
            # Truncate text to 512 tokens (model limit)
            text_truncated = text[:512]
            
            # Classify
            result = self.classifier(
                text_truncated,
                candidate_labels,
                multi_label=False
            )
            
            # Get scores for collective vs personal
            labels = result['labels']
            scores = result['scores']
            
            # Calculate collective score
            collective_score = 0.0
            for label, score in zip(labels, scores):
                if 'collective' in label.lower() or 'country-level' in label.lower():
                    collective_score += score
                elif 'personal' in label.lower() or 'private' in label.lower():
                    collective_score -= score * 0.5  # Penalize personal
            
            # Normalize to 0-1
            collective_score = max(0, min(1, (collective_score + 0.5)))
            
            is_collective = collective_score >= 0.5
            
            return {
                'is_collective': is_collective,
                'collective_score': round(collective_score, 2),
                'reason': f"ML classified as: {labels[0]}",
                'method': 'zero-shot-classification',
                'top_label': labels[0],
                'confidence': round(scores[0], 2)
            }
            
        except Exception as e:
            print(f"ML classification error: {e}")
            # Fallback to keywords
            return self._analyze_with_keywords(text)

    def _analyze_with_keywords(self, text: str) -> Dict:
        """
        Fallback keyword-based analysis when ML model unavailable
        """
        text_lower = text.lower()

        # Score based on indicators
        personal_score = sum(1 for indicator in self.personal_indicators if indicator in text_lower)
        collective_score = sum(1 for indicator in self.collective_indicators if indicator in text_lower)

        # Check for collective topics
        topic_score = sum(1 for topic in self.collective_topics if topic in text_lower)

        # Calculate final score
        total_score = (collective_score + topic_score * 2) - personal_score

        # Normalize to 0-1
        normalized_score = max(0, min(1, total_score / 10))

        # Determine if collective
        is_collective = normalized_score >= 0.3

        reason = self._get_reason(personal_score, collective_score, topic_score)

        return {
            'is_collective': is_collective,
            'collective_score': normalized_score,
            'reason': reason,
            'method': 'keyword-based',
            'personal_indicators': personal_score,
            'collective_indicators': collective_score,
            'topic_indicators': topic_score
        }

    def cluster_posts(self, posts: List[str], min_cluster_size: int = 5) -> List[List[int]]:
        """
        Cluster similar posts to find common themes
        Returns: List of clusters (each cluster is list of post indices)
        """
        if len(posts) < min_cluster_size:
            return []

        try:
            # Convert posts to TF-IDF vectors
            vectors = self.vectorizer.fit_transform(posts)

            # Cluster using DBSCAN
            clustering = DBSCAN(eps=0.3, min_samples=min_cluster_size, metric='cosine')
            labels = clustering.fit_predict(vectors.toarray())

            # Group posts by cluster
            clusters = defaultdict(list)
            for idx, label in enumerate(labels):
                if label != -1:  # -1 means noise/outliers
                    clusters[label].append(idx)

            return list(clusters.values())

        except Exception as e:
            print(f"Error clustering posts: {e}")
            return []

    def detect_collective_patterns(self, posts: List[Dict], min_pattern_size: int = 5) -> List[Dict]:
        """
        Detect patterns indicating collective issues
        Returns: List of detected patterns with metadata
        """
        if len(posts) < min_pattern_size:
            return []

        # Extract texts
        texts = [post['text'] for post in posts]

        # Cluster posts
        clusters = self.cluster_posts(texts, min_cluster_size=min_pattern_size)

        patterns = []
        for cluster_indices in clusters:
            if len(cluster_indices) >= min_pattern_size:
                # Extract common keywords
                cluster_texts = [texts[i] for i in cluster_indices]
                keywords = self._extract_keywords(cluster_texts)

                # Get dominant emotion
                emotions = [posts[i]['emotion'] for i in cluster_indices]
                emotion_counts = Counter(emotions)
                dominant_emotion = emotion_counts.most_common(1)[0][0]

                patterns.append({
                    'cluster_id': len(patterns),
                    'post_indices': cluster_indices,
                    'size': len(cluster_indices),
                    'keywords': keywords[:10],
                    'dominant_emotion': dominant_emotion,
                    'emotion_distribution': dict(emotion_counts),
                    'is_collective': True
                })

        return patterns

    def _extract_keywords(self, texts: List[str]) -> List[str]:
        """Extract common keywords from texts"""
        try:
            vectorizer = TfidfVectorizer(max_features=20, stop_words='english')
            vectors = vectorizer.fit_transform(texts)

            # Get feature names (keywords)
            keywords = vectorizer.get_feature_names_out()

            # Calculate average TF-IDF scores
            avg_scores = np.asarray(vectors.mean(axis=0)).flatten()

            # Sort by score
            keyword_scores = list(zip(keywords, avg_scores))
            keyword_scores.sort(key=lambda x: x[1], reverse=True)

            return [kw for kw, score in keyword_scores]

        except Exception as e:
            print(f"Error extracting keywords: {e}")
            return []

    def _get_reason(self, personal_score: int, collective_score: int, topic_score: int) -> str:
        """Get human-readable reason for classification"""
        if topic_score >= 2:
            return "Contains collective issue topics"
        elif collective_score > personal_score:
            return "Uses collective language"
        elif personal_score > collective_score:
            return "Personal/individual issue"
        else:
            return "Neutral classification"


# Test
if __name__ == '__main__':
    analyzer = CollectiveAnalyzer()

    test_posts = [
        "My wife left me and I'm so sad",
        "Water shortage affecting millions in our country",
        "We have no electricity for 3 days now",
        "I got fired from my job today",
        "The war has displaced thousands of families",
        "Can't find water anywhere in the city",
        "My personal problems with anxiety",
        "Everyone is struggling with inflation",
        "No power again today, this is widespread",
        "The crisis is affecting all of us",
    ]

    print("Individual Post Analysis:\n")
    for post in test_posts[:3]:
        result = analyzer.analyze_post(post)
        print(f"Text: {post}")
        print(f"Is Collective: {result['is_collective']}")
        print(f"Score: {result['collective_score']:.2f}")
        print(f"Reason: {result['reason']}\n")

    print("\n" + "="*50)
    print("Pattern Detection:\n")

    # Simulate posts
    posts_data = [{'text': text, 'emotion': 'sadness'} for text in test_posts]
    patterns = analyzer.detect_collective_patterns(posts_data, min_pattern_size=2)

    for pattern in patterns:
        print(f"Pattern {pattern['cluster_id']}:")
        print(f"  Size: {pattern['size']} posts")
        print(f"  Keywords: {', '.join(pattern['keywords'][:5])}")
        print(f"  Dominant emotion: {pattern['dominant_emotion']}\n")
