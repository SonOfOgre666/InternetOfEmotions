# Internet of Emotions - Technical Architecture

> Complete system architecture based on actual code implementation

**Last Updated**: December 16, 2025

---

## System Overview

6 microservices working together to fetch, process, analyze, and aggregate emotion data from Reddit posts across 195+ countries.

```
Data Flow:
Reddit → Data Fetcher → Content Extractor → Event Extractor → ML Analyzer → Aggregator → API Gateway → Frontend
```

---

## Service Details

### 1. Data Fetcher (:5001)

**Purpose**: Fetches Reddit posts for countries using intelligent subreddit strategy

**Key Features**:
- **Circular Rotation**: Fair distribution across all 195+ countries (30 countries per batch)
- **Smart Subreddit Strategy**:
  - Country-name subreddits (r/morocco, r/france): Fetch `.new()` posts directly
  - Regional/news subreddits (r/worldnews, r/europe): `.search()` by country keyword
- **Post Type Classification**: Categorizes as text, link, image, video, or social
- **Rate Limiting**: 0.5s delay between Reddit API calls to avoid 429 errors
- **Parallel Fetching**: ThreadPoolExecutor with 10 workers for concurrent country fetching

**Database Operations**:
```sql
INSERT OR IGNORE INTO raw_posts (
  id, text, country, timestamp, source, url, author, score,
  post_type, media_url, link_url, needs_extraction
)
```

**Important Fields**:
- `post_type`: 'text' | 'link' | 'image' | 'video' | 'social'
- `needs_extraction`: 1 for link posts requiring article extraction
- `link_url`: URL to extract content from (for link posts)

**Endpoints**:
- `POST /fetch` - Fetch for specific countries
- `POST /fetch/next-batch` - Fetch next batch in rotation (used by pipeline)
- `POST /cleanup` - Delete posts older than MAX_POST_AGE_DAYS
- `GET /stats` - Get rotation and database stats

---

### 2. Content Extractor (:5007)

**Purpose**: Extracts full article content from link posts AND translates non-English content to English

**Key Features**:
- **Article Extraction**: Uses BeautifulSoup to extract main content from news URLs
  - Removes scripts, styles, nav, footer, aside
  - Finds article containers (`<article>`, `.post-content`, etc.)
  - Extracts paragraphs >50 chars, limits to 1000 chars
- **Language Detection**: Uses `langdetect` to identify non-English content
- **Translation**: Uses `deep_translator.GoogleTranslator` to translate to English
  - Handles chunks for long text (max 4500 chars per chunk)
  - Translates both title and article content
  - Preserves context across chunks
- **Social Media Filtering**: Skips Twitter, Facebook, Instagram, LinkedIn (require login)

**Database Operations**:
```sql
-- Finds posts needing extraction or translation
SELECT id, text, link_url FROM raw_posts 
WHERE needs_extraction = 1 OR needs_extraction = 0

-- Updates with extracted + translated content
UPDATE raw_posts 
SET text = ?, needs_extraction = 0 
WHERE id = ?
```

**Processing Flow**:
1. Check if `link_url` exists → Extract article content
2. Combine title + extracted content
3. Detect language → Translate to English if needed
4. Update `text` field with translated content
5. Set `needs_extraction = 0`

**Endpoints**:
- `POST /extract` - Extract single URL
- `POST /process/pending` - Process all pending posts (used by pipeline)
- `GET /stats` - Get extraction statistics

**Critical Detail**: This service does TWO jobs - extraction AND translation. All non-English content is automatically translated before emotion analysis.

---

### 3. Event Extractor (:5004)

**Purpose**: Groups similar posts into thematic events with AI-generated summaries

**Key Features**:
- **DBSCAN Clustering**: Density-based clustering using TF-IDF vectors
  - `eps=0.75` (25% similarity threshold) - lenient to ensure related topics cluster
  - `min_samples=2` - at least 2 posts to form cluster
  - Uses cosine similarity on TF-IDF vectors
