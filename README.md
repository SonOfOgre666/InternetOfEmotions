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

### Microservices

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

| Service | Port | Purpose |
|---------|------|---------|
| **Data Fetcher** | 5001 | Fetches Reddit posts, circular rotation |
| **Content Extractor** | 5007 | Extracts full article content from links |
| **Event Extractor** | 5004 | DBSCAN clustering + AI summarization |
| **ML Analyzer** | 5005 | RoBERTa emotion classification |
| **Aggregator** | 5003 | Country-level statistics |
| **API Gateway** | 5000 | Central routing + background processing |

### Database Schema

**SQLite** (`backend/microservices/database.db`)

**Posts Table:**
```sql
posts (
  id TEXT PRIMARY KEY,
  text TEXT,
  country TEXT,
  timestamp TEXT,
  source TEXT,
  url TEXT,
  author TEXT,
  score INTEGER,
  post_type TEXT,             -- 'text' or 'link'
  needs_extraction INTEGER,   -- 1 if link post
  content_extracted INTEGER,  -- 1 after extraction
  extracted_content TEXT,
  created_at TEXT
)
```

**Events Table:**
```sql
events (
  id INTEGER PRIMARY KEY,
  country TEXT,
  title TEXT,                 -- Event title
  description TEXT,           -- AI-generated summary
  post_ids TEXT,              -- JSON array of post IDs
  event_date TEXT,
  post_count INTEGER,
  emotions TEXT,              -- JSON emotion scores
  top_emotion TEXT,
  confidence REAL,
  created_at TEXT
)
```

**Country Emotions Table:**
```sql
country_emotions (
  country TEXT PRIMARY KEY,
  emotions TEXT,              -- JSON emotion distribution
  top_emotion TEXT,
  confidence REAL,
  post_count INTEGER,
  event_count INTEGER,
  top_topics TEXT,            -- JSON array
  updated_at TEXT
)
```

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
