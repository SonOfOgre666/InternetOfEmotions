# Internet of Emotions - Backend Architecture

## Overview
Modern microservices architecture for real-time global emotion analysis from social media.

## Architecture Pattern
**Event-Driven Microservices** with message queue-based communication.

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway (8000)                      │
│          Single entry point for all client requests          │
└───────────────┬──────────────────────────────────────────────┘
                │
    ┌───────────┴───────────┬──────────────┬─────────────┐
    ▼                       ▼              ▼             ▼
┌──────────┐         ┌──────────┐   ┌──────────┐  ┌──────────┐
│  Post    │         │   ML     │   │  Stats   │  │  Search  │
│ Fetcher  │────────▶│ Analyzer │   │ Service  │  │ Service  │
└──────────┘         └──────────┘   └──────────┘  └──────────┘
    │                      │
    ▼                      ▼
┌──────────┐         ┌──────────┐
│   URL    │         │ Country  │
│Extractor │────────▶│   Aggr   │
└──────────┘         └──────────┘
```

## Services

### 1. **API Gateway** (Port 8000)
- **Role**: Single entry point, request routing, load balancing
- **Tech**: Flask, CORS enabled
- **Routes**: Proxies to all backend services
- **Dependencies**: None (entry point)

### 2. **Post Fetcher** (Port 5001)
- **Role**: Fetch posts from Reddit for 196 countries
- **Tech**: Flask, PRAW (Reddit API)
- **Events Published**: `post.fetched`
- **Database**: Stores raw posts with metadata
- **Schedule**: Every 5 minutes (configurable)

### 3. **URL Extractor** (Port 5002)
- **Role**: Extract article content from URLs
- **Tech**: Flask, BeautifulSoup, Newspaper3k
- **Events Consumed**: `post.fetched` (for URL posts)
- **Events Published**: `url.extracted`
- **Database**: Updates posts with extracted content

### 4. **ML Analyzer** (Port 5003)
- **Role**: Emotion analysis using transformers
- **Tech**: Flask, HuggingFace Transformers
- **Models**: 
  - RoBERTa (emotion classification)
  - BART (collective events)
  - BERT NER (entity recognition)
- **Events Consumed**: `post.fetched`, `url.extracted`
- **Events Published**: `post.analyzed`
- **Database**: Stores emotion scores
- **Memory**: 4-8GB (model caching)

### 5. **Country Aggregation** (Port 5005)
- **Role**: Aggregate emotions by country
- **Tech**: Flask, PostgreSQL aggregation
- **Events Consumed**: `post.analyzed`
- **Events Published**: `country.updated`
- **Database**: Reads analyzed posts, computes country stats

### 6. **Cache Service** (Port 5006)
- **Role**: Redis-based caching for API responses
- **Tech**: Flask, Redis
- **TTL**: Configurable per endpoint
- **Used By**: API Gateway, Stats Service

### 7. **Search Service** (Port 5007)
- **Role**: Full-text search across posts
- **Tech**: Flask, Elasticsearch
- **Indexes**: Posts by country, emotion, date
- **Query Types**: Text search, filters, aggregations

### 8. **Stats Service** (Port 5008)
- **Role**: Real-time analytics and metrics
- **Tech**: Flask, PostgreSQL
- **Metrics**: 
  - Total posts per country
  - Emotion distribution
  - Trending topics
  - Time-series data

### 9. **DB Cleanup** (Port 5004)
- **Role**: Remove old posts (>30 days based on Reddit creation date)
- **Tech**: Flask, PostgreSQL scheduled jobs
- **Schedule**: Daily at 3 AM

### 10. **Scheduler** (Port 5010)
- **Role**: Smart country prioritization and adaptive timing
- **Tech**: Flask, PostgreSQL
- **Features**: 
  - Country activity scoring
  - Timezone-aware scheduling
  - Adaptive fetch intervals
  - Priority queue management

### 11. **Collective Analyzer** (Port 5011)
- **Role**: Classify posts as collective vs personal events
- **Tech**: Flask, BART transformer model
- **Events Consumed**: `post.analyzed`
- **Events Published**: `post.classified`
- **Database**: Updates posts with collective/personal classification
- **Confidence Threshold**: 0.7 for collective events

### 12. **Cross-Country Detector** (Port 5012)
- **Role**: Detect cross-country mentions in posts
- **Tech**: Flask, BERT NER model, keyword matching
- **Events Consumed**: `post.classified`
- **Events Published**: `cross_country.detected`
- **Database**: Stores cross-country relationships
- **Methods**: NER + keyword extraction + geo-entity matching

---

## Testing

All services have comprehensive unit tests with **440+ test cases** total.

### Run Tests

```bash
# Run all tests with coverage
./run_tests.sh

# Test specific service
cd backend/services/ml_analyzer
pytest test_app.py -v