- **Individual Events**: Unclustered posts (-1 label) become standalone events
- **Extractive Summarization**: TF-IDF sentence scoring (no PyTorch needed)
  - Ranks sentences by content relevance, position, and length
  - Max 2 sentences, 250 character limit
  - Filters generic content (AMA, "Hi everyone", "Looking for advice")
  - Sorts by original position for natural reading flow
- **Title Generation**: Uses first sentence from most recent post (max 200 chars)

**Database Operations**:
```sql
-- Gets unprocessed posts from last 7 days
SELECT id, text, timestamp, url, source, post_type
FROM raw_posts
WHERE country = ? AND timestamp > ? 
  AND needs_extraction = 0
  AND post_type IN ('text', 'link', 'image', 'video', 'social')
  AND id NOT IN (SELECT post_ids FROM events)

-- Inserts event
INSERT INTO events (
  country, title, description, post_ids, event_date, post_count
) VALUES (?, ?, ?, ?, ?, ?)
```

**Summarization Algorithm**:
1. TF-IDF vectorization with expanded stopwords
2. Sentence scoring: `content_score + position_bonus - length_penalty`
3. Filter sentences 20-200 chars
4. Select top 2 sentences by score
5. Sort by original position
6. Limit to 250 chars total

**Endpoints**:
- `POST /extract_events` - Extract events for countries (or all if empty)
- `GET /health` - Health check

---

### 4. ML Analyzer (:5005)

**Purpose**: Emotion classification using RoBERTa transformer model

**Key Features**:
- **RoBERTa Model**: `j-hartmann/emotion-english-distilroberta-base`
  - 7 emotions: joy, sadness, anger, fear, surprise, disgust, neutral
  - ~500MB model size
  - CPU inference (device=-1)
  - Processes 512 tokens max
- **VADER Fallback**: If RoBERTa fails or unavailable
  - Maps compound score to joy/sadness/neutral
  - Lower confidence (0.5-0.6)
- **No Collective Filtering**: All posts from news subreddits assumed collective

**Database Operations**:
```sql
-- Finds unanalyzed events
SELECT id, title, description 
FROM events 
WHERE is_analyzed = 0 
LIMIT 50

-- Updates with emotion analysis
UPDATE events 
SET emotion = ?, confidence = ?, is_analyzed = 1 
WHERE id = ?
```

**Processing**:
1. Get pending events (is_analyzed = 0)
2. Combine title + description for analysis
3. Run through RoBERTa classifier
4. Extract top emotion and confidence
5. Update event with results

**Endpoints**:
- `POST /analyze/event` - Analyze single event
- `POST /process/pending` - Process all pending events (used by pipeline)
- `GET /health` - Health check

---

### 5. Aggregator (:5003)

**Purpose**: Country-level emotion aggregation and statistics

**Key Features**:
- **Emotion Averaging**: Averages emotion scores across all country events
- **Post Counting**: Sums total posts across all events (not event count)
- **Top Topics**: Extracts frequent keywords from event titles
- **Case-Insensitive**: Normalizes country names to lowercase

**Database Operations**:
```sql
-- Gets analyzed events for country
SELECT emotion, confidence, post_ids 
FROM events 
WHERE LOWER(country) = ? AND is_analyzed = 1

-- Stores aggregated data
INSERT OR REPLACE INTO country_emotions (
  country, emotions, top_emotion, total_posts, last_updated
) VALUES (?, ?, ?, ?, ?)
```

**Aggregation Logic**:
1. Get all analyzed events for country
2. Sum emotion confidences across events
3. Divide by event count for average
4. Count total posts from post_ids JSON
5. Identify top emotion

**Endpoints**:
- `POST /aggregate/country/<country>` - Aggregate specific country
- `POST /aggregate/all` - Aggregate all countries (used by pipeline)
- `GET /country/<country>` - Get aggregated data + recent events
- `GET /all` - Get all country emotions
- `GET /health` - Health check

