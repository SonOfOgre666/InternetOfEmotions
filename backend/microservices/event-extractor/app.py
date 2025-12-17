"""
Event Extractor Microservice
Groups related posts by country into thematic events with titles and descriptions
"""

from flask import Flask, jsonify, request
import sys
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from database import SharedDatabase
from config import DB_PATH

# Import ML libraries for clustering and summarization
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import DBSCAN
    MODELS_AVAILABLE = True
    print("✓ Using sklearn TfidfVectorizer for semantic similarity (lightweight, no PyTorch needed)")
except ImportError:
    MODELS_AVAILABLE = False
    print("Warning: ML libraries not available. Using fallback grouping.")

app = Flask(__name__)
db = SharedDatabase(DB_PATH)


class EventExtractor:
    """Extracts thematic events from posts using clustering and extractive summarization"""
    
    def __init__(self):
        self.vectorizer = None
        self.summarizer = "extractive"  # Use lightweight extractive summarization
        
        if MODELS_AVAILABLE:
            try:
                # Use TfidfVectorizer for semantic similarity (lightweight, no PyTorch)
                self.vectorizer = TfidfVectorizer(
                    max_features=500,  # Limit features for speed
                    ngram_range=(1, 2),  # Unigrams and bigrams
                    min_df=1,  # Minimum document frequency
                    stop_words='english'  # Remove common English words
                )
                print("✓ Event extraction ready: TfidfVectorizer + DBSCAN + extractive summarization")
            except Exception as e:
                print(f"Error initializing vectorizer: {e}")
                self.vectorizer = None
                self.summarizer = None
    
    def extract_events_for_country(self, country: str) -> list:
        """
        Group posts from a country into thematic events
        Returns list of events with title, description, and post IDs
        """
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get recent posts from last 7 days that haven't been grouped into events
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        print(f"DEBUG: Querying posts for {country} after {seven_days_ago}", flush=True)
        
        # Get posts that aren't already in events
        # Include ALL post types (text, link, image, video, social) - they all have titles/text
        cursor.execute('''
            SELECT rp.id, rp.text, rp.timestamp, rp.url, rp.source, rp.post_type
            FROM raw_posts rp
            WHERE rp.country = ? 
            AND rp.timestamp > ?
            AND rp.needs_extraction = 0
            AND rp.post_type IN ('text', 'link', 'image', 'video', 'social')
            AND rp.id NOT IN (
                SELECT json_each.value
                FROM events, json_each(events.post_ids)
                WHERE events.country = ?
            )
            ORDER BY rp.timestamp DESC
        ''', (country, seven_days_ago, country))
        
        posts = [{'id': row[0], 'text': row[1], 'timestamp': row[2], 'url': row[3], 'source': row[4], 'post_type': row[5]} 
                 for row in cursor.fetchall()]
        
        print(f"DEBUG: Found {len(posts)} posts for {country}", flush=True)
        
        if len(posts) < 1:
            # Need at least 1 post to make an event
            return []
        
        # Use ML clustering if available, otherwise simple keyword grouping
        if self.vectorizer:
            events = self._cluster_posts_ml(posts, country)
            print(f"DEBUG: Extracted {len(events)} events for {country}", flush=True)
        else:
            events = self._cluster_posts_simple(posts, country)
        
        return events
    
    def _cluster_posts_ml(self, posts: list, country: str) -> list:
        """Use TF-IDF vectorization and DBSCAN clustering to group similar posts"""
        
        # Create TF-IDF vectors
        texts = [p['text'][:500] for p in posts]  # Limit to 500 chars
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        
        # Calculate cosine similarity matrix
        # DBSCAN expects distance, so we use (1 - cosine_similarity)
        similarity_matrix = cosine_similarity(tfidf_matrix)
        distance_matrix = np.clip(1 - similarity_matrix, 0, 2)  # Ensure non-negative distances
        
        # DBSCAN clustering (density-based, auto-detects number of clusters)
        # eps=0.75 means posts with >25% similarity will cluster (1 - 0.75 = 0.25 similarity threshold)
        # min_samples=2 requires at least 2 posts to form a cluster
        # Lenient threshold to ensure related topics cluster together
        clustering = DBSCAN(eps=0.75, min_samples=2, metric='precomputed').fit(distance_matrix)
        
        # Group posts by cluster
        clusters = defaultdict(list)
        individual_posts = []  # Track unclustered posts
        
        for idx, label in enumerate(clustering.labels_):
            if label != -1:  # -1 means noise (unclustered)
                clusters[label].append(posts[idx])
            else:
                # Treat unclustered posts as individual events
                individual_posts.append(posts[idx])
        
        print(f"DEBUG: DBSCAN found {len(clusters)} clusters and {len(individual_posts)} individual posts", flush=True)
        
        # Create events from clusters
        events = []
        for cluster_id, cluster_posts in clusters.items():
            event = self._create_event_from_posts(cluster_posts, country)
            if event:
                events.append(event)
        
        # Create events from individual posts (important standalone news)
        for post in individual_posts:
            event = self._create_event_from_posts([post], country)
            if event:
                events.append(event)
        
        return events
    
    def _cluster_posts_simple(self, posts: list, country: str) -> list:
        """Simple keyword-based grouping as fallback"""
        
        # Extract common keywords and group posts
        from collections import Counter
        
        # Simple approach: group posts by shared significant words
        clusters = defaultdict(list)
        
        for post in posts:
            # Extract significant words (simple tokenization)
            words = set([w.lower() for w in post['text'].split() if len(w) > 5])
            
            # Find existing cluster with shared words
            assigned = False
            for cluster_id, cluster_posts in clusters.items():
                cluster_words = set()
                for cp in cluster_posts:
                    cluster_words.update([w.lower() for w in cp['text'].split() if len(w) > 5])
                
                # If >20% word overlap, add to cluster
                if words and cluster_words:
                    overlap = len(words & cluster_words) / len(words | cluster_words)
                    if overlap > 0.2:
                        clusters[cluster_id].append(post)
                        assigned = True
                        break
            
            if not assigned:
                clusters[len(clusters)].append(post)
        
        # Create events from clusters with at least 1 post
        events = []
        for cluster_posts in clusters.values():
            if len(cluster_posts) >= 1:
                event = self._create_event_from_posts(cluster_posts, country)
                if event:
                    events.append(event)
        
        return events
    
    def _create_event_from_posts(self, posts: list, country: str) -> dict:
        """Create event with title and ML-generated summary from clustered posts"""
        
        if not posts:
            return None
        
        # Sort posts by timestamp
        posts = sorted(posts, key=lambda p: p['timestamp'], reverse=True)
        
        # Generate title - use most recent post's first sentence
        first_sentence = posts[0]['text'].split('.')[0]
        # Use full sentence if reasonable length, otherwise truncate at 200 chars
        if len(first_sentence) <= 200:
            title = first_sentence
        else:
            title = first_sentence[:200] + '...'
        
        # Generate description using T5 summarization
        description = self._generate_summary(posts)
        
        # Create event object
        event = {
            'country': country,
            'title': title,
            'description': description,
            'post_ids': json.dumps([p['id'] for p in posts]),
            'event_date': posts[0]['timestamp'],
            'post_count': len(posts),
            'urls': [p['url'] for p in posts if p['url']]
        }
        
        return event
    
    def _generate_summary(self, posts: list) -> str:
        """
        Generate intelligent summary using extractive method (lightweight, no torch).
        Creates a concise 1-2 sentence summary of what the event is about.
        """
        
        if not posts:
            return "No description available."
        
        # Combine all post content (title + body are already merged by content-extractor)
        combined_text = ""
        for post in posts[:3]:  # Use up to 3 posts to avoid too much text
            text = post.get('text', '')
            combined_text += text[:300] + " "  # 300 chars per post max
        
        combined_text = combined_text.strip()
        
        if not combined_text or len(combined_text) < 50:
            return self._create_description_simple(posts)
        
        # Use extractive summarization (sentence ranking)
        if self.summarizer == "extractive":
            try:
                # Generate concise 1-2 sentence summary
                summary = self._extractive_summarization(combined_text, max_sentences=2)
                
                # Ensure summary is not too long (max 250 chars)
                if len(summary) > 250:
                    # Take first sentence only if too long
                    first_sentence = summary.split('.')[0] + '.'
                    summary = first_sentence
                
                print(f"✓ Generated extractive summary: {summary[:80]}...")
                return summary
                
            except Exception as e:
                print(f"⚠️  Summarization error: {e}")
                return self._create_description_simple(posts)
        else:
            return self._create_description_simple(posts)
    
    def _extractive_summarization(self, text: str, max_sentences: int = 2) -> str:
        """
        Lightweight extractive summarization using sentence scoring.
        Creates concise summaries by selecting the most informative sentences.
        """
        import re
        from collections import Counter
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20 and len(s.strip()) < 200]
        
        if not sentences:
            return text[:200] + "..." if len(text) > 200 else text
        
        if len(sentences) <= max_sentences:
            return '. '.join(sentences) + '.'
        
        # Score sentences by word frequency and position
        words = re.findall(r'\b\w+\b', text.lower())
        word_freq = Counter(words)
        
        # Remove common words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                    'of', 'with', 'by', 'from', 'is', 'was', 'are', 'were', 'been', 'be',
                    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                    'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
                    'hi', 'hello', 'my', 'me', 'i', 'you', 'we', 'they', 'he', 'she', 'it'}
        
        for sw in stopwords:
            word_freq.pop(sw, None)
        
        # Score each sentence
        sentence_scores = []
        for idx, sentence in enumerate(sentences):
            words_in_sentence = re.findall(r'\b\w+\b', sentence.lower())
            
            # Content score based on important words
            content_score = sum(word_freq.get(word, 0) for word in words_in_sentence)
            
            # Position bonus: prefer earlier sentences (but not the very first if it's an intro)
            position_score = (len(sentences) - idx) * 0.1 if idx > 0 else 0
            
            # Penalty for very long sentences
            length_penalty = -0.2 if len(sentence) > 150 else 0
            
            total_score = content_score + position_score + length_penalty
            sentence_scores.append((total_score, sentence, idx))
        
        # Sort by score and take top N
        sentence_scores.sort(reverse=True, key=lambda x: x[0])
        top_sentences = sentence_scores[:max_sentences]
        
        # Sort by original position to maintain reading flow
        top_sentences.sort(key=lambda x: x[2])
        
        summary = '. '.join([sent for _, sent, _ in top_sentences]) + '.'
        
        # Clean up any duplicate phrases
        if len(summary) > 250:
            summary = top_sentences[0][1] + '.'
        
        return summary
    
    def _create_description_simple(self, posts: list) -> str:
        """Fallback: Create concise description from posts"""
        
        if not posts:
            return "No description available."
        
        # Get first meaningful sentence that's not too generic
        post = posts[0]
        text = post.get('text', '')
        
        if not text:
            return "Multiple posts about this topic."
        
        # Split into sentences
        import re
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not sentences:
            return text[:150] + "..." if len(text) > 150 else text
        
        # Skip generic intro sentences (AMA, Hi, etc.)
        generic_starts = ['hi ', 'hello ', 'ama ', 'ask me anything']
        meaningful_sentence = None
        
        for sentence in sentences[:3]:  # Check first 3 sentences
            sentence_lower = sentence.lower()
            if not any(sentence_lower.startswith(g) for g in generic_starts):
                if len(sentence) > 30 and len(sentence) < 200:
                    meaningful_sentence = sentence
                    break
        
        if meaningful_sentence:
            return meaningful_sentence + "."
        
        # Fallback to first non-empty sentence, truncated
        first_sent = sentences[0] if sentences else text
        if len(first_sent) > 150:
            first_sent = first_sent[:150].rsplit(' ', 1)[0] + "..."
        
        return first_sent + "."
    
    def _create_event_from_posts(self, posts: list, country: str) -> dict:
        """Create event object from clustered posts"""
        if not posts:
            return None
        
        # Sort posts by timestamp
        posts = sorted(posts, key=lambda p: p['timestamp'], reverse=True)
        
        # Generate title - use most recent post's first sentence
        first_sentence = posts[0]['text'].split('.')[0]
        # Use full sentence if reasonable length, otherwise truncate at 200 chars
        if len(first_sentence) <= 200:
            title = first_sentence
        else:
            title = first_sentence[:200] + '...'
        
        # Generate concise summary
        description = self._generate_summary(posts)
        
        # Create event object
        event = {
            'country': country,
            'title': title,
            'description': description,
            'post_ids': json.dumps([p['id'] for p in posts]),
            'event_date': posts[0]['timestamp'],
            'post_count': len(posts),
            'urls': [p['url'] for p in posts if p['url']]
        }
        
        return event


