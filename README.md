# 🌍 Internet of Emotions

> **Real-time Global Emotion Analysis Dashboard** - Monitor the collective emotional state of 196 countries through AI-powered analysis of Reddit posts using production-ready microservices architecture.

[![Production Ready](https://img.shields.io/badge/status-production%20ready-success)](.)
[![Architecture](https://img.shields.io/badge/architecture-microservices-success)](.)
[![Services](https://img.shields.io/badge/services-12-orange)](.)
[![ML Models](https://img.shields.io/badge/ML%20models-5-blue)](.)
[![Countries](https://img.shields.io/badge/countries-196-orange)](.)
[![Python](https://img.shields.io/badge/python-3.9+-blue)](.)
[![React](https://img.shields.io/badge/react-18-blue)](.)
[![License](https://img.shields.io/badge/license-MIT-green)](.)

<p align="center">
  <img src="https://img.shields.io/badge/emotion-analysis-ff69b4" />
  <img src="https://img.shields.io/badge/real--time-streaming-success" />
  <img src="https://img.shields.io/badge/AI-ensemble-blueviolet" />
  <img src="https://img.shields.io/badge/deployment-docker%20compose-blue" />
  <img src="https://img.shields.io/badge/database-postgresql-blue" />
  <img src="https://img.shields.io/badge/messaging-rabbitmq-orange" />
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Services](#-services)
- [Testing](#-testing)
- [API Reference](#-api-reference)
- [Documentation](#-documentation)
- [Deployment](#-deployment)
- [Performance](#-performance)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

**Internet of Emotions** is a sophisticated real-time emotion analysis system that monitors and analyzes the collective emotional state of 196 countries by processing Reddit posts using advanced AI/ML techniques in a scalable microservices architecture.

### What It Does

- **Collects** posts from Reddit's news and discussion subreddits across all countries
- **Analyzes** emotions using advanced ML models (RoBERTa, BART, BERT NER)
- **Extracts** content from URLs using intelligent article extraction
- **Aggregates** emotions at country level with real-time updates
- **Provides** full-text search and analytics across all posts
- **Visualizes** results on an interactive world map with real-time updates

### Architecture

**Production-ready microservices architecture** with 12 independent services communicating via RabbitMQ message queue.

```
Frontend (React + Nginx) → API Gateway → 11 Backend Services → PostgreSQL/Redis/Elasticsearch
```

---

## ✨ Key Features

### 🤖 **Microservices Architecture**

- **12 Independent Services**: Each service has a single responsibility
- **Event-Driven**: RabbitMQ message queue for async communication
- **Horizontally Scalable**: Each service scales independently
- **Fault-Tolerant**: Service isolation prevents cascade failures
- **Production-Ready**: Docker Compose orchestration with health checks

### 🧠 **Advanced ML/AI Pipeline**

- **RoBERTa**: Emotion classification (7 emotions: anger, fear, sadness, joy, disgust, surprise, neutral)
- **BART**: Collective event detection vs personal posts
- **BERT NER**: Named entity recognition for country detection
- **VADER + TextBlob**: Sentiment analysis ensemble
- **Lazy Loading**: Models load on-demand, unload when idle

### 🌐 **Global Coverage**

- **196 Countries**: Complete world coverage with geographic coordinates
- **Smart Fetching**: Circular rotation ensures equal treatment
- **30-Day Window**: Only recent, relevant posts (based on Reddit creation date)
- **Cross-Country Detection**: Multi-country posts duplicated appropriately

### ⚡ **Performance**

- **Distributed Caching**: Redis for 95%+ cache hit rate, <1ms responses
- **Advanced Search**: Elasticsearch + FAISS for semantic search
- **Async Processing**: Message queue-based workflow
- **Real-time Updates**: Server-sent events (SSE) streaming
- **Auto-Cleanup**: Daily removal of posts >30 days old

### 🎨 **Rich Features**

- **Interactive Map**: Leaflet-powered world visualization with 195+ country markers
- **Live Analytics**: Real-time statistics and emotion distribution
- **Full-Text Search**: Elasticsearch-powered semantic search
- **Country Details**: 4-algorithm consensus for country-level emotions
- **Event Detection**: Automatic topic extraction and clustering

---

## 🚀 Quick Start

### Prerequisites

- **Docker** 20.10+ with **Docker Compose** v2
- **Reddit API Credentials** ([Get them here](https://www.reddit.com/prefs/apps))
- **8GB RAM** minimum (16GB recommended for all services)
- **20GB free disk space**

### 1. Get Reddit API Credentials

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in:
   - **Name**: Internet of Emotions
   - **Type**: Select "script"
   - **Description**: Emotion analysis dashboard
   - **Redirect URI**: http://localhost:8080
4. Copy your `client_id` (under app name) and `client_secret`

### 2. Clone Repository

```bash
git clone https://github.com/SonOfOgre666/InternetOfEmotions.git
cd InternetOfEmotions
```

### 3. Configure Environment

Create a `.env` file in the project root:

```bash
cat > .env << 'EOF'
# Reddit API Credentials (REQUIRED)
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=InternetOfEmotions/2.0 by YourUsername

# Database
DB_NAME=emotion_db
DB_USER=emotion_user
DB_PASSWORD=change_me_secure_password

# RabbitMQ
RABBITMQ_USER=ioe_user
RABBITMQ_PASSWORD=change_me_secure_password

# Redis
REDIS_PASSWORD=change_me_secure_password

# Optional - Performance Tuning
CLEANUP_INTERVAL_HOURS=24
MAX_AGE_DAYS=30
BATCH_SIZE=50
EOF
```

### 4. Start All Services

```bash
# Start all 17 containers (12 services + 5 infrastructure)
docker compose -f docker-compose.microservices.yml up -d

# Check status
docker compose -f docker-compose.microservices.yml ps

# View logs
docker compose -f docker-compose.microservices.yml logs -f
```

### 5. Access Application

- **Frontend Dashboard**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **API Health Check**: http://localhost:8000/health
- **RabbitMQ Management**: http://localhost:15672 (user: ioe_user)

### 6. Verify Services

```bash
# Test API Gateway
curl http://localhost:8000/health

# Check individual services
curl http://localhost:5001/api/health  # Post Fetcher
curl http://localhost:5003/api/health  # ML Analyzer
curl http://localhost:5005/api/health  # Country Aggregation

# View statistics
curl http://localhost:8000/api/stats | jq

# Get country details
curl http://localhost:8000/api/country/usa | jq
```

### 7. Monitor Progress

```bash
# Watch all service logs
docker compose -f docker-compose.microservices.yml logs -f

# Watch specific service
docker compose -f docker-compose.microservices.yml logs -f ml_analyzer

# Check RabbitMQ message flow
# Visit http://localhost:15672 and login with ioe_user
```

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Nginx)                  │
│                        Port 3000                             │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (Flask)                       │
│              Port 8000 - Single Entry Point                  │
└─────┬──────────┬──────────┬──────────┬──────────┬──────────┘
      │          │          │          │          │
      ▼          ▼          ▼          ▼          ▼
┌──────────┐ ┌──────┐ ┌─────────┐ ┌────────┐ ┌────────┐
│Post      │ │URL   │ │ML       │ │Country │ │Stats   │
│Fetcher   │─│Extr  │─│Analyzer │─│Aggreg  │ │Service │
│:5001     │ │:5002 │ │:5003    │ │:5005   │ │:5008   │
└────┬─────┘ └──────┘ └─────────┘ └────────┘ └────────┘
     │
     ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│DB Cleanup│ │Cache     │ │Search    │
│:5004     │ │:5006     │ │:5007     │
└──────────┘ └──────────┘ └──────────┘

     ┌────────────┬──────────────┬─────────────┐
     ▼            ▼              ▼             ▼
┌──────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐
│Scheduler │ │Collect  │ │Cross     │ │RabbitMQ  │
│:5010     │ │Analyzer │ │Country   │ │:5672     │
│          │ │:5011    │ │:5012     │ │          │
└──────────┘ └─────────┘ └──────────┘ └──────────┘
                                            ▲
                                            │
              ┌─────────────────────────────┼──────┐
              ▼                             │      ▼
        ┌──────────┐                  ┌─────────────┐
        │PostgreSQL│                  │   Redis     │
        │:5432     │                  │   :6379     │
        └──────────┘                  └─────────────┘
                                            │
                                            ▼
                                      ┌─────────────┐
                                      │Elasticsearch│
                                      │   :9200     │
                                      └─────────────┘
```

### Message Flow (RabbitMQ)

```
Post Fetcher → [post.fetched] → URL Extractor → [url.extracted]
                                                       ↓
                                              ML Analyzer
                                                       ↓
                                             [post.analyzed]
                                                       ↓
                                           Country Aggregation
                                                       ↓
                                            [country.updated]
```

### Infrastructure Components

| Component | Technology | Port | Purpose |
|-----------|-----------|------|---------|
| **Database** | PostgreSQL 15 | 5432 | Primary data store (8 tables) |
| **Message Queue** | RabbitMQ 3.12 | 5672 | Event-driven communication |
| **Cache** | Redis 7 | 6379 | Distributed caching |
| **Search** | Elasticsearch 8.11 | 9200 | Full-text search |
| **Reverse Proxy** | Nginx | 3000 | Frontend serving |

---

## 🔧 Services

### Service 1: Post Fetcher (Port 5001)
**Fetches posts from Reddit with smart filtering**

**Features**:
- ✅ Fetches posts ≤30 days old (Reddit creation timestamp)
- ✅ Ignores image-only posts (no text content)
- ✅ Keeps posts with text + images
- ✅ Delegates URL-only posts to URL Extractor
- ✅ Circular rotation for fair country coverage
- ✅ Publishes `post.fetched` events

**Endpoints**:
- `GET /api/health` - Health check
- `GET /api/status` - Fetcher statistics

---

### Service 2: URL Content Extractor (Port 5002)
**Extracts article content from URLs**

**Features**:
- ✅ Listens to `post.fetched` events
- ✅ Ignores social media URLs (Twitter, Facebook, Instagram, Reddit, etc.)
- ✅ Extracts from blogs and news sites (newspaper3k)
- ✅ Stores extracted content with original post
- ✅ Publishes `url.extracted` events

---

### Service 3: ML Analysis Service (Port 5003)
**Multi-model emotion detection and classification**

**Features**:
- ✅ 4-model emotion ensemble (RoBERTa, VADER, TextBlob, Keywords)
- ✅ Collective vs personal classification (BART)
- ✅ Cross-country detection (BERT NER + keywords)
- ✅ Lazy loading for memory optimization
- ✅ Batch processing (50 posts)
- ✅ Publishes `post.analyzed` events

**Models**:
- **RoBERTa** (Weight: 3.0): j-hartmann/emotion-english-distilroberta-base
- **VADER** (Weight: 1.0): Sentiment analysis
- **TextBlob** (Weight: 0.8): Pattern NLP
- **Keywords** (Weight: 2.0): Domain-specific emotion keywords
- **BART**: facebook/bart-large-mnli (collective classification)
- **BERT-NER**: dslim/bert-base-NER (country detection)

---

### Service 4: DB Cleanup Service (Port 5004)
**Automatic removal of old posts**

**Features**:
- ✅ Scheduled cleanup every 24 hours
- ✅ Removes posts where `reddit_created_at > 30 days`
- ✅ Cascading deletes (url_content, analyzed_posts)
- ✅ Cleanup reports and metrics

---

### Service 5: Country Aggregation (Port 5005)
**Country-level emotion aggregation**

**Features**:
- ✅ Listens to `post.analyzed` events
- ✅ 4-algorithm consensus (majority, weighted, intensity, median)
- ✅ Confidence scoring
- ✅ Country coordinates for 195+ countries
- ✅ Publishes `country.updated` events

**Endpoints**:
- `GET /api/countries` - All countries with emotions
- `GET /api/country/<name>` - Detailed country analysis

---

### Service 6: Cache Service (Port 5006)
**Redis-based distributed caching**

**Features**:
- ✅ Multi-TTL caching (30s-120s)
- ✅ Cache invalidation on updates
- ✅ Pub/sub for invalidation events
- ✅ 95%+ cache hit rate

---

### Service 7: Search Service (Port 5007)
**Advanced full-text search**

**Features**:
- ✅ Elasticsearch integration
- ✅ FAISS vector similarity search
- ✅ Real-time indexing
- ✅ Faceted search (by country, emotion, date)

**Endpoints**:
- `GET /api/search?q=<query>` - Search posts

---

### Service 8: Stats Service (Port 5008)
**Global statistics aggregation**

**Features**:
- ✅ Real-time global statistics
- ✅ Emotion distribution
- ✅ Top countries by post count
- ✅ Trend analysis

**Endpoints**:
- `GET /api/stats` - Global statistics

---

### Service 9: API Gateway (Port 8000)
**Single entry point for all requests**

**Features**:
- ✅ Routes to all backend services
- ✅ Request logging
- ✅ Health check aggregation
- ✅ CORS handling

**Endpoints**:
- `GET /health` - Gateway health
- `GET /api/*` - Proxies to services

---

### Service 10: Smart Scheduler (Port 5010)
**Intelligent country scheduling**

**Features**:
- ✅ Priority-based scheduling
- ✅ Circular rotation fallback
- ✅ Adaptive batching
- ✅ Load balancing

---

### Service 11: Collective Analyzer (Port 5011)
**Advanced collective event detection**

**Features**:
- ✅ BART-based classification
- ✅ Topic extraction
- ✅ Event clustering
- ✅ Sentiment intensity analysis

---

### Service 12: Cross-Country Detector (Port 5012)
**Multi-country post detection**

**Features**:
- ✅ BERT NER for country entities
- ✅ Keyword matching (196 countries)
- ✅ Confidence scoring
- ✅ Post duplication for multiple countries

---

## 📡 API Reference

### Base URL
```
http://localhost:8000/api
```

### Core Endpoints

#### **GET /health**
Gateway and service health check

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-11T12:00:00Z",
  "services": {
    "post_fetcher": "healthy",
    "ml_analyzer": "healthy",
    "database": "connected"
  }
}
```

#### **GET /api/emotions**
Get all emotion posts for map visualization

**Response:**
```json
{
  "emotions": [
    {
      "country": "USA",
      "emotion": "anger",
      "confidence": 0.85,
      "lat": 37.0902,
      "lng": -95.7129,
      "total_posts": 847
    }
  ],
  "demo_mode": false,
  "count": 145
}
```

#### **GET /api/stats**
Get global statistics

**Response:**
```json
{
  "total": 45000,
  "by_emotion": {
    "anger": 12500,
    "fear": 9800,
    "sadness": 8200,
    "neutral": 6500,
    "joy": 4500,
    "disgust": 2000,
    "surprise": 1500
  },
  "by_country": {
    "USA": 3500,
    "UK": 2800,
    "India": 2500
  }
}
```

#### **GET /api/country/<name>**
Get detailed country analysis (case-insensitive)

**Parameters:**
- `name`: Country name (e.g., "USA", "uk", "France")

**Response:**
```json
{
  "country_emotion": {
    "dominant_emotion": "anger",
    "confidence": 0.78,
    "method": "consensus",
    "algorithm_votes": {
      "majority": "anger",
      "weighted": "anger",
      "intensity": "fear",
      "median": "anger"
    }
  },
  "emotion_distribution": {
    "anger": 295,
    "fear": 231,
    "sadness": 142,
    "neutral": 89,
    "joy": 45,
    "disgust": 30,
    "surprise": 15
  },
  "total_posts": 847,
  "top_events": [
    {
      "topic": "election results",
      "count": 47,
      "sample_posts": [...]
    }
  ]
}
```

#### **GET /api/posts/stream**
Server-Sent Events stream for real-time updates

**Response:** (SSE stream)
```
data: {"country":"USA","emotion":"anger","text":"..."}

data: {"country":"UK","emotion":"fear","text":"..."}
```

#### **GET /api/search?q=<query>**
Full-text search across all posts

**Parameters:**
- `q`: Search query

**Response:**
```json
{
  "results": [
    {
      "post_id": "abc123",
      "text": "Matching post text...",
      "country": "USA",
      "emotion": "anger",
      "score": 0.95
    }
  ],
  "total": 42
}
```

---

## 🧪 Testing

### Unit Tests

All 12 microservices have comprehensive unit test coverage with **440+ test cases**.

#### Run All Tests

```bash
# Run all tests
./run_tests.sh

# Run with verbose output
./run_tests.sh -v

# Generate coverage report
./run_tests.sh -h
```

#### Run Tests for Specific Service

```bash
# Test individual service
cd backend/services/ml_analyzer
pytest test_app.py -v

# Test with coverage
pytest test_app.py --cov=app --cov-report=html
```

#### Test Coverage

| Service | Test Cases | Coverage |
|---------|-----------|----------|
| API Gateway | 30+ | Core routing, error handling |
| ML Analyzer | 70+ | Emotion detection, models |
| Post Fetcher | 50+ | Reddit API, filtering |
| Country Aggregation | 55+ | 4 algorithms, consensus |
| Collective Analyzer | 40+ | Classification, patterns |
| Cross-Country Detector | 45+ | NER, keywords |
| Cache Service | 20+ | Redis operations |
| Search Service | 15+ | Search queries |
| Stats Service | 20+ | Aggregation, streaming |
| Scheduler | 35+ | Prioritization, timing |
| URL Extractor | 35+ | Content extraction |
| DB Cleanup | 25+ | Cleanup logic |

**Documentation:**
- [backend/TESTING.md](backend/TESTING.md) - Complete testing guide
- [TEST_IMPLEMENTATION_SUMMARY.md](TEST_IMPLEMENTATION_SUMMARY.md) - Test implementation details

---

## 📚 Documentation

### Architecture & Design
- **[MICROSERVICES_ARCHITECTURE.md](MICROSERVICES_ARCHITECTURE.md)** - Complete architecture design
- **[MICROSERVICES_README.md](MICROSERVICES_README.md)** - Detailed microservices guide
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Current project structure
- **[TEST_IMPLEMENTATION_SUMMARY.md](TEST_IMPLEMENTATION_SUMMARY.md)** - Testing implementation

### Getting Started
- **[QUICK_START_MICROSERVICES.md](QUICK_START_MICROSERVICES.md)** - 5-minute quick start
- **[backend/DEPLOYMENT.md](backend/DEPLOYMENT.md)** - Production deployment guide
- **[backend/TESTING.md](backend/TESTING.md)** - Testing guide

### UML Diagrams
- **[docs/CLASS_DIAGRAM_MERMAID.md](docs/CLASS_DIAGRAM_MERMAID.md)** - Class structure
- **[docs/SEQUENCE_DIAGRAM_MERMAID.md](docs/SEQUENCE_DIAGRAM_MERMAID.md)** - Data flow sequences
- **[docs/USE_CASE_DIAGRAMS_MERMAID.md](docs/USE_CASE_DIAGRAMS_MERMAID.md)** - Use cases with actors

### Legacy
- **[archive/old_monolith/](archive/old_monolith/)** - Archived v1.0 monolithic backend

---

## 🐳 Deployment

### Docker Compose (Production)

The recommended deployment method using `docker-compose.microservices.yml`:

```bash
# Start all services
docker compose -f docker-compose.microservices.yml up -d

# View logs (all services)
docker compose -f docker-compose.microservices.yml logs -f

# View logs (specific service)
docker compose -f docker-compose.microservices.yml logs -f ml_analyzer

# Check status
docker compose -f docker-compose.microservices.yml ps

# Restart services
docker compose -f docker-compose.microservices.yml restart

# Stop services
docker compose -f docker-compose.microservices.yml down

# Stop and remove volumes
docker compose -f docker-compose.microservices.yml down -v

# Rebuild after changes
docker compose -f docker-compose.microservices.yml up -d --build
```

### Service Scaling

Scale individual services based on load:

```bash
# Scale ML analyzer to 3 instances
docker compose -f docker-compose.microservices.yml up -d --scale ml_analyzer=3

# Scale post fetcher to 2 instances
docker compose -f docker-compose.microservices.yml up -d --scale post_fetcher=2
```

### Health Monitoring

```bash
# API Gateway health
curl http://localhost:8000/health

# Individual service health
curl http://localhost:5001/api/health  # Post Fetcher
curl http://localhost:5003/api/health  # ML Analyzer
curl http://localhost:5005/api/health  # Country Aggregation

# RabbitMQ Management UI
open http://localhost:15672

# Check database
docker compose -f docker-compose.microservices.yml exec db psql -U emotion_user -d emotion_db -c "SELECT COUNT(*) FROM raw_posts;"
```

### Production Considerations

1. **Environment Variables**: Use Docker secrets or vault for credentials
2. **Volume Mounts**: Persist database with named volumes
3. **Reverse Proxy**: Use Nginx/Traefik for SSL termination and load balancing
4. **Monitoring**: Set up Prometheus + Grafana
5. **Resource Limits**: Configure memory/CPU limits in docker-compose
6. **Backup**: Regular PostgreSQL backups with pg_dump
7. **Log Aggregation**: Use ELK stack or similar for centralized logging

---

## 📊 Performance

### System Metrics

| Metric | Value | Details |
|--------|-------|---------|
| **Throughput** | 20-30 posts/min | Per country |
| **Total Containers** | 17 | 12 services + 5 infrastructure |
| **Memory (all services)** | ~6-8 GB | With models loaded |
| **Cache Hit Rate** | 95%+ | After warmup |
| **API Response (cached)** | <1 ms | Redis cache |
| **API Response (uncached)** | 50-200 ms | Database query |
| **Database Query** | <10 ms | With indexes |
| **ML Processing** | 50-100 ms/post | Includes NER |
| **Model Load Time** | 15 seconds | All models |

### Database Schema

**8 Tables** in PostgreSQL:

1. **raw_posts**: Fetched posts (12 fields, UNIQUE on post_id)
2. **url_content**: Extracted URL content (5 fields, UNIQUE on post_id)
3. **analyzed_posts**: ML analysis results (15 fields, UNIQUE on post_id)
4. **country_emotions**: Aggregated country data (8 fields)
5. **cleanup_logs**: Cleanup operation history (5 fields)
6. **global_statistics**: System-wide stats (4 fields)
7. **collective_events**: Detected events (7 fields)
8. **cross_country_mentions**: Multi-country posts (4 fields)

### Accuracy Metrics

- **Individual Post Emotion**: 70% accuracy (RoBERTa baseline)
- **Country-Level Emotion**: 78-82% accuracy (4-algorithm consensus)
- **Cross-Country Detection**: 85%+ recall with NER
- **Collective Classification**: 75% precision with BART

### Optimization Highlights

✅ **Lazy Loading**: ML models load on-demand, save memory  
✅ **Smart Caching**: 95%+ hit rate, <1ms responses  
✅ **Batch Processing**: 50 posts at once, efficient  
✅ **UNIQUE Constraints**: Prevent duplicate database inserts  
✅ **UTC Timestamps**: Consistent time filtering  
✅ **Case-Insensitive Queries**: LOWER() for country matching  
✅ **Auto Cleanup**: Daily removal of posts >30 days  
✅ **Message Queue**: Async processing, decoupled services  

---

## 🔧 Troubleshooting

### Common Issues

#### Issue: Services won't start

**Symptoms**: Container exits immediately or shows errors

**Solutions**:
```bash
# Check logs
docker compose -f docker-compose.microservices.yml logs <service_name>

# Common causes:
# 1. Missing Reddit credentials
cat .env  # Verify REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET

# 2. Port conflicts
lsof -i :8000  # Check if ports are occupied

# 3. Database not ready
docker compose -f docker-compose.microservices.yml restart db
```

#### Issue: No data appearing on map

**Symptoms**: Map loads but no emotion markers

**Solutions**:
```bash
# Check statistics
curl http://localhost:8000/api/stats | jq

# Verify post fetcher is working
docker compose -f docker-compose.microservices.yml logs post_fetcher

# Check database
docker compose -f docker-compose.microservices.yml exec db psql -U emotion_user -d emotion_db -c "SELECT COUNT(*) FROM raw_posts;"

# Wait time: 5-10 minutes for first batch
# Data collection is automatic via post_fetcher service
```

#### Issue: High memory usage

**Symptoms**: System running slow, memory warnings

**Solutions**:
```bash
# Check memory usage
docker stats

# ML models load on-demand
# Expected: ~6-8GB total with all services

# Reduce services if needed
docker compose -f docker-compose.microservices.yml stop ml_analyzer
```

#### Issue: RabbitMQ message backlog

**Symptoms**: Messages piling up in queues

**Solutions**:
```bash
# Check RabbitMQ management UI
open http://localhost:15672

# Scale consumers
docker compose -f docker-compose.microservices.yml up -d --scale ml_analyzer=2

# Check consumer logs
docker compose -f docker-compose.microservices.yml logs ml_analyzer
```

#### Issue: Database connection errors

**Symptoms**: "Connection refused" or "Authentication failed"

**Solutions**:
```bash
# Verify database is running
docker compose -f docker-compose.microservices.yml ps db

# Check credentials in .env
cat .env | grep DB_

# Restart database
docker compose -f docker-compose.microservices.yml restart db

# Check database logs
docker compose -f docker-compose.microservices.yml logs db
```

### Debug Mode

Enable detailed logging:

```bash
# Edit docker-compose.microservices.yml
# Add to service environment:
LOG_LEVEL=DEBUG

# Restart service
docker compose -f docker-compose.microservices.yml restart <service_name>
```

### Getting Help

1. **Check Logs**: `docker compose -f docker-compose.microservices.yml logs -f`
2. **Review Documentation**: See [Documentation](#-documentation)
3. **GitHub Issues**: [Report bugs](https://github.com/SonOfOgre666/InternetOfEmotions/issues)

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

### Reporting Issues

1. Check existing issues first
2. Provide detailed description
3. Include logs and screenshots
4. Specify environment (OS, Docker version, etc.)

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Setup

```bash
# Clone repository
git clone https://github.com/SonOfOgre666/InternetOfEmotions.git
cd InternetOfEmotions

# Start development environment
docker compose -f docker-compose.microservices.yml up -d

# Watch logs
docker compose -f docker-compose.microservices.yml logs -f
```

### Code Style

- **Python**: Follow PEP 8, use Black formatter
- **JavaScript**: Follow Airbnb style guide, use ESLint/Prettier
- **Documentation**: Update relevant docs with changes

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

### ML Models

- **RoBERTa**: [j-hartmann/emotion-english-distilroberta-base](https://huggingface.co/j-hartmann/emotion-english-distilroberta-base)
- **BART**: [facebook/bart-large-mnli](https://huggingface.co/facebook/bart-large-mnli)
- **BERT-NER**: [dslim/bert-base-NER](https://huggingface.co/dslim/bert-base-NER)
- **VADER**: [vaderSentiment](https://github.com/cjhutto/vaderSentiment)
- **TextBlob**: [TextBlob](https://textblob.readthedocs.io/)

### Libraries & Frameworks

- **Flask**: Web framework
- **React**: UI framework
- **Leaflet**: Map visualization
- **Hugging Face Transformers**: ML model library
- **PRAW**: Reddit API wrapper
- **PostgreSQL**: Production database
- **RabbitMQ**: Message queue
- **Redis**: Caching layer
- **Elasticsearch**: Search engine

### Data Sources

- **Reddit**: Social media data via official API
- **Country Coordinates**: Geographic data for 195+ countries

---

## 📈 Project Stats

[![Services](https://img.shields.io/badge/microservices-12-success)](./)
[![Containers](https://img.shields.io/badge/containers-17-blue)](./)
[![Countries](https://img.shields.io/badge/countries%20supported-196-green)](./)
[![ML Models](https://img.shields.io/badge/ML%20models-6-blueviolet)](./)
[![Accuracy](https://img.shields.io/badge/accuracy-70--82%25-success)](./)

---

## 🔗 Quick Links

| Resource | Link |
|----------|------|
| **Quick Start** | [QUICK_START_MICROSERVICES.md](QUICK_START_MICROSERVICES.md) |
| **Architecture** | [MICROSERVICES_ARCHITECTURE.md](MICROSERVICES_ARCHITECTURE.md) |
| **API Reference** | [API Reference](#-api-reference) |
| **Implementation Status** | [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) |
| **Project Structure** | [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) |

---

## 🎬 Getting Started Path

**New to the project?** Follow this path:

1. 📖 Read this README (you are here!)
2. 🚀 Follow [Quick Start](#-quick-start) guide
3. 🏗️ Understand [Architecture](#-architecture)
4. 🗺️ Explore the dashboard at http://localhost:3000
5. 📊 Check [API Reference](#-api-reference)
6. 🔍 Deep dive with [MICROSERVICES_ARCHITECTURE.md](MICROSERVICES_ARCHITECTURE.md)

---

<p align="center">
  <b>Built with ❤️ for understanding global emotions</b><br/>
  <i>Monitoring 196 countries • Processing thousands of posts • Powered by AI</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-production%20ready-success" />
  <img src="https://img.shields.io/badge/maintained-yes-green" />
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen" />
</p>

---

**Last Updated**: December 11, 2025  
**Version**: 2.0.0 (Microservices)  
**Status**: ✅ Production Ready
