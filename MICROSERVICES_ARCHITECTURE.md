# 🏗️ Internet of Emotions - Microservices Architecture

## Overview

This document describes the microservices architecture redesign for the Internet of Emotions project. The monolithic application has been decomposed into **12 independent services** for better scalability, maintainability, and fault tolerance.

---

## 🎯 Architecture Benefits

### Why Microservices?

1. **Scalability**: Scale individual services based on load (e.g., ML service needs more resources)
2. **Maintainability**: Each service has a single responsibility
3. **Fault Isolation**: If one service fails, others continue working
4. **Technology Flexibility**: Use different tech stacks per service if needed
5. **Independent Deployment**: Deploy services separately without downtime
6. **Team Autonomy**: Different teams can own different services

---

## 🔧 Service Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     INTERNET OF EMOTIONS                             │
│                   Microservices Architecture                         │
└─────────────────────────────────────────────────────────────────────┘

                           ┌──────────────────┐
                           │   React Frontend │
                           │   (Port 3000)    │
                           └────────┬─────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │   API Gateway    │ ← Single entry point
                           │   (Port 8000)    │   Load balancing, routing
                           │   Kong/NGINX     │   Authentication, rate limiting
                           └────────┬─────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│  Service 1   │          │  Service 2   │          │  Service 3   │
│Post Fetcher  │──────────│URL Extractor │──────────│ ML Analyzer  │
│  (Port 5001) │  Events  │  (Port 5002) │  Events  │  (Port 5003) │
└──────┬───────┘          └──────┬───────┘          └──────┬───────┘
       │                         │                         │
       │   ┌──────────────┐      │    ┌──────────────┐    │
       │   │  Service 4   │      │    │  Service 5   │    │
       └──▶│DB Cleanup    │      └───▶│Country Agg.  │◀───┘
           │  (Port 5004) │           │  (Port 5005) │
           └──────────────┘           └──────────────┘
                  │                          │
        ┌─────────┴──────────────────────────┴─────────┐
        │                                               │
        ▼                                               ▼
┌──────────────┐  ┌──────────────┐          ┌──────────────┐
│  Service 6   │  │  Service 7   │          │  Service 8   │
│Cache Service │  │Search Service│          │ Stats Service│
│  (Port 5006) │  │  (Port 5007) │          │  (Port 5008) │
│  Redis       │  │ Elasticsearch│          │  Aggregator  │
└──────────────┘  └──────────────┘          └──────────────┘
       │                  │                         │
       └──────────────────┼─────────────────────────┘
                          │
              ┌───────────┴────────────┐
              ▼                        ▼
      ┌──────────────┐        ┌──────────────┐
      │Message Queue │        │  PostgreSQL  │
      │  RabbitMQ    │        │  Database    │
      │ (Port 5672)  │        │  (Port 5432) │
      └──────────────┘        └──────────────┘
```

---

## 📦 Service Descriptions

### **Service 1: Post Fetcher Service**
**Port**: 5001
**Responsibility**: Fetch posts from Reddit subreddits

**Features**:
- Fetches posts from news subreddits (≤30 days old)
- Filters out image-only posts (keeps text + image posts)
- Filters out URL-only posts (delegates to URL Extractor)
- Stores post metadata with Reddit creation date
- Uses circular rotation for fair country coverage
- Publishes `post.fetched` events to message queue

**Technologies**:
- Python/Flask
- PRAW (Reddit API)
- RabbitMQ client

**API Endpoints**:
- `POST /api/fetch` - Trigger manual fetch for country/region
- `GET /api/status` - Get fetcher status and queue size
- `GET /api/health` - Health check

**Database Tables**:
- `raw_posts` (id, reddit_id, title, text, url, author, subreddit, reddit_created_at, fetched_at, has_url, country)

---

### **Service 2: URL Content Extractor Service**
**Port**: 5002
**Responsibility**: Extract content from URLs in posts

**Features**:
- Listens to `post.fetched` events
- Detects URLs in post content
- Identifies URL type (blog, news site, social media)
- **Ignores** social media URLs (Twitter, Facebook, Instagram, LinkedIn, Reddit)
- **Extracts** content from blogs and news sites
- Uses newspaper3k, BeautifulSoup for content extraction
- Stores extracted content with original post
- Publishes `url.extracted` events

**Technologies**:
- Python/Flask
- newspaper3k (article extraction)
- BeautifulSoup4
- RabbitMQ client

**URL Type Detection**:
```python
SOCIAL_MEDIA_DOMAINS = [
    'twitter.com', 'facebook.com', 'instagram.com',
    'linkedin.com', 'reddit.com', 'tiktok.com',
    'snapchat.com', 'pinterest.com', 'youtube.com'
]