---

### 6. API Gateway (:5000)

**Purpose**: Central routing, orchestration, and background processing

**Key Features**:
- **Background Pipeline**: Runs every 30 seconds
  1. Cleanup old posts (daily)
  2. Fetch new posts (next batch)
  3. Extract article content + translate
  4. Extract events from posts
  5. Analyze emotions (RoBERTa)
  6. Aggregate country emotions
- **Circuit Breakers**: Prevents cascade failures (fail_max=5, reset_timeout=60s)
- **Retry Logic**: Exponential backoff for transient failures
- **Error Tracking**: Sentry integration for production monitoring
- **Metrics**: Prometheus-compatible metrics at `/metrics`

**Background Processing Thread**:
```python
while processing_active:
    # 30-second cycle
    cleanup_old_posts()  # Daily
    fetch_next_batch()   # 90s timeout
    extract_content()    # 120s timeout
    extract_events()     # 120s timeout
    analyze_emotions()   # 120s timeout
    aggregate_emotions() # 60s timeout
    time.sleep(30)
```

**Frontend API Endpoints**:
- `GET /health` - Gateway health
- `GET /api/health` - Detailed system health
- `GET /api/emotions` - All country emotions
- `GET /api/country/<country>` - Country details with events
- `POST /api/fetch` - Manual data fetch
- `POST /api/trigger_pipeline` - Manual pipeline trigger
- `GET /metrics` - Prometheus metrics

---

## Database Schema

### Table: `raw_posts`

```sql
CREATE TABLE raw_posts (
  id TEXT PRIMARY KEY,              -- Reddit post ID
  text TEXT,                        -- Post text (title + content, translated to English)
  country TEXT,                     -- Country name
  timestamp TEXT,                   -- Reddit post timestamp (ISO format)
  source TEXT,                      -- Domain (e.g., 'bbc.com')
  url TEXT,                         -- Full Reddit URL
  author TEXT,                      -- Reddit username
  score INTEGER,                    -- Reddit upvotes
  post_type TEXT,                   -- 'text', 'link', 'image', 'video', 'social'
  media_url TEXT,                   -- URL to image/video
  link_url TEXT,                    -- URL to external article (if link post)
  needs_extraction INTEGER,         -- 1 if needs article extraction
  content_extracted INTEGER,        -- 1 after extraction complete
  extracted_content TEXT,           -- Full article text (deprecated)
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### Table: `events`

```sql
CREATE TABLE events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  country TEXT,                     -- Country name
  title TEXT,                       -- Event title (first sentence of recent post)
  description TEXT,                 -- AI-generated summary (max 250 chars, 2 sentences)
  post_ids TEXT,                    -- JSON array of post IDs in this event
  event_date TEXT,                  -- Timestamp of most recent post
  post_count INTEGER,               -- Number of posts in event
  emotion TEXT,                     -- Top emotion from RoBERTa
  confidence REAL,                  -- Emotion confidence score
  is_analyzed INTEGER DEFAULT 0,   -- 1 after ML analysis complete
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### Table: `country_emotions`

```sql
CREATE TABLE country_emotions (
  country TEXT PRIMARY KEY,         -- Country name
  emotions TEXT,                    -- JSON emotion distribution
  top_emotion TEXT,                 -- Dominant emotion
  confidence REAL,                  -- Top emotion confidence
  total_posts INTEGER,              -- Total posts across all events
  event_count INTEGER,              -- Number of events
  top_topics TEXT,                  -- JSON array of frequent keywords
  last_updated TEXT                 -- Last aggregation timestamp
);
```

---

## Data Pipeline Flow

### Complete Pipeline (30-second cycle)