# Initialize extractor
extractor = EventExtractor()


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'event-extractor',
        'models_available': MODELS_AVAILABLE
    })


@app.route('/extract_events', methods=['POST'])
def extract_events():
    """
    Extract events from posts for specified countries
    Body: { "countries": ["USA", "Japan", ...] }
    """
    data = request.get_json() or {}
    countries = data.get('countries', [])
    
    if not countries:
        # Get all active countries
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT country FROM raw_posts')
        countries = [row[0] for row in cursor.fetchall()]
    
    total_events = 0
    results = {}
    
    for country in countries:
        try:
            events = extractor.extract_events_for_country(country)
            
            if events:
                # Save events to database with batch insert
                conn = db.get_connection()
                cursor = conn.cursor()
                
                # Batch insert for better performance
                cursor.executemany('''
                    INSERT INTO events (country, title, description, post_ids, event_date, is_analyzed, post_count)
                    VALUES (?, ?, ?, ?, ?, 0, ?)
                ''', [(event['country'], event['title'], event['description'], 
                       event['post_ids'], event['event_date'], event['post_count']) for event in events])
                
                conn.commit()
            
            results[country] = len(events)
            total_events += len(events)
            
        except Exception as e:
            print(f"Error extracting events for {country}: {e}")
            results[country] = 0
    
    return jsonify({
        'status': 'success',
        'total_events': total_events,
        'by_country': results
    })


@app.route('/events/<country>', methods=['GET'])
def get_country_events(country):
    """Get recent events for a country"""
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, description, post_ids, event_date, emotion, confidence
        FROM events
        WHERE country = ?
        ORDER BY event_date DESC
        LIMIT 20
    ''', (country,))
    
    events = []
    for row in cursor.fetchall():
        post_ids = json.loads(row[3])
        
        # Get post URLs
        cursor.execute(f'''
            SELECT url FROM raw_posts 
            WHERE id IN ({','.join(['?']*len(post_ids))})
        ''', post_ids)
        urls = [r[0] for r in cursor.fetchall() if r[0]]
        
        events.append({
            'id': row[0],
            'title': row[1],
            'description': row[2],
            'post_count': len(post_ids),
            'event_date': row[4],
            'emotion': row[5],
            'confidence': row[6],
            'urls': urls
        })
    
    return jsonify({
        'country': country,
        'events': events
    })


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5004))
    app.run(host='0.0.0.0', port=port, debug=False)
