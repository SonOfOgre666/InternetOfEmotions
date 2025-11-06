"""
Country Emotion Aggregator
Aggregates emotions from individual posts into ONE dominant emotion per country
using multiple statistical algorithms
"""

from collections import Counter
from typing import Dict, List, Tuple
import numpy as np


class CountryEmotionAggregator:
    """
    Combines emotions from multiple posts to determine ONE dominant emotion per country
    Uses multiple algorithms for robust aggregation
    """

    def __init__(self):
        """Initialize aggregator with emotion weights"""
        # Emotion intensity ordering (for weighted voting)
        self.emotion_intensity = {
            'anger': 0.95,      # Strongest emotion
            'fear': 0.90,
            'disgust': 0.85,
            'sadness': 0.70,
            'surprise': 0.60,
            'joy': 0.80,        # Positive but strong
            'neutral': 0.30     # Weakest
        }

    def aggregate_country_emotions(self, posts: List[Dict]) -> Dict:
        """
        Aggregate emotions from all posts in a country
        Returns: {
            'dominant_emotion': str,
            'confidence': float,
            'distribution': {emotion: count},
            'weighted_scores': {emotion: score},
            'method': str (which algorithm won),
            'details': {...}
        }
        """
        if not posts:
            return {
                'dominant_emotion': 'neutral',
                'confidence': 0.0,
                'distribution': {},
                'weighted_scores': {},
                'method': 'empty',
                'details': 'No posts to analyze'
            }

        # Extract emotions and confidences
        emotions = [p['emotion'] for p in posts]
        confidences = [p.get('confidence', 0.5) for p in posts]

        # Apply multiple aggregation algorithms
        results = {}

        # Algorithm 1: Simple Majority Vote (Most Common)
        results['majority'] = self._majority_vote(emotions)

        # Algorithm 2: Weighted Vote (by confidence scores)
        results['weighted'] = self._weighted_vote(emotions, confidences)

        # Algorithm 3: Intensity-based Vote (emotion strength)
        results['intensity'] = self._intensity_weighted_vote(emotions, confidences)

        # Algorithm 4: Median with Intensity (robust to outliers)
        results['intensity_median'] = self._intensity_median_vote(emotions, confidences)

        # Consensus: Which algorithm agrees most?
        final_emotion = self._consensus_emotion(results)

        # Calculate confidence
        emotion_counts = Counter(emotions)
        confidence = self._calculate_confidence(final_emotion, emotion_counts, confidences)

        # Distribution
        emotion_distribution = dict(emotion_counts)

        # Weighted scores for each emotion
        weighted_scores = self._calculate_weighted_scores(emotions, confidences)

        return {
            'dominant_emotion': final_emotion,
            'confidence': round(confidence, 2),
            'distribution': emotion_distribution,
            'weighted_scores': {k: round(v, 3) for k, v in weighted_scores.items()},
            'method': 'ensemble_aggregation',
            'algorithm_votes': results,
            'total_posts': len(posts),
            'details': {
                'total_emotions_analyzed': len(emotions),
                'emotion_distribution': emotion_distribution,
                'average_confidence': round(np.mean(confidences), 2),
                'algorithm_consensus': self._get_algorithm_names(results)
            }
        }

    def _majority_vote(self, emotions: List[str]) -> Tuple[str, float]:
        """
        Algorithm 1: Simple majority vote - most common emotion wins
        Best for: Clear consensus
        """
        if not emotions:
            return ('neutral', 0.0)

        counter = Counter(emotions)
        most_common, count = counter.most_common(1)[0]
        vote_strength = count / len(emotions)  # % of votes

        return (most_common, vote_strength)

    def _weighted_vote(self, emotions: List[str], confidences: List[float]) -> Tuple[str, float]:
        """
        Algorithm 2: Weighted by confidence scores
        Best for: Mixed confidence levels
        Weight each emotion by its average confidence
        """
        if not emotions or not confidences:
            return ('neutral', 0.0)

        emotion_scores = {}

        for emotion, confidence in zip(emotions, confidences):
            if emotion not in emotion_scores:
                emotion_scores[emotion] = []
            emotion_scores[emotion].append(confidence)

        # Calculate average confidence per emotion
        weighted_emotions = {}
        for emotion, conf_list in emotion_scores.items():
            avg_confidence = np.mean(conf_list)
            weight = len(conf_list) / len(emotions)  # frequency weight
            weighted_emotions[emotion] = avg_confidence * weight

        best_emotion = max(weighted_emotions.items(), key=lambda x: x[1])

        return (best_emotion[0], best_emotion[1])

    def _intensity_weighted_vote(self, emotions: List[str], confidences: List[float]) -> Tuple[str, float]:
        """
        Algorithm 3: Weighted by emotion intensity + confidence
        Best for: Identifying strong collective emotions
        Stronger emotions (anger, fear) get higher priority
        """
        if not emotions or not confidences:
            return ('neutral', 0.0)

        emotion_scores = {}

        for emotion, confidence in zip(emotions, confidences):
            intensity = self.emotion_intensity.get(emotion, 0.5)
            # Combined score: intensity × confidence × frequency
            score = intensity * confidence

            if emotion not in emotion_scores:
                emotion_scores[emotion] = []
            emotion_scores[emotion].append(score)

        # Sum scores for each emotion
        total_scores = {}
        for emotion, score_list in emotion_scores.items():
            total_scores[emotion] = sum(score_list)

        best_emotion = max(total_scores.items(), key=lambda x: x[1])

        # Normalize to 0-1
        total_intensity = sum(total_scores.values())
        normalized_score = best_emotion[1] / total_intensity if total_intensity > 0 else 0

        return (best_emotion[0], normalized_score)

    def _intensity_median_vote(self, emotions: List[str], confidences: List[float]) -> Tuple[str, float]:
        """
        Algorithm 4: Median-based with intensity weighting
        Best for: Robustness to outliers
        More resistant to a few extreme values
        """
        if not emotions or not confidences:
            return ('neutral', 0.0)

        emotion_scores = {}

        for emotion, confidence in zip(emotions, confidences):
            intensity = self.emotion_intensity.get(emotion, 0.5)
            score = intensity * confidence

            if emotion not in emotion_scores:
                emotion_scores[emotion] = []
            emotion_scores[emotion].append(score)

        # Use median instead of sum for robustness
        median_scores = {}
        for emotion, score_list in emotion_scores.items():
            median_scores[emotion] = np.median(score_list)

        best_emotion = max(median_scores.items(), key=lambda x: x[1])

        # Normalize
        total_median = sum(median_scores.values())
        normalized_score = best_emotion[1] / total_median if total_median > 0 else 0

        return (best_emotion[0], normalized_score)

    def _consensus_emotion(self, algorithm_results: Dict) -> str:
        """
        Determine final emotion from multiple algorithms
        Takes emotion that wins in most algorithms
        """
        emotions_by_algo = [result[0] for result in algorithm_results.values()]
        counter = Counter(emotions_by_algo)

        # Most algorithms agree on which emotion?
        consensus_emotion = counter.most_common(1)[0][0]

        return consensus_emotion

    def _calculate_confidence(self, emotion: str, distribution: Dict, confidences: List[float]) -> float:
        """
        Calculate overall confidence in the prediction
        Based on agreement and individual confidence scores
        """
        # Agreement score: % of posts with dominant emotion
        emotion_count = distribution.get(emotion, 0)
        total_posts = sum(distribution.values())
        agreement = emotion_count / total_posts if total_posts > 0 else 0

        # Average confidence of posts with that emotion
        avg_confidence = np.mean(confidences)

        # Combined confidence
        confidence = (agreement * 0.6) + (avg_confidence * 0.4)

        return min(confidence, 1.0)  # Cap at 1.0

    def _calculate_weighted_scores(self, emotions: List[str], confidences: List[float]) -> Dict[str, float]:
        """Calculate weighted score for each emotion"""
        emotion_scores = {}

        for emotion, confidence in zip(emotions, confidences):
            intensity = self.emotion_intensity.get(emotion, 0.5)

            if emotion not in emotion_scores:
                emotion_scores[emotion] = []

            emotion_scores[emotion].append(confidence * intensity)

        # Average weighted score per emotion
        return {
            emotion: np.mean(scores)
            for emotion, scores in emotion_scores.items()
        }

    def _get_algorithm_names(self, results: Dict) -> Dict[str, str]:
        """Get human-readable names of algorithm results"""
        names = {
            'majority': f"Majority Vote: {results['majority'][0]}",
            'weighted': f"Weighted Vote: {results['weighted'][0]}",
            'intensity': f"Intensity Vote: {results['intensity'][0]}",
            'intensity_median': f"Median Intensity Vote: {results['intensity_median'][0]}"
        }
        return names

    def get_emotion_trend(self, posts_by_time: List[List[Dict]]) -> Dict:
        """
        Analyze emotion trend over time for a country
        Takes posts grouped by time period
        Returns emotion changes over time
        """
        trends = []

        for period_posts in posts_by_time:
            agg_result = self.aggregate_country_emotions(period_posts)
            trends.append({
                'timestamp': period_posts[0].get('timestamp') if period_posts else None,
                'emotion': agg_result['dominant_emotion'],
                'confidence': agg_result['confidence'],
                'post_count': len(period_posts)
            })

        return {
            'trends': trends,
            'trend_direction': self._calculate_trend_direction(trends)
        }

    def _calculate_trend_direction(self, trends: List[Dict]) -> str:
        """Determine if emotion is improving, worsening, or stable"""
        if len(trends) < 2:
            return 'insufficient_data'

        # Define positive vs negative emotions
        negative_emotions = {'anger', 'fear', 'sadness', 'disgust'}

        recent_negatives = sum(
            1 for t in trends[-3:]
            if t['emotion'] in negative_emotions
        )
        old_negatives = sum(
            1 for t in trends[:-3]
            if t['emotion'] in negative_emotions
        ) if len(trends) > 3 else recent_negatives

        if recent_negatives > old_negatives:
            return 'worsening'
        elif recent_negatives < old_negatives:
            return 'improving'
        else:
            return 'stable'