# Test with coverage report
pytest --cov=app --cov-report=html
```

See [backend/TESTING.md](backend/TESTING.md) for comprehensive testing documentation.
- **Database**: Cascading deletes from raw_posts

### 10. **Smart Scheduler** (Port 5010)
- **Role**: Intelligent country scheduling with priority
- **Tech**: Flask, Priority queue
- **Strategy**: Priority-based with circular rotation fallback
- **Database**: Reads country post counts for priority

### 11. **Collective Analyzer** (Port 5011)
- **Role**: Advanced collective event detection
- **Tech**: Flask, BART model
- **Features**: Topic extraction, event clustering
- **Database**: Stores collective events

### 12. **Cross-Country Detector** (Port 5012)
- **Role**: Multi-country post detection
- **Tech**: Flask, BERT NER
- **Features**: Country entity recognition, post duplication
- **Database**: Stores cross-country mentions
- **Ensures**: Fresh, relevant data only

## Infrastructure Services

### PostgreSQL (Port 5432)
- **Database**: `internet_of_emotions`
- **Tables**: posts, emotions, countries, cache_metadata
- **Shared By**: All services (different access patterns)

### RabbitMQ (Port 5672, 15672)
- **Exchange**: `posts_exchange` (topic)
- **Queues**: Per service
- **Message Flow**: Event-driven async processing
- **Management UI**: http://localhost:15672

### Redis (Port 6379)
- **Purpose**: Response caching, rate limiting
- **TTL**: 60-300 seconds
- **Eviction**: LRU

### Elasticsearch (Port 9200, 9300)
- **Index**: `posts_index`
- **Shards**: Auto-configured
- **Purpose**: Fast text search

## Message Flow

```
1. Post Fetcher finds post
   ├─▶ Stores in DB
   └─▶ Publishes "post.fetched" to RabbitMQ
   
2. URL Extractor receives "post.fetched"
   ├─▶ Extracts article content (if URL post)
   ├─▶ Updates DB
   └─▶ Publishes "url.extracted"
   
3. ML Analyzer receives "post.fetched" OR "url.extracted"
   ├─▶ Runs emotion analysis
   ├─▶ Updates DB with emotion scores
   └─▶ Publishes "post.analyzed"
   
4. Country Aggregation receives "post.analyzed"
   ├─▶ Aggregates by country
   ├─▶ Updates country stats
   └─▶ Publishes "country.updated"
   
5. Frontend polls API Gateway
   └─▶ Returns cached or fresh country data
```

## Environment Variables

### Required for All Services
```bash
DATABASE_URL=postgresql://user:pass@postgres:5432/internet_of_emotions
RABBITMQ_URL=amqp://user:pass@rabbitmq:5672/
LOG_LEVEL=INFO
```

### Post Fetcher Specific
```bash
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=InternetOfEmotions/2.0
MAX_POST_AGE_DAYS=28
FETCH_INTERVAL_SECONDS=300
```

### Cache Service Specific
```bash
REDIS_URL=redis://redis:6379/0
DEFAULT_CACHE_TTL=300
```

### Search Service Specific
```bash
ELASTICSEARCH_URL=http://elasticsearch:9200
```

## Development

### Local Development
```bash
# Start infrastructure
docker compose -f docker-compose.microservices.yml up -d postgres rabbitmq redis

# Run individual service
cd services/post_fetcher
python app.py
```

### Production Deployment
```bash
# Start all services
docker compose -f docker-compose.microservices.yml up -d

# View logs
docker compose -f docker-compose.microservices.yml logs -f

# Check health
curl http://localhost:8000/health
```

## Service Independence

Each service is **fully independent**:
- ✅ Separate codebase in `/services/<service-name>/`
- ✅ Own Dockerfile and dependencies
- ✅ Independent scaling
- ✅ Isolated failure (circuit breaker pattern)
- ✅ Can be deployed separately

## Data Flow Principles

1. **Single Source of Truth**: PostgreSQL for persistent data
2. **Event Sourcing**: RabbitMQ for async processing
3. **Caching Strategy**: Redis for frequently accessed data
4. **Search Optimization**: Elasticsearch for full-text queries
5. **No Direct Service-to-Service Calls**: All via message queue or API Gateway

## Monitoring

- **Health Checks**: Each service exposes `/health` endpoint
- **RabbitMQ Dashboard**: http://localhost:15672 (user: ioe_user)
- **Logs**: Centralized via Docker Compose
- **Metrics**: Prometheus-ready endpoints (optional)

## Redundancy Elimination

### Removed Duplicates
- ❌ Old monolithic backend archived
- ❌ Duplicate emotion analysis logic
- ❌ Redundant Reddit fetching code
- ❌ Inline ML model loading
- ❌ Mixed responsibilities

### Clean Separation
- ✅ One service = One responsibility
- ✅ DRY principle enforced
- ✅ Shared code in common libraries (if needed)
- ✅ Clear service boundaries

## Migration from Monolith

The old monolithic backend has been archived to:
- `archive/old_monolith/backend/`

Key improvements in microservices:
1. **Scalability**: Each service scales independently
2. **Maintainability**: Clear code boundaries
3. **Reliability**: Service isolation prevents cascade failures
4. **Performance**: Parallel processing via message queue
5. **Development**: Teams can work on services independently
