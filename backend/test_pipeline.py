"""
Pipeline Testing Script - Deep Dive into Each Function
Tests each component of the emotion analysis pipeline with detailed I/O

TESTING MODE:
- Uses LIMITED regions (2-4 countries per region for faster testing)
- Uses SEPARATE test database (test_posts.db)
- Uses YOUR Reddit API credentials from .env
- Detailed input/output for each function
"""

import os
import sys
import json
from datetime import datetime
from pprint import pprint
import praw
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all components
from emotion_analyzer import EmotionAnalyzer
from collective_analyzer import CollectiveAnalyzer
from multimodal_analyzer import MultimodalAnalyzer
from cross_country_detector import CrossCountryDetector
from post_database import PostDatabase
from country_coordinates import get_coordinates

# Load environment
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# ============================================================================
# TEST CONFIGURATION - Limited regions for faster testing
# ============================================================================
TEST_REGIONS = {
    "europe": ["albania", "andorra"],
    "asia": ["afghanistan", "armenia"],
    "africa": ["algeria", "angola", "benin"],
    "americas": ["antigua and barbuda", "argentina", "bahamas", "barbados"],
    "oceania": ["australia", "federated states of micronesia"],
    "middleeast": ["bahrain", "cyprus", "iran", "iraq"]
}

TEST_REGION_SUBREDDITS = {
    "europe":     ["europe", "worldnews", "news", "UpliftingNews", "UnderReportedNews"],
    "asia":       ["asia", "worldnews", "news", "UpliftingNews", "UnderReportedNews"],
    "africa":     ["africa", "worldnews", "news", "UpliftingNews", "UnderReportedNews"],
    "americas":   ["worldnews", "news", "latinamerica", "UpliftingNews", "UnderReportedNews"],
    "oceania":    ["australia", "worldnews", "news", "UpliftingNews", "UnderReportedNews"],
    "middleeast": ["middleeast", "worldnews", "news", "UpliftingNews", "UnderReportedNews"],
}

# Build reverse lookup for test regions
TEST_COUNTRY_TO_REGION = {}
for region, countries in TEST_REGIONS.items():
    for country in countries:
        TEST_COUNTRY_TO_REGION[country.lower()] = region

# Test database path (separate from production)
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), 'test_posts.db')

print(f"\n{'='*80}")
print(f"TESTING CONFIGURATION")
print(f"{'='*80}")
print(f"Database: {TEST_DB_PATH}")
print(f"Total test countries: {sum(len(countries) for countries in TEST_REGIONS.values())}")
print(f"Regions: {list(TEST_REGIONS.keys())}")
print(f"Using Reddit credentials from: .env file")
print(f"{'='*80}\n")


# ============================================================================
# TEST HELPER FUNCTIONS - Regional Search
# ============================================================================
def get_country_region_test(country: str) -> str:
    """Get the region for a country (test version)"""
    country_lower = country.lower()
    
    # Direct lookup
    if country_lower in TEST_COUNTRY_TO_REGION:
        return TEST_COUNTRY_TO_REGION[country_lower]
    
    # Fuzzy matching for variations
    for region, countries in TEST_REGIONS.items():
        for c in countries:
            if country_lower in c or c in country_lower:
                return region
    
    # Default fallback
    return "worldnews"


