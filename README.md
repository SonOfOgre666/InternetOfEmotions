# 🌍 Internet of Emotions

> **Real-time Global Emotion Analysis Dashboard** - Monitor the collective emotional state of 195+ countries through AI-powered analysis of Reddit posts.

[![Production Ready](https://img.shields.io/badge/status-production%20ready-success)](.)
[![Python](https://img.shields.io/badge/python-3.9+-blue)](.)
[![Next.js](https://img.shields.io/badge/next.js-15-black)](.)
[![Microservices](https://img.shields.io/badge/microservices-6-orange)](.)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [API Reference](#-api-reference)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Overview

**Internet of Emotions** analyzes Reddit posts to track real-time emotional trends across 195+ countries using advanced AI/ML techniques.

### What It Does

- Collects posts from country-specific and news subreddits
- Analyzes emotions using RoBERTa transformer model
- Clusters similar posts into thematic events with AI summaries
- Aggregates country-level emotion statistics
- Visualizes results on interactive world map
- Updates automatically every 30 seconds

### Technology Stack

**Backend:**
- 6 Flask microservices (Python 3.9+)
- SQLite database with WAL mode
- PyTorch + Transformers (RoBERTa emotion model)
- DBSCAN clustering for event extraction
- TF-IDF extractive summarization

**Frontend:**
- Next.js 15 with App Router
- TypeScript + Tailwind CSS
- Leaflet interactive maps
- Real-time data refresh

---

## ✨ Key Features

### 🤖 AI-Powered Analysis

- **RoBERTa Emotion Detection**: `j-hartmann/emotion-english-distilroberta-base`
  - 7 emotions: joy, sadness, anger, fear, surprise, disgust, neutral
  - ~90% classification accuracy
  
- **Event Extraction**: DBSCAN clustering groups similar posts
  - Creates events from both clusters and individual posts
  - Generates concise AI summaries (max 2 sentences, 250 chars)
  - Filters generic content automatically

### 🌐 Global Coverage

- **195+ Countries** with fair circular rotation
- **Smart Data Collection**:
  - Country subreddits (r/Morocco, r/France): Fetch newest posts directly
  - News subreddits (r/worldnews, r/europe): Search by country keyword
  - Automatic rate limiting to avoid Reddit API restrictions

### 🔄 Real-time Updates

- Automated pipeline runs every 30 seconds
- Background processing: Fetch → Extract → Cluster → Analyze → Aggregate
- Frontend auto-refreshes with latest data

---

## 🏗️ Architecture

### System Overview

6 microservices working together to fetch, process, analyze, and aggregate emotion data from Reddit posts across 195+ countries.

```
Data Flow:
Reddit → Data Fetcher → Content Extractor → Event Extractor → ML Analyzer → Aggregator → API Gateway → Frontend
```

### Microservices Diagram

```
┌─────────────────┐
│  Next.js        │
│  Frontend       │  :3000
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  API Gateway    │  :5000 - Routes requests, orchestrates pipeline
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┬──────────┐
    ▼         ▼        ▼        ▼          ▼
┌────────┐ ┌────────┐ ┌──────┐ ┌────────┐ ┌──────────┐
│  Data  │ │Content │ │Event │ │   ML   │ │Aggregator│
│Fetcher │ │Extract │ │Extract│ │Analyzer│ │          │
│  :5001 │ │  :5007 │ │ :5004 │ │  :5005 │ │   :5003  │
└────────┘ └────────┘ └──────┘ └────────┘ └──────────┘
    │          │         │         │           │
    └──────────┴─────────┴─────────┴───────────┘
                        │
                   ┌────▼────┐
                   │ SQLite  │
                   │database │
                   └─────────┘
```

### Service Details

#### 1. Data Fetcher (:5001)

**Purpose**: Fetches Reddit posts for countries using intelligent subreddit strategy

**Key Features**:
- **Circular Rotation**: Fair distribution across all 195+ countries (30 countries per batch)
- **Smart Subreddit Strategy**:
  - Country-name subreddits (r/morocco, r/france): Fetch `.new()` posts directly
  - Regional/news subreddits (r/worldnews, r/europe): `.search()` by country keyword
- **Post Type Classification**: Categorizes as text, link, image, video, or social
- **Rate Limiting**: 0.5s delay between Reddit API calls to avoid 429 errors
- **Parallel Fetching**: ThreadPoolExecutor with 10 workers for concurrent country fetching

**Endpoints**:
- `POST /fetch` - Fetch for specific countries
- `POST /fetch/next-batch` - Fetch next batch in rotation (used by pipeline)
- `POST /cleanup` - Delete posts older than MAX_POST_AGE_DAYS
- `GET /stats` - Get rotation and database stats

#### 2. Content Extractor (:5007)

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

**Endpoints**:
- `POST /extract` - Extract single URL
- `POST /process/pending` - Process all pending posts (used by pipeline)
- `GET /stats` - Get extraction statistics

**Critical Detail**: This service does TWO jobs - extraction AND translation. All non-English content is automatically translated before emotion analysis.

#### 3. Event Extractor (:5004)

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

**Endpoints**:
- `POST /extract_events` - Extract events for countries (or all if empty)
- `GET /health` - Health check

#### 4. ML Analyzer (:5005)

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

**Endpoints**:
- `POST /analyze/event` - Analyze single event
- `POST /process/pending` - Process all pending events (used by pipeline)
- `GET /health` - Health check

#### 5. Aggregator (:5003)

**Purpose**: Country-level emotion aggregation and statistics

**Key Features**:
- **Emotion Averaging**: Averages emotion scores across all country events
- **Post Counting**: Sums total posts across all events (not event count)
- **Top Topics**: Extracts frequent keywords from event titles
- **Case-Insensitive**: Normalizes country names to lowercase

**Endpoints**:
- `POST /aggregate/country/<country>` - Aggregate specific country
- `POST /aggregate/all` - Aggregate all countries (used by pipeline)
- `GET /country/<country>` - Get aggregated data + recent events
- `GET /all` - Get all country emotions
- `GET /health` - Health check

#### 6. API Gateway (:5000)

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

**Frontend API Endpoints**:
- `GET /health` - Gateway health
- `GET /api/health` - Detailed system health
- `GET /api/emotions` - All country emotions
- `GET /api/country/<country>` - Country details with events
- `POST /api/fetch` - Manual data fetch
- `POST /api/trigger_pipeline` - Manual pipeline trigger
- `GET /metrics` - Prometheus metrics

### Database Schema

**SQLite** (`backend/microservices/database.db`)

#### Table: `raw_posts`

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

#### Table: `events`

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

#### Table: `country_emotions`

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

### Data Pipeline Flow

Complete pipeline runs every 30 seconds:

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

### Technical Details

#### Rate Limiting & Performance

- **Reddit API**: 0.5s delay between requests (avoid 429 errors)
- **Parallel Workers**: 10 ThreadPoolExecutor workers for country fetching
- **Batch Size**: 30 countries per rotation cycle
- **Pipeline Cycle**: 30 seconds
- **Cleanup**: Daily deletion of posts >28 days old

#### Timeouts

- Data Fetcher: 90s
- Content Extractor: 120s (allows for translation)
- Event Extractor: 120s (clustering + summarization)
- ML Analyzer: 120s (RoBERTa inference)
- Aggregator: 60s

#### ML Models & Memory

- **RoBERTa**: 500MB, CPU inference, 512 token limit
- **TF-IDF**: Lightweight, no PyTorch, 500 max features
- **DBSCAN**: Scikit-learn, eps=0.75, min_samples=2
- **Translation**: Google Translate API via deep_translator
- **Total Backend**: ~1-2GB (depending on database size)

#### Critical Implementation Notes

1. **Translation is Automatic**: Content Extractor translates ALL non-English content to English before emotion analysis
2. **Individual Posts Become Events**: DBSCAN's `-1` labels (unclustered) are treated as important standalone events
3. **Post Count vs Event Count**: Aggregator counts total POSTS across events, not number of events
4. **Case-Insensitive Countries**: All country lookups normalized to lowercase
5. **Smart Subreddit Strategy**: Country-name subreddits get newest posts; news subreddits are keyword-searched
6. **Extractive Summarization**: Uses TF-IDF sentence scoring (fast, lightweight, no GPU)
7. **Circuit Breakers**: Prevent cascade failures (5 failures → 60s cooldown)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Reddit API credentials ([Get them here](https://www.reddit.com/prefs/apps))

### 1. Get Reddit API Credentials

1. Visit https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in:
   - **Name**: Internet of Emotions
   - **Type**: script
   - **Redirect URI**: http://localhost:8080
4. Copy `client_id` and `client_secret`

### 2. Clone & Setup Backend

```bash
git clone <your-repo-url>
cd internet-of-emotions

# Create virtual environment
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

Create `backend/microservices/.env`:

```bash
# Reddit API (required)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=InternetOfEmotions/1.0

# Optional
MAX_POST_AGE_DAYS=28
DATA_FETCH_WORKERS=10
REDDIT_FETCH_LIMIT=200
```

### 4. Start Backend

```bash
# From project root
./start-backend.sh
```

Services start in background. Logs saved to `/logs/`.

**Check health:**
```bash
curl http://localhost:5000/health
```

### 5. Setup & Start Frontend

```bash
cd frontend
npm install

# Optional: Configure API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:5000" > .env.local

# Start
npm run dev
```

### 6. Access Application

Open **http://localhost:3000**

### Stop Services

```bash
./stop-backend.sh
```

---

## 📡 API Reference

### Base URL
```
http://localhost:5000
```

### Endpoints

#### Health Check
```http
GET /health
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "data-fetcher": "healthy",
    "content-extractor": "healthy",
    "event-extractor": "healthy",
    "ml-analyzer": "healthy",
    "aggregator": "healthy"
  },
  "db_posts": 1234,
  "timestamp": "2025-12-16T10:30:00"
}
```

#### Get All Countries
```http
GET /api/emotions
```

**Response:**
```json
{
  "emotions": {
    "france": {
      "emotions": {
        "joy": 0.35,
        "sadness": 0.25,
        "anger": 0.20,
        "fear": 0.10,
        "surprise": 0.05,
        "disgust": 0.03,
        "neutral": 0.02
      },
      "top_emotion": "joy",
      "confidence": 0.78,
      "post_count": 45,
      "event_count": 12,
      "top_topics": ["climate", "economy", "politics"]
    }
  }
}
```

#### Get Country Details
```http
GET /api/country/<country_name>
```

**Example:** `GET /api/country/france`

**Response:**
```json
{
  "country": "france",
  "emotions": {...},
  "events": [
    {
      "id": 1,
      "title": "French government announces climate policy",
      "description": "Parliament passes new environmental legislation targeting carbon emissions.",
      "post_count": 8,
      "top_emotion": "hope",
      "confidence": 0.82,
      "event_date": "2025-12-16T10:30:00"
    }
  ],
  "posts": [...],
  "top_topics": ["climate", "policy", "environment"]
}
```

#### Manual Data Fetch
```http
POST /api/fetch
Content-Type: application/json

{
  "countries": ["france", "germany"],
  "limit": 50
}
```

#### Trigger Pipeline
```http
POST /api/trigger_pipeline
```

Manually triggers the full data processing pipeline.

---

## ⚙️ Configuration

### Backend Environment Variables

**Location:** `backend/microservices/.env`

```bash
# === Required ===
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx
REDDIT_USER_AGENT=InternetOfEmotions/1.0

# === Optional ===
# Data collection
MAX_POST_AGE_DAYS=28          # Delete posts older than this
DATA_FETCH_WORKERS=10         # Parallel workers
REDDIT_FETCH_LIMIT=200        # Posts per fetch

# Service URLs (default: localhost)
DATA_FETCHER_URL=http://localhost:5001
CONTENT_EXTRACTOR_URL=http://localhost:5007
EVENT_EXTRACTOR_URL=http://localhost:5004
ML_ANALYZER_URL=http://localhost:5005
AGGREGATOR_URL=http://localhost:5003
```

### Frontend Environment Variables

**Location:** `frontend/.env.local`

```bash
NEXT_PUBLIC_API_URL=http://localhost:5000
```

---

## 🔧 Development

### Running Tests

```bash
cd backend/microservices
source ../.venv/bin/activate
pytest tests/ -v
```

### Viewing Logs

```bash
cd logs

# Tail specific service
tail -f data-fetcher.log
tail -f event-extractor.log
tail -f ml-analyzer.log

# View all errors
grep ERROR *.log

# Last 50 lines from all logs
tail -50 *.log
```

### Database Access

```bash
cd backend/microservices

# Open SQLite console
sqlite3 database.db

# Useful queries
SELECT COUNT(*) FROM posts;
SELECT COUNT(*) FROM events;
SELECT country, COUNT(*) as count FROM posts GROUP BY country ORDER BY count DESC LIMIT 10;
SELECT country, title FROM events ORDER BY created_at DESC LIMIT 5;
```

### Manual Service Control

```bash
# Start specific service
cd backend/microservices/<service-name>
source ../../.venv/bin/activate
python app.py

# Check if running
curl http://localhost:<port>/health
```

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check if ports are in use
lsof -i :5000
lsof -i :5001

# Kill all Python microservices
pkill -f "python.*microservices"

# Restart
./stop-backend.sh && sleep 2 && ./start-backend.sh
```

### No Data Appearing

```bash
# Check database
sqlite3 backend/microservices/database.db "SELECT COUNT(*) FROM posts;"

# Manual fetch
curl -X POST http://localhost:5001/fetch \
  -H "Content-Type: application/json" \
  -d '{"countries": ["france"], "limit": 20}'

# Check logs
tail -f logs/data-fetcher.log
```

### Frontend Not Connecting

```bash
# Verify API Gateway
curl http://localhost:5000/health

# Check environment
cat frontend/.env.local

# Rebuild frontend
cd frontend
rm -rf .next
npm run dev
```

### Reddit API Rate Limiting (429 errors)

The system includes automatic 0.5s delays between Reddit requests. If you still see 429 errors:

```bash
# Reduce worker count in .env
DATA_FETCH_WORKERS=5  # instead of 10
REDDIT_FETCH_LIMIT=100  # instead of 200
```

### RoBERTa Model Not Loading

```bash
# Check if model downloaded
ls -lh backend/.venv/lib/python3.*/site-packages/transformers/

# Manually trigger download
cd backend/microservices/ml-analyzer
source ../../.venv/bin/activate
python -c "from transformers import pipeline; pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base')"
```

---

## 📊 System Requirements

- **RAM**: 4GB minimum (8GB recommended for ML models)
- **Disk**: 2GB for ML models + database
- **CPU**: Multi-core recommended for parallel processing
- **OS**: Linux, macOS, or WSL2 on Windows

---

## 📖 Additional Documentation

- **[TEST_SETUP.md](TEST_SETUP.md)** - Detailed testing guide
- **[PRESENTATION.md](PRESENTATION.md)** - Project presentation
- **[frontend/README.md](frontend/README.md)** - Frontend documentation
- **[Présentation_d'Ingénierie_Logicielle.md](Présentation_d'Ingénierie_Logicielle.md)** - French software engineering presentation

---

## 🙏 Acknowledgments

### ML Models

- **RoBERTa**: [j-hartmann/emotion-english-distilroberta-base](https://huggingface.co/j-hartmann/emotion-english-distilroberta-base)
- **VADER**: [vaderSentiment](https://github.com/cjhutto/vaderSentiment)
- **TextBlob**: [TextBlob](https://textblob.readthedocs.io/)

### Libraries

- Flask, PyTorch, Transformers
- Next.js, React, Leaflet
- PRAW (Reddit API), newspaper3k, BeautifulSoup4

---

## 📄 License

MIT License - see LICENSE file for details.

---

**Last Updated**: December 16, 2025  
**Version**: 2.0.0  
**Status**: ✅ Production Ready