# Test
if __name__ == '__main__':
    aggregator = CountryEmotionAggregator()

    # Example: 10 posts from different countries
    sample_posts_usa = [
        {'emotion': 'joy', 'confidence': 0.92},
        {'emotion': 'joy', 'confidence': 0.88},
        {'emotion': 'sadness', 'confidence': 0.75},
        {'emotion': 'joy', 'confidence': 0.91},
        {'emotion': 'joy', 'confidence': 0.89},
        {'emotion': 'neutral', 'confidence': 0.60},
        {'emotion': 'joy', 'confidence': 0.93},
        {'emotion': 'joy', 'confidence': 0.87},
    ]

    sample_posts_india = [
        {'emotion': 'fear', 'confidence': 0.91},
        {'emotion': 'fear', 'confidence': 0.88},
        {'emotion': 'anger', 'confidence': 0.85},
        {'emotion': 'fear', 'confidence': 0.90},
        {'emotion': 'sadness', 'confidence': 0.78},
        {'emotion': 'fear', 'confidence': 0.92},
        {'emotion': 'fear', 'confidence': 0.87},
        {'emotion': 'anger', 'confidence': 0.82},
    ]

    print("USA Emotion Aggregation:")
    usa_result = aggregator.aggregate_country_emotions(sample_posts_usa)
    print(f"  Dominant Emotion: {usa_result['dominant_emotion']} (Confidence: {usa_result['confidence']})")
    print(f"  Distribution: {usa_result['distribution']}")
    print(f"  Algorithm Votes: {usa_result['algorithm_votes']}\n")

    print("India Emotion Aggregation:")
    india_result = aggregator.aggregate_country_emotions(sample_posts_india)
    print(f"  Dominant Emotion: {india_result['dominant_emotion']} (Confidence: {india_result['confidence']})")
    print(f"  Distribution: {india_result['distribution']}")
    print(f"  Algorithm Votes: {india_result['algorithm_votes']}\n")
