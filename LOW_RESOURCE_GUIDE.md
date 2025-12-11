# 🎯 Running on Limited Resources (7.4GB RAM)

## Your System Specs
- **RAM**: 7.4GB (3.8GB available)
- **CPU**: 8 cores ✅
- **Disk**: 15GB available

## Resource Allocation Strategy

### Total Memory Budget: ~6.5GB

| Component | Memory Limit | Purpose |
|-----------|-------------|---------|
| **PostgreSQL** | 512MB | Database |
| **RabbitMQ** | 512MB | Message queue |
| **Redis** | 256MB | Cache (with LRU eviction) |
| **Elasticsearch** | 768MB | Search (reduced from 1GB) |
| **ML Analyzer** | 2GB | Main ML service (4 models) |
| **Collective Analyzer** | 512MB | BART model |
| **Cross-Country Detector** | 512MB | BERT NER |
| **Other 9 services** | ~1.9GB | (9 × ~200MB each) |
| **System Reserve** | ~1GB | OS + Docker overhead |

## How to Use

### Start with Optimized Configuration

```bash
# Use the optimized docker-compose file
docker compose -f docker-compose.optimized.yml up -d

# Monitor resource usage
docker stats

# View logs
docker compose -f docker-compose.optimized.yml logs -f
```

### Key Optimizations Implemented

#### 1. **Memory Limits**
Every service has strict memory limits to prevent OOM (Out of Memory) crashes:
```yaml
deploy:
  resources:
    limits:
      memory: 256M  # Maximum allowed
    reservations:
      memory: 128M  # Start with this
```

#### 2. **CPU Constraints**
CPU usage is limited to prevent system freeze:
- Heavy services (ML): 2-3 cores max
- Medium services: 1 core max
- Light services: 0.5 cores max

#### 3. **ML Model Optimization**
- **Lazy Loading**: Models load only when needed
- **Auto-Unload**: Models unload after 5 minutes of inactivity
- **Shared Cache**: All ML services share model cache (saves ~500MB)
- **Thread Limiting**: `OMP_NUM_THREADS=2` prevents CPU overuse

#### 4. **Database Optimization**
PostgreSQL configured for low memory:
```bash
POSTGRES_SHARED_BUFFERS: "256MB"  # Reduced from default 1GB
POSTGRES_WORK_MEM: "16MB"         # Reduced from default 64MB
```

#### 5. **Redis Optimization**
```bash
--maxmemory 256mb           # Hard limit
--maxmemory-policy allkeys-lru  # Auto-evict old keys
```

#### 6. **Elasticsearch Optimization**
```bash
ES_JAVA_OPTS: "-Xms512m -Xmx512m"  # Reduced from 1GB
```

## Performance Impact

### ✅ What Works Normally
- All API endpoints
- Real-time emotion analysis
- Database operations
- Message queue processing
- Caching and search

### ⚠️ Slightly Slower (But Still Works)
- **Initial ML model loading**: 30-60 seconds (one-time)
- **Large batch processing**: Processes in smaller chunks
- **Search indexing**: May take a bit longer

### 💡 Smart Behaviors
- **ML models auto-unload** when idle → frees 1-1.5GB RAM
- **Redis evicts old cache** → never runs out of memory
- **Services start small** → grow only if needed

## Monitoring

### Check Memory Usage
```bash
# Overall system
free -h

# Per container
docker stats --no-stream

# Specific service
docker stats ioe_ml_analyzer --no-stream
```

### Check if Services are Healthy
```bash
# All services status
docker compose -f docker-compose.optimized.yml ps

# Test API
curl http://localhost:8000/health
curl http://localhost:5003/api/health  # ML Analyzer
```

### Warning Signs
If you see:
- `OOMKilled` in `docker ps -a`: A service ran out of memory
- Very high swap usage: System is struggling
- Services constantly restarting: Memory pressure

**Solution**: Free up RAM by closing browser tabs, other apps

## Disk Space Management

With only **15GB available**, manage space carefully:

### Check Docker Disk Usage
```bash
docker system df
```

### Clean Up (Run weekly)
```bash
# Remove unused containers
docker container prune -f

# Remove unused images
docker image prune -a -f

# Remove unused volumes
docker volume prune -f

# Clean everything (CAUTION: removes all data)
docker system prune -a --volumes -f
```

### Keep ML Models Cached
The `ml_models` volume (~2-3GB) caches downloaded models:
- **Don't delete** unless absolutely necessary
- Saves bandwidth and time on restart

## Troubleshooting

### Problem: "Cannot allocate memory"
```bash
# Check what's using memory
docker stats

# Stop non-critical services temporarily
docker compose -f docker-compose.optimized.yml stop elasticsearch

# Restart when needed
docker compose -f docker-compose.optimized.yml start elasticsearch
```

### Problem: ML Analyzer keeps restarting
```bash
# Check logs
docker logs ioe_ml_analyzer --tail 50

# Likely cause: Memory limit too low
# Increase to 2.5GB if needed (edit docker-compose.optimized.yml)
```

### Problem: System becomes slow
```bash
# Check swap usage
free -h

# If swap is high (>2GB used):
# 1. Close other applications
# 2. Restart Docker
sudo systemctl restart docker
```

## Comparison: Normal vs Optimized

| Metric | Normal Config | Optimized Config |
|--------|---------------|------------------|
| **Total RAM Usage** | ~8-10GB | ~5.5-6.5GB ✅ |
| **Elasticsearch Heap** | 1GB | 512MB ✅ |
| **ML Analyzer Limit** | Unlimited | 2GB ✅ |
| **Redis Limit** | Unlimited | 256MB ✅ |
| **Startup Time** | 2-3 min | 3-4 min (~slower) |
| **All Features** | ✅ | ✅ |

## Tips for Best Performance

1. **Close Heavy Applications**
   - Chrome/Firefox: Close extra tabs
   - VS Code: Close unused windows
   - Other IDEs: Close if not needed

2. **Run Services in Stages**
   ```bash
   # Start infrastructure first
   docker compose -f docker-compose.optimized.yml up -d postgres rabbitmq redis
   
   # Wait 30 seconds, then start services
   docker compose -f docker-compose.optimized.yml up -d
   ```

3. **Monitor Regularly**
   ```bash
   # Set up a monitoring terminal
   watch -n 5 'docker stats --no-stream'
   ```

4. **Use Swap Wisely**
   - Your system has swap enabled (good!)
   - Some services will use swap (expected)
   - If swap > 3GB used → close other apps

5. **Limit Fetch Countries** (Optional)
   - If still too heavy, edit `.env`:
   ```bash
   # Fetch only 50 most active countries instead of 196
   LIMIT_COUNTRIES=50
   ```

## Success Criteria

Your system will run successfully if:
- ✅ All 17 containers start and stay running
- ✅ Health checks pass for all services
- ✅ API responses within 1-2 seconds
- ✅ ML analysis works (even if slower)
- ✅ No OOMKilled containers

**You have everything you need to run the full project!** 🚀
