# Backend Integration Guide

This document explains how the new Next.js frontend connects to the Python Flask backend.

## Architecture Overview

```
┌─────────────────────┐         ┌─────────────────────┐
│   Next.js Frontend  │ ◄─────► │   Flask Backend     │
│   (Port 3000)       │   HTTP  │   (Port 5000)       │
│                     │   SSE   │                     │
└─────────────────────┘         └─────────────────────┘
```

## Connection Flow

### 1. Initial Data Load

On page load, the frontend fetches initial data:

```typescript
// 1. Check backend health
GET /api/health
Response: { status: "ok", demo_mode: false, db_posts: 1234 }

// 2. Fetch emotion data
GET /api/emotions
Response: { emotions: [...], count: 100, countries_ready: 45 }

// 3. Fetch statistics
GET /api/stats
Response: { total: 1234, by_emotion: {...}, by_country: {...} }
```

### 2. Real-time Updates (SSE)

The frontend connects to Server-Sent Events stream:

```typescript
EventSource → /api/posts/stream

// Receives new posts in real-time
{
  id: "post_123",
  country: "United States",
  emotion: "joy",
  confidence: 85,
  title: "Breaking news...",
  timestamp: 1234567890
}
```

### 3. Data Transformation

Backend posts are transformed into the frontend's `CountryData` format:

```typescript
// Backend format
{
  id: string,
  country: string,
  emotion: Emotion,
  confidence: number,
  title: string,
  ...
}

// Frontend format
{
  iso: string,
  name: string,
  emoji: string,
  emotion: Emotion,
  confidence: number,
  postCount: number,
  distribution: Record<Emotion, number>,
  ...
}
```

## Key Files

### Frontend

- **`src/lib/api.ts`** - API client functions
  - `fetchEmotions()` - Get emotion data
  - `fetchStats()` - Get statistics
  - `fetchHealth()` - Check backend status
  - `createPostStream()` - Create SSE connection

- **`src/lib/useBackend.ts`** - React hook for backend integration
  - Manages connection state
  - Transforms backend data to frontend format
  - Handles reconnection logic
  - Provides fallback to mock data

- **`src/app/page.tsx`** - Main page using the hook
  - Uses `useBackend()` hook
  - Displays connection status
  - Toggles between backend and mock data

### Backend

- **`backend/app.py`** - Flask API server
  - `/api/emotions` - Returns analyzed posts
  - `/api/stats` - Returns statistics
  - `/api/health` - Health check endpoint
  - `/api/posts/stream` - SSE stream for real-time updates

## Environment Configuration

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:5000
```

### Backend (.env)

```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=EmotionsDashboard/1.0
```

## Running Both Services

### Option 1: Separate Terminals

**Terminal 1 - Backend:**
```bash
cd backend
python app.py
# Runs on http://localhost:5000
```

**Terminal 2 - Frontend:**
```bash
cd new-frontend
npm run dev
# Runs on http://localhost:3000
```

### Option 2: Production Build

**Terminal 1 - Backend:**
```bash
cd backend
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd new-frontend
npm run build
npm start
# Runs on http://localhost:3000
```

## Connection States

The frontend manages three connection states:

1. **Connected (● LIVE)**
   - SSE stream active
   - Receiving real-time updates
   - Green indicator

2. **Connecting (○ CONNECTING...)**
   - Backend reachable
   - Attempting SSE connection
   - Yellow indicator

3. **Offline (⚠ BACKEND OFFLINE)**
   - Cannot reach backend
   - Auto-retry every 10 seconds
   - Red indicator
   - Option to use mock data

## Error Handling

### Backend Unavailable

```typescript
try {
  const data = await fetchEmotions();
  // Success
} catch (error) {
  // Fallback to mock data
  setUseMockData(true);
}
```

### SSE Connection Lost

```typescript
eventSource.onerror = () => {
  setIsConnected(false);
  // Retry after 10 seconds
  setTimeout(() => reconnect(), 10000);
};
```

## CORS Configuration

The backend enables CORS for all origins:

```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
```

For production, restrict to specific origins:

```python
CORS(app, origins=['http://localhost:3000', 'https://yourdomain.com'])
```

## API Response Examples

### GET /api/emotions

```json
{
  "emotions": [
    {
      "id": "post_123",
      "country": "United States",
      "emotion": "joy",
      "confidence": 85,
      "title": "Great news today",
      "text": "...",
      "timestamp": 1702234567,
      "subreddit": "news",
      "url": "https://reddit.com/...",
      "latitude": 40.7128,
      "longitude": -74.0060
    }
  ],
  "count": 150,
  "countries_ready": 45,
  "max_age_days": 28
}
```

### GET /api/stats

```json
{
  "total": 1234,
  "by_emotion": {
    "joy": 345,
    "anger": 234,
    "fear": 189,
    "sadness": 156,
    "neutral": 200,
    "surprise": 67,
    "disgust": 43
  },
  "by_country": {
    "United States": 456,
    "United Kingdom": 234,
    "Germany": 189
  },
  "countries_ready": 45,
  "max_age_days": 28
}
```

### SSE Stream Event

```
data: {"id":"post_456","country":"Germany","emotion":"joy","confidence":78,"title":"Economic growth reported","timestamp":1702234890,...}
```

## Testing the Connection

1. **Start backend:**
   ```bash
   cd backend && python app.py
   ```

2. **Test health endpoint:**
   ```bash
   curl http://localhost:5000/api/health
   ```

3. **Start frontend:**
   ```bash
   cd new-frontend && npm run dev
   ```

4. **Check browser console** for connection logs:
   - `✓ Connected to emotion stream` = Success
   - Connection errors = Check backend URL

## Troubleshooting

### "Failed to fetch" errors

- ✅ Backend running on port 5000
- ✅ CORS enabled in backend
- ✅ `NEXT_PUBLIC_API_URL` set correctly
- ✅ No firewall blocking ports

### SSE not connecting

- ✅ Backend `/api/posts/stream` endpoint working
- ✅ Browser supports EventSource
- ✅ No ad blockers interfering

### No data showing

- ✅ Backend has analyzed posts in database
- ✅ Check `GET /api/emotions` returns data
- ✅ Frontend transformation logic working
- ✅ Try mock data mode to isolate issue

## Production Deployment

### Frontend (Vercel/Netlify)

Set environment variable:
```
NEXT_PUBLIC_API_URL=https://your-backend-api.com
```

### Backend (Railway/Heroku/VPS)

Ensure:
- CORS allows frontend domain
- SSE endpoint accessible
- Ports properly configured

## Next Steps

- [ ] Add authentication/API keys
- [ ] Implement rate limiting
- [ ] Add request caching
- [ ] Monitor connection health
- [ ] Add error analytics