def search_regional_subreddits_test(reddit, country: str, limit: int = 50) -> list:
    """
    Search region-specific subreddits for posts about a country (test version)
    Uses TEST_REGIONS and TEST_REGION_SUBREDDITS
    """
    from datetime import timedelta
    
    posts = []
    seen_ids = set()
    
    # Calculate date threshold (only posts from last 30 days)
    date_threshold = datetime.now() - timedelta(days=30)
    date_threshold_timestamp = date_threshold.timestamp()
    
    # Get region for this country
    region = get_country_region_test(country)
    
    # Get subreddits for this region
    subreddits = TEST_REGION_SUBREDDITS.get(region, ["worldnews", "news"])
    
    print(f"  🔍 Searching for {country} in region '{region}' subreddits: {subreddits}")
    
    try:
        # Search each regional subreddit
        for subreddit_name in subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                
                # Search for country name in this subreddit
                search_results = subreddit.search(
                    country,
                    limit=15,
                    time_filter='month',
                    sort='new'
                )
                
                for submission in search_results:
                    # DATE FILTER: Skip posts older than 30 days
                    if submission.created_utc < date_threshold_timestamp:
                        continue
                    
                    # Skip duplicates
                    if submission.id in seen_ids:
                        continue
                    seen_ids.add(submission.id)
                    
                    # Must have content
                    if submission.selftext or submission.title:
                        text = f"{submission.title}. {submission.selftext[:500]}"
                        
                        post_age_days = (datetime.now().timestamp() - submission.created_utc) / 86400
                        
                        posts.append({
                            'text': text,
                            'country': country,
                            'coords': get_coordinates(country),
                            'timestamp': datetime.fromtimestamp(submission.created_utc).isoformat(),
                            'source': f'r/{submission.subreddit.display_name}',
                            'id': submission.id,
                            'url': f'https://reddit.com{submission.permalink}',
                            'author': str(submission.author) if submission.author else '[deleted]',
                            'score': submission.score,
                            'num_comments': submission.num_comments,
                            'subreddit': submission.subreddit.display_name,
                            'search_query': f'{country} in r/{subreddit_name}',
                            'post_age_days': round(post_age_days, 1),
                            'region': region
                        })
                        
                        # Stop early if we have enough posts
                        if len(posts) >= limit:
                            print(f"  ✓ Found {len(posts)} posts (stopped early)")
                            return posts
                            
            except Exception as e:
                print(f"  ✗ Error searching r/{subreddit_name}: {e}")
                continue
        
        # Sort by date (newest first)
        posts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        if posts:
            print(f"  ✓ Found {len(posts)} posts")
        else:
            print(f"  ⚠ Found 0 posts")
        
    except Exception as e:
        print(f"  ❌ Error in regional search: {e}")
    
    return posts

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_section(title):
    """Print a section header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title.center(80)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}\n")

def print_step(step_num, title):
    """Print a step header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}[Step {step_num}] {title}{Colors.END}")
    print(f"{Colors.CYAN}{'-'*80}{Colors.END}")

def print_input(label, data):
    """Print input data"""
    print(f"{Colors.YELLOW}📥 INPUT - {label}:{Colors.END}")
    if isinstance(data, (dict, list)):
        print(json.dumps(data, indent=2, default=str)[:500])
    else:
        print(str(data)[:500])
    print()

def print_output(label, data):
    """Print output data"""
    print(f"{Colors.GREEN}📤 OUTPUT - {label}:{Colors.END}")
    if isinstance(data, (dict, list)):
        print(json.dumps(data, indent=2, default=str)[:800])
    else:
        print(str(data)[:800])
    print()

def print_analysis(text):
    """Print analysis text"""
    print(f"{Colors.BLUE}💡 ANALYSIS: {text}{Colors.END}\n")


# =============================================================================
# TEST 1: COUNTRY COORDINATES
# =============================================================================
def test_country_coordinates():
    print_section("TEST 1: COUNTRY COORDINATES")
    print_analysis("Maps country names to latitude/longitude for map display")
    
    test_countries = ['brazil', 'usa', 'china', 'russia', 'australia']
    
    for country in test_countries:
        print_step("2", f"Get coordinates for {country}")
        print_input("Country", country)
        coords = get_coordinates(country)
        print_output("Coordinates [lat, lon]", coords)
        print_analysis(f"Will be displayed at position: {coords}")


# =============================================================================
# TEST 2: REDDIT FETCH (Regional Search Strategy)
# =============================================================================
def test_reddit_fetch():
    print_section("TEST 2: REDDIT FETCH")
    print_analysis("Fetches Reddit posts using REGIONAL SEARCH strategy (not country subreddits)")
    print_analysis("Searches regional subreddits (r/europe, r/asia, etc.) for country mentions")
    
    # Initialize Reddit
    print_step(1, "Initialize Reddit API")
    reddit = praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        user_agent=os.getenv('REDDIT_USER_AGENT', 'EmotionsDashboard/1.0')
    )
    print_output("Reddit API", "Connected successfully")
    
    # Test regional search
    print_step(2, "Test Regional Subreddit Search (NEW STRATEGY)")
    test_country = "albania"  # Using test country from limited set
    print_input("Country", test_country)
    print_input("Limit", 5)
    
    region = get_country_region_test(test_country)
    print_output("Detected region", region)
    print_output("Regional subreddits", TEST_REGION_SUBREDDITS.get(region, []))
    
    posts = search_regional_subreddits_test(reddit, test_country, limit=5)
    print_output("Posts found", len(posts))
    
    if posts:
        print_step(3, "Sample Post Structure")
        sample_post = posts[0]
        print_output("Post fields", list(sample_post.keys()))
        print_output("Full post", sample_post)
        print_analysis(f"Post age: {sample_post.get('post_age_days', 'N/A')} days")
        print_analysis(f"Source: {sample_post.get('source', 'N/A')}")
        print_analysis(f"Region: {sample_post.get('region', 'N/A')}")
    
    return posts