```
1. Data Fetcher
   ↓ Fetches 30 countries (5-30 posts each)
   ↓ Inserts into raw_posts (needs_extraction=1 for link posts)
   
2. Content Extractor
   ↓ Finds posts with needs_extraction=1
   ↓ Extracts article content from link_url
   ↓ Detects language → Translates to English
   ↓ Updates text field with translated content
   ↓ Sets needs_extraction=0
   
3. Event Extractor
   ↓ Gets posts where needs_extraction=0 (last 7 days)
   ↓ TF-IDF vectorization → DBSCAN clustering
   ↓ Creates events from clusters + individual posts
   ↓ Generates extractive summaries (2 sentences, 250 chars)
   ↓ Inserts into events (is_analyzed=0)
   
4. ML Analyzer
   ↓ Gets events where is_analyzed=0
   ↓ RoBERTa emotion classification (7 emotions)
   ↓ Updates events with emotion + confidence
   ↓ Sets is_analyzed=1
   
5. Aggregator
   ↓ Gets all events where is_analyzed=1
   ↓ Groups by country → averages emotions
   ↓ Counts total posts (not events)
   ↓ Inserts/updates country_emotions
   
6. Frontend
   ↓ Fetches /api/emotions
   ↓ Displays on interactive map
```

---

## Key Technical Details

### Rate Limiting & Performance

- **Reddit API**: 0.5s delay between requests (avoid 429 errors)
- **Parallel Workers**: 10 ThreadPoolExecutor workers for country fetching
- **Batch Size**: 30 countries per rotation cycle
- **Pipeline Cycle**: 30 seconds
- **Cleanup**: Daily deletion of posts >28 days old

### Timeouts

- Data Fetcher: 90s
- Content Extractor: 120s (allows for translation)
- Event Extractor: 120s (clustering + summarization)
- ML Analyzer: 120s (RoBERTa inference)
- Aggregator: 60s

### ML Models

- **RoBERTa**: 500MB, CPU inference, 512 token limit
- **TF-IDF**: Lightweight, no PyTorch, 500 max features
- **DBSCAN**: Scikit-learn, eps=0.75, min_samples=2
- **Translation**: Google Translate API via deep_translator

### Memory Usage

- RoBERTa Model: ~500MB
- VADER: <10MB
- TF-IDF Vectorizer: <50MB
- Total Backend: ~1-2GB (depending on database size)

---

## Environment Variables

```bash
# Reddit API (required)
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx
REDDIT_USER_AGENT=InternetOfEmotions/1.0

# Data collection
MAX_POST_AGE_DAYS=28          # Delete old posts
DATA_FETCH_WORKERS=10         # Parallel workers
REDDIT_FETCH_LIMIT=200        # Posts per fetch

# Services (defaults to localhost)
DATA_FETCHER_URL=http://localhost:5001
CONTENT_EXTRACTOR_URL=http://localhost:5007
EVENT_EXTRACTOR_URL=http://localhost:5004
ML_ANALYZER_URL=http://localhost:5005
AGGREGATOR_URL=http://localhost:5003

# Monitoring (optional)
SENTRY_DSN=xxx                # Error tracking
ENVIRONMENT=production
VERSION=2.0.0
```

---

## Critical Implementation Notes

1. **Translation is Automatic**: Content Extractor translates ALL non-English content to English before emotion analysis. This happens transparently.

2. **Individual Posts Become Events**: DBSCAN's `-1` labels (noise/unclustered) are treated as important standalone events, not discarded.

3. **Post Count vs Event Count**: Aggregator counts total POSTS across events, not number of events. This gives better representation of discussion volume.

4. **Case-Insensitive Countries**: All country lookups are normalized to lowercase for consistency.

5. **Smart Subreddit Strategy**: Country-name subreddits get newest posts directly (more relevant local content), while news subreddits are keyword-searched (filters for country mentions).

6. **Extractive Summarization**: Uses TF-IDF sentence scoring, not neural models. Fast, lightweight, no GPU needed.

7. **Circuit Breakers**: Prevent cascade failures. If a service fails 5 times, circuit opens for 60s to allow recovery.

---

**Version**: 2.0.0  
**Status**: ✅ Production Ready  
**Last Updated**: December 16, 2025