BLOG_INDICATORS = [
    'medium.com', 'wordpress.com', 'blogger.com',
    'substack.com', 'ghost.io'
]
```

**API Endpoints**:
- `POST /api/extract` - Extract URL content manually
- `GET /api/status` - Get extraction queue status
- `GET /api/health` - Health check

**Database Tables**:
- `url_content` (id, post_id, url, domain, content_type, extracted_text, title, author, published_date, extraction_status)

---

### **Service 3: ML Analysis Service**
**Port**: 5003
**Responsibility**: Emotion detection and classification

**Features**:
- Listens to `url.extracted` and `post.fetched` events
- Multi-model emotion detection (RoBERTa, VADER, TextBlob, Keywords)
- Collective vs personal classification (BART)
- Cross-country detection (NER + keywords)
- Lazy loading of ML models (memory optimization)
- Batch processing (50 posts at a time)
- Publishes `post.analyzed` events

**Technologies**:
- Python/Flask
- Hugging Face Transformers
- PyTorch
- RabbitMQ client

**ML Models**:
- RoBERTa (emotion detection)
- BART (collective classification)
- BERT-NER (country detection)
- VADER, TextBlob (sentiment analysis)

**API Endpoints**:
- `POST /api/analyze` - Analyze post emotion
- `GET /api/models/status` - Check which models are loaded
- `POST /api/models/load` - Load specific model
- `POST /api/models/unload` - Unload specific model
- `GET /api/health` - Health check

**Database Tables**:
- `analyzed_posts` (id, post_id, emotion, confidence, is_collective, detected_countries, analysis_timestamp)

---

### **Service 4: Database Cleanup Service**
**Port**: 5004
**Responsibility**: Auto-remove old posts based on Reddit creation date

**Features**:
- Scheduled cleanup every 24 hours (configurable)
- Removes posts where `reddit_created_at > 30 days`
- Also removes associated data (url_content, analyzed_posts)
- Generates cleanup reports
- Sends metrics to monitoring service
- Can be triggered manually via API

**Technologies**:
- Python/Flask
- APScheduler (scheduling)
- PostgreSQL

**Cleanup Logic**:
```python
# Remove posts older than 30 days (based on Reddit creation date)
DELETE FROM raw_posts
WHERE reddit_created_at < NOW() - INTERVAL '30 days';

# Cascade to related tables
DELETE FROM url_content
WHERE post_id NOT IN (SELECT id FROM raw_posts);