# =============================================================================
# TEST 3: EMOTION ANALYZER (RoBERTa Model)
# =============================================================================
def test_emotion_analyzer(posts):
    print_section("TEST 3: EMOTION ANALYZER")
    print_analysis("Uses j-hartmann/emotion-english-distilroberta-base")
    print_analysis("Classifies text into 7 emotions: joy, sadness, anger, fear, surprise, neutral, disgust")
    
    if not posts:
        print(f"{Colors.RED}⚠️  No posts available. Skipping this test.{Colors.END}")
        return None
    
    print_step(1, "Initialize EmotionAnalyzer")
    analyzer = EmotionAnalyzer()
    print_output("Model loaded", "j-hartmann/emotion-english-distilroberta-base")
    
    print_step(2, "Analyze Post Emotion")
    test_post = posts[0]
    print_input("Text", test_post['text'][:300] + "...")
    
    result = analyzer.analyze(test_post['text'])
    print_output("Emotion", result['emotion'])
    print_output("Confidence", f"{result['confidence']:.2%}")
    print_output("All scores", result.get('scores', {}))
    
    print_analysis(f"The text was classified as '{result['emotion']}' with {result['confidence']:.1%} confidence")
    
    return result


# =============================================================================
# TEST 4: COLLECTIVE ANALYZER (BART Zero-Shot)
# =============================================================================
def test_collective_analyzer(posts):
    print_section("TEST 4: COLLECTIVE ANALYZER")
    print_analysis("Uses facebook/bart-large-mnli for zero-shot classification")
    print_analysis("Determines if post is about collective issues vs personal issues")
    
    if not posts:
        print(f"{Colors.RED}⚠️  No posts available. Skipping this test.{Colors.END}")
        return None
    
    print_step(1, "Initialize CollectiveAnalyzer")
    analyzer = CollectiveAnalyzer()
    print_output("Model loaded", "facebook/bart-large-mnli")
    
    print_step(2, "Analyze if Post is Collective")
    test_post = posts[0]
    print_input("Text", test_post['text'][:300] + "...")
    
    result = analyzer.analyze_post(test_post['text'])
    print_output("Is collective?", result['is_collective'])
    print_output("Collective score", f"{result['collective_score']:.2%}")
    print_output("Classification details", result.get('classification', {}))
    
    if result['is_collective']:
        print_analysis(f"✓ This is a COLLECTIVE issue (affects many people) - score: {result['collective_score']:.1%}")
    else:
        print_analysis(f"✗ This is a PERSONAL issue (individual concern) - score: {result['collective_score']:.1%}")
    
    return result


# =============================================================================
# TEST 5: CROSS-COUNTRY DETECTOR (BERT-NER)
# =============================================================================
def test_cross_country_detector(posts):
    print_section("TEST 5: CROSS-COUNTRY DETECTOR")
    print_analysis("Uses dslim/bert-base-NER for Named Entity Recognition")
    print_analysis("Detects which countries are mentioned in the text")
    
    if not posts:
        print(f"{Colors.RED}⚠️  No posts available. Skipping this test.{Colors.END}")
        return None
    
    print_step(1, "Initialize CrossCountryDetector")
    detector = CrossCountryDetector()
    print_output("Model loaded", "dslim/bert-base-NER")
    
    print_step(2, "Detect Countries in Text")
    test_post = posts[0]
    print_input("Text", test_post['text'][:300] + "...")
    
    result = detector.detect_countries(test_post['text'])
    print_output("Countries found", result['countries'])
    print_output("Primary country", result['primary_country'])
    print_output("Confidence", f"{result['confidence']:.2%}")
    print_output("Detection method", result['method'])
    print_output("Mention count", result['mention_count'])
    
    print_step(3, "Cross-Country Analysis")
    print_input("Original country", test_post['country'])
    print_input("Mentioned countries", result['countries'])
    
    cross_analysis = detector.get_cross_country_analysis(
        test_post['country'],
        result['countries']
    )
    print_output("Is cross-country?", cross_analysis['is_cross_country'])
    print_output("Analysis", cross_analysis)
    
    if cross_analysis['is_cross_country']:
        print_analysis(f"✓ Post from {test_post['country']} discusses {result['primary_country']}")
    else:
        print_analysis(f"✗ Post stays within {test_post['country']}")
    
    return result


