# Internet of Emotions - Project Structure

## Current Microservices Architecture

```
InternetOfEmotions/
├── backend/
│   ├── services/                     # All microservices
│   │   ├── api_gateway/              # Port 8000 - Central API routing
│   │   │   ├── app.py
│   │   │   ├── test_app.py          # Unit tests (30+ test cases)
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   ├── post_fetcher/             # Port 5001 - Reddit data collection
│   │   │   ├── app.py
│   │   │   ├── test_app.py          # Unit tests (50+ test cases)
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   ├── url_extractor/            # Port 5002 - URL content extraction
│   │   │   ├── app.py
│   │   │   ├── test_app.py          # Unit tests (35+ test cases)
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   ├── ml_analyzer/              # Port 5003 - Emotion analysis (4 models)
│   │   │   ├── app.py
│   │   │   ├── test_app.py          # Unit tests (70+ test cases)
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   ├── db_cleanup/               # Port 5004 - Auto-cleanup (30-day retention)
│   │   │   ├── app.py
│   │   │   ├── test_app.py          # Unit tests (25+ test cases)
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   ├── country_aggregation/      # Port 5005 - Country-level aggregation
│   │   │   ├── app.py
│   │   │   ├── country_coordinates.py
│   │   │   ├── test_app.py          # Unit tests (55+ test cases)
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   ├── cache_service/            # Port 5006 - Redis caching
│   │   │   ├── app.py
│   │   │   ├── test_app.py          # Unit tests (20+ test cases)
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   ├── search_service/           # Port 5007 - Full-text search
│   │   │   ├── app.py
│   │   │   ├── test_app.py          # Unit tests (15+ test cases)
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   ├── stats_service/            # Port 5008 - Statistics & SSE streaming
│   │   │   ├── app.py
│   │   │   ├── test_app.py          # Unit tests (20+ test cases)
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   ├── scheduler/                # Port 5010 - Smart country prioritization
│   │   │   ├── app.py
│   │   │   ├── test_app.py          # Unit tests (35+ test cases)
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   ├── collective_analyzer/      # Port 5011 - Collective vs personal classification
│   │   │   ├── app.py
│   │   │   ├── test_app.py          # Unit tests (40+ test cases)
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   ├── cross_country_detector/   # Port 5012 - Cross-country mention detection
│   │   │   ├── app.py
│   │   │   ├── test_app.py          # Unit tests (45+ test cases)
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   └── database/                 # PostgreSQL schema & init scripts
│   │       └── init.sql
│   │
│   ├── README.md                     # Backend architecture overview
│   ├── API.md                        # Complete API documentation
│   ├── DEPLOYMENT.md                 # Deployment guide
│   ├── TESTING.md                    # Testing guide (NEW)
│   └── INDEX.md                      # Documentation index
│
├── frontend/                         # React dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── EmotionMap.js         # Interactive world map
│   │   │   ├── StatsPanel.js         # Statistics charts
│   │   │   └── PostFeed.js           # Live post feed
│   │   ├── App.js
│   │   └── index.js
│   ├── public/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
│
├── archive/
│   └── old_monolith/                 # Archived monolithic version
│       └── backend/                  # Old 1709-line app.py + modules
│
├── docker-compose.microservices.yml  # Main orchestration (17 containers)
├── pyproject.toml                    # Pytest configuration (NEW)
├── run_tests.sh                      # Test runner script (NEW)
├── TEST_IMPLEMENTATION_SUMMARY.md    # Testing overview (NEW)
├── .env.example                      # Environment template
├── .gitignore
└── README.md                         # Main project readme