DELETE FROM analyzed_posts
WHERE post_id NOT IN (SELECT id FROM raw_posts);
```

**API Endpoints**:
- `POST /api/cleanup/trigger` - Trigger cleanup manually
- `GET /api/cleanup/status` - Get last cleanup stats
- `GET /api/cleanup/schedule` - Get cleanup schedule
- `PUT /api/cleanup/schedule` - Update cleanup schedule
- `GET /api/health` - Health check

**Database Tables**:
- `cleanup_logs` (id, cleanup_timestamp, posts_removed, url_content_removed, analyzed_posts_removed, duration_seconds)

---

### **Service 5: Country Aggregation Service**
**Port**: 5005
**Responsibility**: Aggregate emotions at country level

**Features**:
- Listens to `post.analyzed` events
- Applies 4-algorithm consensus (majority, weighted, intensity, median)
- Updates country-level emotion statistics
- Calculates confidence scores
- Publishes `country.updated` events

**Technologies**:
- Python/Flask
- NumPy, scikit-learn
- RabbitMQ client

**API Endpoints**:
- `GET /api/country/{name}` - Get country aggregated emotion
- `GET /api/countries` - Get all countries with emotions
- `POST /api/recalculate/{name}` - Recalculate country emotion
- `GET /api/health` - Health check

**Database Tables**:
- `country_emotions` (id, country, dominant_emotion, confidence, algorithm_votes, post_count, last_updated)

---

### **Service 6: Cache Service (Redis)**
**Port**: 5006 (Redis: 6379)
**Responsibility**: Distributed caching for API responses

**Features**:
- Caches API responses with TTLs
- Cache invalidation on data updates
- Multi-TTL strategy (30s-120s)
- Pub/sub for cache invalidation events

**Technologies**:
- Redis
- Python/Flask (management API)

**Cache Keys**:
- `emotions:all` (TTL: 30s)
- `country:{name}:details` (TTL: 120s)
- `stats:global` (TTL: 30s)

---

### **Service 7: Search Service (Elasticsearch)**
**Port**: 5007 (Elasticsearch: 9200)
**Responsibility**: Full-text search, semantic search, hybrid search

**Features**:
- Indexes all posts for full-text search
- FAISS integration for semantic search
- BM25 for keyword search
- Hybrid search (BM25 + FAISS)
- Quality scoring and ranking

**Technologies**:
- Elasticsearch
- FAISS (vector search)
- sentence-transformers
- Python/Flask (API wrapper)

**API Endpoints**:
- `GET /api/search?q={query}` - Keyword search
- `GET /api/semantic_search?q={query}` - Semantic search
- `GET /api/hybrid_search?q={query}` - Hybrid search

---

---

### **Service 9: Scheduler Service**
**Port**: 5010
**Responsibility**: Smart country prioritization and adaptive fetch timing

**Features**:
- Country activity scoring based on past post volume
- Timezone-aware scheduling
- Adaptive fetch intervals (more active countries = more frequent)
- Priority queue management
- Publishes `fetch.scheduled` events

**Technologies**:
- Python/Flask
- APScheduler
- PostgreSQL

**API Endpoints**:
- `GET /api/schedule` - Get current schedule
- `POST /api/prioritize` - Manually adjust priorities
- `GET /api/health` - Health check

**Database Tables**:
- `country_schedule` (country, last_fetch, next_fetch, priority_score, activity_score)

---

### **Service 10: Collective Analyzer Service**
**Port**: 5011
**Responsibility**: Classify posts as collective vs personal events

**Features**:
- Uses BART transformer model for classification
- Keyword-based detection for collective markers
- ML-based confidence scoring
- Publishes `post.classified` events

**Technologies**:
- Python/Flask
- Hugging Face Transformers (BART)
- RabbitMQ client

**API Endpoints**:
- `POST /api/classify` - Classify post
- `GET /api/health` - Health check

**Database Tables**:
- `collective_classifications` (post_id, is_collective, confidence, method)

---

### **Service 11: Cross-Country Detector Service**
**Port**: 5012
**Responsibility**: Detect cross-country mentions in posts

**Features**:
- BERT NER model for entity recognition
- Keyword-based country detection
- Geo-entity matching
- Stores cross-country relationships
- Publishes `cross_country.detected` events

**Technologies**:
- Python/Flask
- Hugging Face Transformers (BERT NER)
- RabbitMQ client

**API Endpoints**:
- `POST /api/detect` - Detect cross-country mentions
- `GET /api/relationships` - Get country relationship graph
- `GET /api/health` - Health check

**Database Tables**:
- `cross_country_mentions` (post_id, source_country, mentioned_country, context, confidence)

---

### **Service 8: Statistics Aggregation Service**
**Port**: 5008
**Responsibility**: Real-time statistics and analytics

**Features**:
- Aggregates global statistics
- Top events extraction
- Emotion distribution by region
- Real-time SSE streaming
- Publishes stats updates

**Technologies**:
- Python/Flask
- Server-Sent Events (SSE)

**API Endpoints**:
- `GET /api/stats` - Global statistics
- `GET /api/stats/stream` - SSE stream
- `GET /api/top_events` - Top global events

---

## 🔄 Message Queue Events

### **Event Types**

| Event | Publisher | Subscribers | Payload |
|-------|-----------|-------------|---------|
| `post.fetched` | Post Fetcher | URL Extractor, ML Analyzer | post_id, reddit_id, text, url, has_url |
| `url.extracted` | URL Extractor | ML Analyzer | post_id, url, extracted_content |
| `post.analyzed` | ML Analyzer | Country Aggregation, Stats | post_id, emotion, confidence, countries |
| `country.updated` | Country Aggregation | Cache Service, Stats | country, dominant_emotion |
| `cache.invalidate` | Any service | Cache Service | cache_key |

### **RabbitMQ Configuration**

**Exchanges**:
- `posts_exchange` (topic) - Post-related events
- `analytics_exchange` (topic) - Analytics events
- `cache_exchange` (fanout) - Cache invalidation

**Queues**:
- `post_fetcher_queue`
- `url_extractor_queue`
- `ml_analyzer_queue`
- `country_aggregation_queue`
- `stats_queue`

---

## 💾 Database Design

### **PostgreSQL Schema**

```sql
-- Service 1: Post Fetcher
CREATE TABLE raw_posts (
    id SERIAL PRIMARY KEY,
    reddit_id VARCHAR(20) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    text TEXT,
    url TEXT,
    author VARCHAR(100),
    subreddit VARCHAR(50),
    score INTEGER DEFAULT 0,
    num_comments INTEGER DEFAULT 0,
    reddit_created_at TIMESTAMP NOT NULL,  -- Reddit post creation date
    fetched_at TIMESTAMP DEFAULT NOW(),     -- When we fetched it
    has_url BOOLEAN DEFAULT FALSE,
    country VARCHAR(100),
    region VARCHAR(50),
    INDEX idx_reddit_created (reddit_created_at),
    INDEX idx_country (country),
    INDEX idx_has_url (has_url)
);

