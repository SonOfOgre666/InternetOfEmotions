# API Documentation

## Base URL
```
http://localhost:8000
```

## Health Check

### GET /health
Check API Gateway health and connected services.

**Response:**
```json
{
  "status": "healthy",
  "service": "api_gateway",
  "timestamp": "2025-12-10T12:00:00",
  "services": [
    "post_fetcher",
    "url_extractor",
    "ml_analyzer",
    "db_cleanup",
    "country_aggregation",
    "cache",
    "search",
    "stats",
    "scheduler",
    "collective_analyzer",
    "cross_country_detector"
  ]
}
```

## Country Emotions

### GET /api/emotions
Get emotion data for all countries.

**Response:**
```json
{
  "countries": [
    {
      "country": "United States",
      "latitude": 37.0902,
      "longitude": -95.7129,
      "emotions": {
        "joy": 0.45,
        "sadness": 0.20,
        "anger": 0.15,
        "fear": 0.10,
        "surprise": 0.05,
        "neutral": 0.05
      },
      "dominant_emotion": "joy",
      "post_count": 156,
      "last_updated": "2025-12-10T11:45:00"
    }
  ],
  "total_countries": 196,
  "last_updated": "2025-12-10T11:45:00"
}
```

### GET /api/country_aggregation/country/{country_name}
Get detailed emotion data for a specific country.

**Parameters:**
- `country_name` (path): Country name (case-insensitive)

**Response:**
```json
{
  "country": "France",
  "emotions": {
    "joy": 0.35,
    "sadness": 0.25,
    "anger": 0.20,
    "fear": 0.10,
    "surprise": 0.05,
    "neutral": 0.05
  },
  "recent_posts": [
    {
      "title": "Paris celebrates...",
      "emotion": "joy",
      "score": 0.85,
      "created_at": "2025-12-10T10:30:00"
    }
  ],
  "post_count": 87
}
```

## Statistics

### GET /api/stats
Get global statistics and trends.

**Response:**
```json
{
  "total_posts": 12456,
  "total_countries": 196,
  "active_countries": 178,
  "global_emotions": {
    "joy": 0.32,
    "sadness": 0.28,
    "anger": 0.18,
    "fear": 0.12,
    "surprise": 0.06,
    "neutral": 0.04
  },
  "trending_topics": [
    {"topic": "climate", "count": 234},
    {"topic": "economy", "count": 189}
  ],
  "last_24h": {
    "new_posts": 1234,
    "analyzed_posts": 1200
  }
}
```

### GET /api/stats/timeline
Get emotion trends over time.

**Query Parameters:**
- `days` (optional): Number of days (default: 7, max: 30)
- `country` (optional): Filter by country

**Response:**
```json
{
  "timeline": [
    {
      "date": "2025-12-09",
      "emotions": {
        "joy": 0.30,
        "sadness": 0.25,
        "anger": 0.20
      },
      "post_count": 523
    }
  ]
}
```

## Search

### GET /api/search
Search posts by text, country, or emotion.

**Query Parameters:**
- `q` (required): Search query
- `country` (optional): Filter by country
- `emotion` (optional): Filter by dominant emotion
- `limit` (optional): Results limit (default: 50, max: 200)
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "results": [
    {
      "post_id": "abc123",
      "title": "Breaking news...",
      "country": "Germany",
      "emotion": "surprise",
      "score": 0.78,
      "url": "https://...",
      "created_at": "2025-12-10T09:15:00"
    }
  ],
  "total": 156,
  "limit": 50,
  "offset": 0
}
```

## Cache Management

### DELETE /api/cache/clear
Clear all cached data (admin only).

**Response:**
```json
{
  "status": "success",
  "cleared_keys": 234,
  "message": "Cache cleared successfully"
}
```

### GET /api/cache/stats
Get cache statistics.

**Response:**
```json
{
  "total_keys": 456,
  "memory_used": "12.5 MB",
  "hit_rate": 0.87,
  "evictions": 23
}
```

## Service-Specific Endpoints

### Post Fetcher

#### POST /api/post_fetcher/fetch
Manually trigger post fetching for specific country.

**Body:**
```json
{
  "country": "Japan",
  "limit": 25
}
```

### URL Extractor

#### POST /api/url_extractor/extract
Extract content from a URL.

**Body:**
```json
{
  "url": "https://example.com/article"
}
```

**Response:**
```json
{
  "url": "https://example.com/article",
  "title": "Article Title",
  "content": "Full article text...",
  "author": "John Doe",
  "publish_date": "2025-12-10"
}
```

### ML Analyzer

#### POST /api/ml_analyzer/analyze
Analyze text for emotions.

**Body:**
```json
{
  "text": "This is amazing news for everyone!"
}
```

**Response:**
```json
{
  "emotions": {
    "joy": 0.85,
    "surprise": 0.10,
    "neutral": 0.05
  },
  "dominant_emotion": "joy",
  "sentiment": "positive",
  "entities": ["news"]
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid request parameters",
  "details": "Missing required field: country"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found",
  "resource": "country",
  "requested": "Atlantis"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "Database connection failed"
}
```

### 503 Service Unavailable
```json
{
  "error": "Service unavailable",
  "service": "ml_analyzer",
  "message": "Service is currently down"
}
```

### 504 Gateway Timeout
```json
{
  "error": "Service timeout",
  "service": "url_extractor",
  "message": "Request exceeded 30 second timeout"
}
```

## Rate Limiting

All endpoints are rate-limited:
- **Default**: 100 requests per minute per IP
- **Search**: 30 requests per minute per IP
- **POST endpoints**: 20 requests per minute per IP

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1702213200
```

## CORS

CORS is enabled for all origins in development. In production, configure allowed origins in API Gateway environment variables.

## Versioning

Current API version: **v1**

Future versions will be available at:
- `/api/v2/...`
- `/api/v3/...`