# =============================================================================
# TEST 6: MULTIMODAL ANALYZER (CLIP + BLIP)
# =============================================================================
def test_multimodal_analyzer(posts):
    print_section("TEST 6: MULTIMODAL ANALYZER")
    print_analysis("Uses CLIP for image-text matching and BLIP for image captioning")
    print_analysis("Analyzes Reddit posts with images/videos")
    
    if not posts:
        print(f"{Colors.RED}⚠️  No posts available. Skipping this test.{Colors.END}")
        return None
    
    print_step(1, "Initialize MultimodalAnalyzer")
    analyzer = MultimodalAnalyzer()
    print_output("Models loaded", "CLIP + BLIP")
    
    print_step(2, "Check for Media in Posts")
    for i, post in enumerate(posts[:3]):
        print(f"\n{Colors.CYAN}Post {i+1}:{Colors.END}")
        print_input("URL", post.get('url', 'N/A'))
        
        result = analyzer.analyze_reddit_media(post)
        print_output("Has media?", result['has_media'])
        print_output("Media type", result['media_type'])
        
        if result['has_media']:
            print_output("Media analysis", result['analysis'])
            print_analysis(f"✓ Found {result['media_type']} - analyzed with multimodal AI")
        else:
            print_analysis("✗ No media in this post")
    
    return analyzer


# =============================================================================
# TEST 7: POST DATABASE - STORAGE
# =============================================================================
def test_post_database(posts):
    print_section("TEST 7: POST DATABASE - STORAGE")
    print_analysis("Tests SQLite database operations: raw_posts → posts → country_stats")
    
    if not posts:
        print(f"{Colors.RED}⚠️  No posts available. Skipping this test.{Colors.END}")
        return None
    
    print_step(1, "Initialize PostDatabase")
    print_output("Database", TEST_DB_PATH)
    db = PostDatabase(TEST_DB_PATH)
    print_output("Using test database (separate from production)", True)
    
    print_step(2, "Add Raw Post (Before Analysis)")
    raw_post = posts[0]
    print_input("Raw post", {k: v for k, v in raw_post.items() if k not in ['text']})
    
    success = db.add_raw_post(raw_post)
    print_output("Added to raw_posts table?", success)
    
    raw_count = db.get_raw_post_count(raw_post['country'])
    print_output(f"Raw posts for {raw_post['country']}", raw_count)
    
    print_step(3, "Get Unanalyzed Posts")
    unanalyzed = db.get_unanalyzed_posts(limit=5)
    print_output("Unanalyzed posts", len(unanalyzed))
    
    print_step(4, "Add Analyzed Post (After ML Processing)")
    # Simulate analyzed post with ML results
    analyzed_post = {
        **raw_post,
        'emotion': 'neutral',
        'confidence': 0.85,
        'is_collective': True,
        'collective_score': 0.75
    }
    print_input("Analyzed post fields", list(analyzed_post.keys()))
    
    success = db.add_post(analyzed_post)
    print_output("Added to posts table?", success)
    
    # Mark as analyzed
    db.mark_post_analyzed(raw_post['id'])
    print_output("Marked as analyzed?", True)
    
    print_step(5, "Get Country Statistics")
    country_stats = db.get_all_country_stats()
    print_output("Countries with stats", len(country_stats))
    if country_stats:
        print_output("Sample country stat", country_stats[0])
    
    print_step(6, "Get Country Aggregated Emotion")
    if country_stats:
        country = country_stats[0]['country']
        print_input("Country", country)
        
        aggregated = db.get_country_aggregated_emotion(country)
        print_output("Dominant emotion", aggregated['dominant_emotion'])
        print_output("Confidence", f"{aggregated['confidence']:.2%}")
        print_output("Method", aggregated['method'])
        print_output("Algorithm votes", aggregated['algorithm_votes'])
        print_analysis(f"4 algorithms voted: {aggregated['algorithm_votes']}")
    
    return db