-- Service 2: URL Extractor
CREATE TABLE url_content (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES raw_posts(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    domain VARCHAR(255),
    content_type VARCHAR(50),  -- 'blog', 'news', 'ignored'
    extracted_text TEXT,
    title TEXT,
    author VARCHAR(255),
    published_date TIMESTAMP,
    extraction_status VARCHAR(20),  -- 'pending', 'success', 'failed', 'ignored'
    extracted_at TIMESTAMP DEFAULT NOW(),
    error_message TEXT,
    INDEX idx_post_id (post_id),
    INDEX idx_extraction_status (extraction_status)
);

-- Service 3: ML Analyzer
CREATE TABLE analyzed_posts (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES raw_posts(id) ON DELETE CASCADE,
    emotion VARCHAR(20) NOT NULL,  -- joy, sadness, anger, fear, surprise, disgust, neutral
    confidence FLOAT,
    is_collective BOOLEAN,
    detected_countries TEXT[],  -- Array of detected countries
    analysis_timestamp TIMESTAMP DEFAULT NOW(),
    model_version VARCHAR(50),
    INDEX idx_post_id (post_id),
    INDEX idx_emotion (emotion),
    INDEX idx_is_collective (is_collective)
);

-- Service 4: Cleanup Service
CREATE TABLE cleanup_logs (
    id SERIAL PRIMARY KEY,
    cleanup_timestamp TIMESTAMP DEFAULT NOW(),
    posts_removed INTEGER,
    url_content_removed INTEGER,
    analyzed_posts_removed INTEGER,
    duration_seconds FLOAT,
    status VARCHAR(20)
);

-- Service 5: Country Aggregation
CREATE TABLE country_emotions (
    id SERIAL PRIMARY KEY,
    country VARCHAR(100) UNIQUE NOT NULL,
    dominant_emotion VARCHAR(20),
    confidence FLOAT,
    algorithm_votes JSONB,  -- {majority: 'anger', weighted: 'fear', ...}
    post_count INTEGER,
    last_updated TIMESTAMP DEFAULT NOW(),
    INDEX idx_country (country),
    INDEX idx_last_updated (last_updated)
);

-- Service 8: Statistics
CREATE TABLE global_statistics (
    id SERIAL PRIMARY KEY,
    total_posts INTEGER,
    countries_ready INTEGER,
    emotion_distribution JSONB,
    top_countries JSONB,
    calculated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🐳 Docker Compose Configuration

See [docker-compose.microservices.yml](./docker-compose.microservices.yml) for full configuration.

```yaml
version: '3.8'

services:
  # Infrastructure
  postgres:
    image: postgres:15
    ports: ["5432:5432"]
    environment:
      POSTGRES_DB: internet_of_emotions
      POSTGRES_USER: ioe_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  rabbitmq:
    image: rabbitmq:3-management
    ports: ["5672:5672", "15672:15672"]
    environment:
      RABBITMQ_DEFAULT_USER: ioe_user
      RABBITMQ_DEFAULT_PASS: secure_password

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  elasticsearch:
    image: elasticsearch:8.11.0
    ports: ["9200:9200"]
    environment:
      discovery.type: single-node

  # API Gateway
  api_gateway:
    build: ./services/api_gateway
    ports: ["8000:8000"]
    depends_on:
      - post_fetcher
      - url_extractor
      - ml_analyzer
      - country_aggregation
      - stats_service

  # Microservices
  post_fetcher:
    build: ./services/post_fetcher
    ports: ["5001:5001"]
    depends_on:
      - postgres
      - rabbitmq
    environment:
      DATABASE_URL: postgresql://ioe_user:secure_password@postgres:5432/internet_of_emotions
      RABBITMQ_URL: amqp://ioe_user:secure_password@rabbitmq:5672

  url_extractor:
    build: ./services/url_extractor
    ports: ["5002:5002"]
    depends_on:
      - postgres
      - rabbitmq

  ml_analyzer:
    build: ./services/ml_analyzer
    ports: ["5003:5003"]
    depends_on:
      - postgres
      - rabbitmq
    deploy:
      resources:
        limits:
          memory: 8G

  db_cleanup:
    build: ./services/db_cleanup
    ports: ["5004:5004"]
    depends_on:
      - postgres

  country_aggregation:
    build: ./services/country_aggregation
    ports: ["5005:5005"]
    depends_on:
      - postgres
      - rabbitmq

  cache_service:
    build: ./services/cache_service
    ports: ["5006:5006"]
    depends_on:
      - redis
      - rabbitmq

  search_service:
    build: ./services/search_service
    ports: ["5007:5007"]
    depends_on:
      - elasticsearch
      - postgres

  stats_service:
    build: ./services/stats_service
    ports: ["5008:5008"]
    depends_on:
      - postgres
      - rabbitmq

  # Frontend
  frontend:
    build: ./frontend
    ports: ["3000:80"]
    depends_on:
      - api_gateway

volumes:
  postgres_data:
```

---

## 🚀 Deployment Strategy

### **Development**
```bash
docker-compose -f docker-compose.microservices.yml up
```

### **Production**
- Kubernetes (recommended)
- Docker Swarm
- AWS ECS/Fargate
- Google Cloud Run

### **Kubernetes Deployment**
```yaml
# Example: post-fetcher-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: post-fetcher
spec:
  replicas: 3  # Scale horizontally
  selector:
    matchLabels:
      app: post-fetcher
  template:
    metadata:
      labels:
        app: post-fetcher
    spec:
      containers:
      - name: post-fetcher
        image: ioe/post-fetcher:latest
        ports:
        - containerPort: 5001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

---

## 📊 Monitoring & Observability

### **Prometheus + Grafana**
- Service-level metrics
- Request rates, latencies
- Error rates
- Queue depths

### **ELK Stack (Elasticsearch, Logstash, Kibana)**
- Centralized logging
- Log aggregation from all services
- Search and visualization

### **Jaeger (Distributed Tracing)**
- Trace requests across services
- Identify bottlenecks
- Performance optimization

---

## 🔒 Security Considerations

1. **API Gateway Authentication**: JWT tokens, OAuth2
2. **Service-to-Service Auth**: mTLS (mutual TLS)
3. **Secrets Management**: HashiCorp Vault, AWS Secrets Manager
4. **Rate Limiting**: Per-service and per-user limits
5. **Network Isolation**: Services in private VPC/subnet

---

## 📈 Scalability Benefits

| Service | Scaling Strategy | Bottleneck | Solution |
|---------|------------------|------------|----------|
| Post Fetcher | Horizontal (3-5 replicas) | Reddit API rate limits | Multiple API keys, backoff |
| URL Extractor | Horizontal (2-3 replicas) | Network I/O | Async HTTP, connection pooling |
| ML Analyzer | Vertical (GPU) + Horizontal | Model inference | GPU acceleration, batch processing |
| DB Cleanup | Single instance | N/A | Scheduled task, low resource |
| Country Aggregation | Horizontal (2 replicas) | Computation | In-memory caching |
| Cache Service | Redis Cluster | Memory | Redis Cluster with sharding |
| Search Service | Elasticsearch Cluster | Query complexity | Index optimization, sharding |
| Stats Service | Horizontal (2 replicas) | Aggregation queries | Pre-computed aggregates |

---

## 🔄 Migration Path

### **Phase 1: Extract Services** (Week 1-2)
1. Create Post Fetcher service
2. Create URL Extractor service
3. Set up RabbitMQ

### **Phase 2: ML & Analysis** (Week 3-4)
4. Create ML Analyzer service
5. Create Country Aggregation service
6. Set up PostgreSQL migration

### **Phase 3: Infrastructure** (Week 5-6)
7. Create DB Cleanup service
8. Create Cache Service (Redis)
9. Create Search Service (Elasticsearch)

### **Phase 4: Integration** (Week 7-8)
10. Create API Gateway
11. Create Stats Service
12. Update Frontend to use API Gateway
13. Testing and optimization

---

## 📝 Service Communication Examples

### **Example 1: Post Fetching Flow**
```python
# Service 1: Post Fetcher
def fetch_and_publish():
    posts = reddit.fetch_posts(subreddit='worldnews', max_age_days=30)

    for post in posts:
        # Filter: Ignore image-only posts
        if post.is_image_only():
            continue

        # Store in database
        db_post = db.insert_post({
            'reddit_id': post.id,
            'title': post.title,
            'text': post.selftext,
            'url': post.url if post.url else None,
            'reddit_created_at': datetime.fromtimestamp(post.created_utc),
            'has_url': bool(post.url)
        })

        # Publish event
        rabbitmq.publish('posts_exchange', 'post.fetched', {
            'post_id': db_post.id,
            'reddit_id': post.id,
            'text': post.selftext,
            'url': post.url,
            'has_url': bool(post.url)
        })
```

### **Example 2: URL Extraction Flow**
```python
# Service 2: URL Extractor
def on_post_fetched(event):
    if not event['has_url']:
        return

    url = event['url']
    domain = extract_domain(url)

    # Ignore social media
    if domain in SOCIAL_MEDIA_DOMAINS:
        db.update_url_content(event['post_id'], {
            'extraction_status': 'ignored',
            'content_type': 'social_media'
        })
        return

    # Extract content from blog/news
    try:
        article = newspaper.Article(url)
        article.download()
        article.parse()

        db.insert_url_content({
            'post_id': event['post_id'],
            'url': url,
            'domain': domain,
            'content_type': 'blog' if is_blog(domain) else 'news',
            'extracted_text': article.text,
            'title': article.title,
            'published_date': article.publish_date,
            'extraction_status': 'success'
        })

        # Publish event with extracted content
        rabbitmq.publish('posts_exchange', 'url.extracted', {
            'post_id': event['post_id'],
            'url': url,
            'extracted_content': article.text
        })

    except Exception as e:
        db.update_url_content(event['post_id'], {
            'extraction_status': 'failed',
            'error_message': str(e)
        })
```

### **Example 3: Cleanup Flow**
```python
# Service 4: DB Cleanup
@scheduler.scheduled_job('cron', hour=3)  # Run at 3 AM daily
def cleanup_old_posts():
    start_time = time.time()

    # Remove posts older than 30 days (based on Reddit creation date)
    result = db.execute("""
        DELETE FROM raw_posts
        WHERE reddit_created_at < NOW() - INTERVAL '30 days'
        RETURNING id
    """)

    posts_removed = len(result)

    # Cascade cleanup (handled by foreign keys with ON DELETE CASCADE)
    # Log the cleanup
    db.insert_cleanup_log({
        'cleanup_timestamp': datetime.now(),
        'posts_removed': posts_removed,
        'duration_seconds': time.time() - start_time,
        'status': 'success'
    })

    logger.info(f"Cleanup complete: {posts_removed} posts removed")
```

---

## 🧪 Testing

All **12 microservices** have comprehensive unit tests with **440+ test cases** covering:
- Health endpoints and API routes
- Business logic and algorithms
- Error handling and edge cases
- External dependency mocking (database, RabbitMQ, Redis, ML models)

### Test Framework
- **pytest** 7.4.3 with fixtures and mocking
- **pytest-cov** for coverage reports
- **pytest-mock** for dependency mocking

### Run Tests
```bash
# All services
./run_tests.sh

# Specific service
cd backend/services/ml_analyzer
pytest test_app.py -v --cov=app

# Coverage HTML report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

See [backend/TESTING.md](../backend/TESTING.md) for comprehensive testing documentation.

---

## 🎯 Conclusion

This microservices architecture provides:

✅ **Scalability**: Scale services independently
✅ **Maintainability**: Clear service boundaries
✅ **Fault Tolerance**: Service isolation
✅ **Performance**: Specialized optimization per service
✅ **Flexibility**: Easy to add new services
✅ **Observability**: Better monitoring and debugging

---

**Next Steps**:
1. Review this architecture
2. Approve service boundaries
3. Begin implementation (Phase 1)
