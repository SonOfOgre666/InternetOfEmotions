# Testing the Internet of Emotions Application

## 🚀 Quick Start - Run Everything

### Step 1: Start Backend Services (Automated)

```bash
cd /home/sonofogre/Downloads/InternetOfEmotions-main
./start-backend.sh
```

This automatically starts all 6 microservices:
- ✅ Data Fetcher (Port 5001)
- ✅ Content Extractor (Port 5007)
- ✅ Event Extractor (Port 5004)
- ✅ ML Analyzer (Port 5005)
- ✅ Aggregator (Port 5003)
- ✅ API Gateway (Port 5000)

Logs are saved to: `/logs/`

### Step 2: Start Frontend

```bash
cd /home/sonofogre/Downloads/InternetOfEmotions-main/frontend
npm install  # First time only
npm run dev
```

### Step 3: Access Application

Open browser: **http://localhost:3000**

### Stop All Services

```bash
cd /home/sonofogre/Downloads/InternetOfEmotions-main
./stop-backend.sh
```

---

## 🏗️ System Architecture

### Microservices (6 services)

1. **Data Fetcher** (Port 5001)
   - Fetches Reddit posts for countries
   - Circular rotation through all countries
   - For country-name subreddits (r/Morocco, r/France): fetches newest posts
   - For other subreddits (r/worldnews): searches by country keyword

2. **Content Extractor** (Port 5007)
   - Extracts article content from link posts
   - Enriches posts with full article text

3. **Event Extractor** (Port 5004)
   - Groups similar posts into events using DBSCAN clustering
   - Individual posts also become standalone events
   - Generates concise AI summaries (max 2 sentences, 250 chars)

4. **ML Analyzer** (Port 5005)
   - Emotion analysis using RoBERTa transformer model
   - Processes both posts and events

5. **Aggregator** (Port 5003)
   - Country-level emotion aggregation
   - Computes statistics and top topics

6. **API Gateway** (Port 5000)
   - Central orchestration and routing
   - Background processing pipeline
   - Frontend API endpoints

### Database

- **SQLite** (`backend/microservices/database.db`)
- Tables: `posts`, `events`, `country_emotions`
- Shared across all microservices

### Database

- **SQLite** (`backend/microservices/database.db`)
- Tables: `posts`, `events`, `country_emotions`
- Shared across all microservices

---

## 🧪 Testing Individual Services

### Health Checks

```bash
# Check all services
curl http://localhost:5001/health  # Data Fetcher
curl http://localhost:5007/health  # Content Extractor
curl http://localhost:5004/health  # Event Extractor
curl http://localhost:5005/health  # ML Analyzer
curl http://localhost:5003/health  # Aggregator
curl http://localhost:5000/health  # API Gateway
```

### Test Data Pipeline

```bash
# 1. Fetch posts for specific countries
curl -X POST http://localhost:5001/fetch \
  -H "Content-Type: application/json" \
  -d '{"countries": ["france", "portugal", "morocco"], "limit": 30}'

# 2. Extract content from link posts
curl -X POST http://localhost:5007/process/pending

# 3. Extract events from posts
curl -X POST http://localhost:5004/extract_events \
  -H "Content-Type: application/json" \
  -d '{"countries": ["france", "portugal"]}'

# 4. Analyze emotions
curl -X POST http://localhost:5005/process/pending

# 5. Aggregate country emotions
curl -X POST http://localhost:5003/aggregate/all
```

### Check Database

```bash
cd /home/sonofogre/Downloads/InternetOfEmotions-main/backend/microservices

# Count posts
sqlite3 database.db "SELECT COUNT(*) FROM posts;"

# Count events
sqlite3 database.db "SELECT COUNT(*) FROM events;"

# View countries with data
sqlite3 database.db "SELECT DISTINCT country FROM posts LIMIT 10;"

# View recent events
sqlite3 database.db "SELECT country, title FROM events LIMIT 5;"
```

---

## 🔍 Viewing Logs

All service logs are in `/logs/`:

```bash
cd /home/sonofogre/Downloads/InternetOfEmotions-main/logs

# View specific service log
tail -f data-fetcher.log
tail -f event-extractor.log
tail -f ml-analyzer.log

# Search for errors
grep ERROR *.log

# View last 50 lines of all logs
tail -50 *.log
```

---

## ⚙️ Configuration

### Backend Environment Variables

Create `/backend/microservices/.env`:

```bash
# Reddit API credentials (required)
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_secret_here
REDDIT_USER_AGENT=InternetOfEmotions/1.0

# Optional settings
MAX_POST_AGE_DAYS=28
DATA_FETCH_WORKERS=10
REDDIT_FETCH_LIMIT=200
```

### Frontend Environment Variables

Create `/frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:5000
```

---

## 🐛 Troubleshooting

### Services won't start

```bash
# Check if ports are already in use
lsof -i :5000
lsof -i :5001

# Kill existing processes
pkill -f "python.*microservices"

# Restart
./stop-backend.sh && sleep 2 && ./start-backend.sh
```

### No data appearing