# =============================================================================
# TEST 8: FULL PIPELINE - END TO END
# =============================================================================
def test_full_pipeline():
    print_section("TEST 8: FULL PIPELINE - END TO END")
    print_analysis("Tests complete flow: Reddit → ML Analysis → Database → API")
    
    print_step(1, "Fetch Posts from Reddit")
    print_input("Country", "argentina")  # Using test country from limited set
    print_input("Limit", 2)
    
    # Initialize Reddit for this test
    reddit = praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        user_agent=os.getenv('REDDIT_USER_AGENT', 'EmotionsDashboard/1.0')
    )
    
    posts = search_regional_subreddits_test(reddit, "argentina", limit=2)
    print_output("Posts fetched", len(posts))
    
    if not posts:
        print(f"{Colors.RED}⚠️  No posts fetched. Cannot test full pipeline.{Colors.END}")
        return
    
    print_step(2, "Process Posts with ML Models")
    emotion_analyzer = EmotionAnalyzer()
    collective_analyzer = CollectiveAnalyzer()
    cross_country_detector = CrossCountryDetector()
    multimodal_analyzer = MultimodalAnalyzer()
    
    for i, post in enumerate(posts):
        print(f"\n{Colors.CYAN}Processing Post {i+1}:{Colors.END}")
        print_input("Text preview", post['text'][:100] + "...")
        
        # Emotion analysis
        emotion_result = emotion_analyzer.analyze(post['text'])
        print_output("Emotion", f"{emotion_result['emotion']} ({emotion_result['confidence']:.1%})")
        
        # Collective analysis
        collective_result = collective_analyzer.analyze_post(post['text'])
        print_output("Collective?", f"{collective_result['is_collective']} ({collective_result['collective_score']:.1%})")
        
        # Cross-country detection
        cross_country_result = cross_country_detector.detect_countries(post['text'])
        print_output("Countries", cross_country_result['countries'])
        
        # Multimodal
        media_result = multimodal_analyzer.analyze_reddit_media(post)
        print_output("Has media?", media_result['has_media'])
        
        # Combined result
        processed_post = {
            **post,
            'emotion': emotion_result['emotion'],
            'confidence': emotion_result['confidence'],
            'is_collective': collective_result['is_collective'],
            'collective_score': collective_result['collective_score'],
            'mentioned_countries': cross_country_result['countries'],
            'has_media': media_result['has_media']
        }
        
        print_output("Final processed post keys", list(processed_post.keys()))
    
    print_analysis("✓ Complete pipeline executed successfully!")


# =============================================================================
# TEST 9: API ENDPOINTS
# =============================================================================
def test_api_endpoints():
    print_section("TEST 9: API ENDPOINTS")
    print_analysis("Tests Flask API routes (requires running server)")
    
    print_step(1, "Available API Endpoints")
    endpoints = [
        "GET /api/emotions - Get all emotions from ready countries",
        "GET /api/stats - Get emotion statistics",
        "GET /api/countries - Get country list with emotions",
        "GET /api/country/<name> - Get detailed country info",
        "GET /api/progress - Get data collection progress",
        "GET /api/posts/stream - SSE stream of live posts",
        "GET /api/health - Health check"
    ]
    
    for endpoint in endpoints:
        print(f"{Colors.GREEN}  • {endpoint}{Colors.END}")
    
    print_analysis("Start the Flask server with: python backend/app.py")
    print_analysis("Then test with: curl http://localhost:5000/api/health")


# =============================================================================
# MAIN EXECUTION
# =============================================================================
def main():
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                   EMOTION PIPELINE - DEEP DIVE TESTING                       ║")
    print("║                  Test Each Function with Detailed I/O                        ║")
    print("║                                                                              ║")
    print("║  🧪 TEST MODE: Limited regions, separate DB, your Reddit credentials        ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    # Check if test database exists
    if os.path.exists(TEST_DB_PATH):
        print(f"{Colors.YELLOW}⚠️  Test database already exists: {TEST_DB_PATH}{Colors.END}")
        response = input("Do you want to delete it and start fresh? (y/n): ")
        if response.lower() == 'y':
            os.remove(TEST_DB_PATH)
            print(f"{Colors.GREEN}✓ Deleted old test database{Colors.END}\n")
        else:
            print(f"{Colors.YELLOW}⚠️  Continuing with existing test database{Colors.END}\n")
    
    try:
        # Test 1: Country Coordinates
        test_country_coordinates()
        
        # Test 2: Reddit Fetch
        posts = test_reddit_fetch()
        
        # Test 3: Emotion Analyzer
        test_emotion_analyzer(posts)
        
        # Test 4: Collective Analyzer
        test_collective_analyzer(posts)
        
        # Test 5: Cross-Country Detector
        test_cross_country_detector(posts)
        
        # Test 6: Multimodal Analyzer
        test_multimodal_analyzer(posts)
        
        # Test 7: Post Database
        test_post_database(posts)
        
        # Test 8: Full Pipeline
        test_full_pipeline()
        
        # Test 9: API Endpoints
        test_api_endpoints()
        
        print_section("ALL TESTS COMPLETED")
        print(f"{Colors.GREEN}✓ Pipeline testing completed successfully!{Colors.END}")
        print(f"{Colors.YELLOW}📊 Test database location: {TEST_DB_PATH}{Colors.END}")
        print(f"{Colors.YELLOW}🔧 You can inspect it with: sqlite3 {TEST_DB_PATH}{Colors.END}")
        print(f"{Colors.YELLOW}🗑️  To clean up: rm {TEST_DB_PATH}{Colors.END}\n")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error during testing: {e}{Colors.END}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()