```bash
# Check if database exists and has data
sqlite3 backend/microservices/database.db "SELECT COUNT(*) FROM posts;"

# Trigger manual data fetch
curl -X POST http://localhost:5001/fetch \
  -H "Content-Type: application/json" \
  -d '{"countries": ["france"], "limit": 20}'
```

### Frontend not connecting

```bash
# Verify API Gateway is running
curl http://localhost:5000/health

# Check frontend environment
cat frontend/.env.local

# Rebuild frontend
cd frontend
rm -rf .next
npm run dev
```

---

## 📊 System Requirements

- **Python**: 3.9+
- **Node.js**: 18+
- **RAM**: 4GB minimum (8GB recommended for ML models)
- **Disk**: 2GB for ML models + database
- **OS**: Linux, macOS, or WSL2 on Windows

---

## 🚀 Production Deployment

For production deployment, consider:

1. **Use production WSGI server** (gunicorn, uwsgi)
2. **Set up reverse proxy** (nginx, apache)
3. **Enable HTTPS** with SSL certificates
4. **Configure firewall** rules
5. **Set up monitoring** (logs, health checks)
6. **Use environment variables** for sensitive data
7. **Enable database backups**

---

**Last Updated**: December 16, 2025
pytest backend/microservices/tests/test_data_fetcher.py -v
```

Expected: **29 passed, 1 skipped**

#### 2. Test ML Analyzer
```bash
pytest backend/microservices/tests/test_ml_analyzer.py -v
```

Expected: **4 passed, 1 skipped**

#### 3. Test Aggregator
```bash
pytest backend/microservices/tests/test_aggregator.py -v
```

Expected: **6 passed**

---

## 🔍 Verify Data Flow

### 1. Check API Gateway Health
```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "demo_mode": false,
  "db_posts": 0
}
```

### 2. Check Emotions Endpoint
```bash
curl http://localhost:5000/api/emotions
```

Expected response:
```json
{
  "emotions": [],
  "count": 0,
  "demo_mode": false
}
```

### 3. Check Stats Endpoint
```bash
curl http://localhost:5000/api/stats
```

Expected response:
```json
{
  "total": 0,
  "by_emotion": {},
  "by_country": {},
  "countries_ready": 0
}
```

---

## 📊 Expected Frontend Behavior

Once all services are running:

1. **Connection Status**: Top center should show **"● LIVE"** (green)
2. **Map**: World map loads with default grey colors
3. **Statistics Panel**: Shows "No analytics data available" initially
4. **Country Cards**: Shows "No countries found" initially

### To Generate Data

The system needs to fetch and process posts first:

1. **Automatic Processing**: API Gateway starts background processing automatically
2. **Wait Time**: 5-10 minutes for first cycle:
   - Fetches posts from Reddit
   - Extracts content from articles
   - Groups posts into events
   - Analyzes emotions
   - Aggregates by country
3. **Updates**: Map will update as countries get processed

### Manual Trigger (Optional)
```bash
curl -X POST http://localhost:5000/api/process/start
```

---

## 🎯 Verification Checklist

### Backend Services Running
- [ ] Data Fetcher - Port 5001 - `curl http://localhost:5001/health`
- [ ] Content Extractor - Port 5007 - `curl http://localhost:5007/health`
- [ ] Event Extractor - Port 5004 - `curl http://localhost:5004/health`
- [ ] ML Analyzer - Port 5005 - `curl http://localhost:5005/health`
- [ ] Aggregator - Port 5003 - `curl http://localhost:5003/health`
- [ ] API Gateway - Port 5000 - `curl http://localhost:5000/api/health`

### Frontend
- [ ] Frontend - Port 3000 - Open `http://localhost:3000` in browser
- [ ] Connection shows "● LIVE"
- [ ] Map loads without errors
- [ ] No console errors in browser DevTools

### Data Processing
- [ ] Posts being fetched (check data-fetcher logs)
- [ ] Events being created (check event-extractor logs)
- [ ] Emotions being analyzed (check ml-analyzer logs)
- [ ] Countries being aggregated (check aggregator logs)
- [ ] Frontend updating with new data

---

## 🐛 Troubleshooting

### Issue: "Backend Offline"
**Solution**: Ensure all 6 backend services are running

### Issue: "No data showing"
**Solution**: Wait 5-10 minutes for first processing cycle, or check logs for errors

### Issue: Port already in use
**Solution**: Kill existing process
```bash
lsof -ti:5000 | xargs kill -9  # Replace 5000 with the port
```

### Issue: Frontend can't connect
**Solution**: Check `.env.local` file exists with:
```
NEXT_PUBLIC_API_URL=http://localhost:5000
```

### Issue: Reddit API errors
**Solution**: Check `.env` file has valid Reddit credentials:
```
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT=EmotionsDashboard/1.0
```

---

## 📝 Summary

✅ **Backend**: All unit tests passing  
✅ **Data Flow**: Case sensitivity fixed  
✅ **Frontend**: Configuration complete  
✅ **Integration**: All endpoints properly connected  

**Status**: Ready for production testing! 🚀
