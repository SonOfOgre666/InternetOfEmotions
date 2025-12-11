# Backend Documentation Index

Welcome to the Internet of Emotions backend documentation. This index will help you navigate the comprehensive documentation.

## Quick Links

### Getting Started
- [README.md](./README.md) - Architecture overview and service descriptions
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Complete deployment guide for dev and production
- [TESTING.md](./TESTING.md) - Testing guide with 440+ test cases

### Development
- [API.md](./API.md) - Complete API documentation with examples
- [ORCHESTRATION.md](./ORCHESTRATION.md) - Service orchestration and debugging

### Reference
- [config.py](./config.py) - Shared configuration constants
- [common_utils.py](./common_utils.py) - Reusable utilities and helpers

## Documentation Structure

```
backend/
├── README.md                # Architecture overview
├── API.md                   # API endpoints documentation
├── DEPLOYMENT.md            # Deployment and scaling guide
├── TESTING.md               # Testing guide (NEW)
├── config.py                # Shared configuration
├── common_utils.py          # Common utilities
└── INDEX.md                 # This file
```

## For Different Roles

### 👨‍💻 **Developer**
Start here:
1. [README.md](./README.md) - Understand the architecture
2. [TESTING.md](./TESTING.md) - Run tests and verify changes
3. [config.py](./config.py) - Review shared configuration
4. [common_utils.py](./common_utils.py) - Learn available utilities
5. [API.md](./API.md) - API endpoints reference

### 🚀 **DevOps Engineer**
Start here:
1. [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment procedures
2. [ORCHESTRATION.md](./ORCHESTRATION.md) - Service management
3. [README.md](./README.md#monitoring) - Monitoring setup

### 🔧 **SRE / Support**
Start here:
1. [ORCHESTRATION.md#troubleshooting](./ORCHESTRATION.md#troubleshooting) - Common issues
2. [DEPLOYMENT.md#health-checks](./DEPLOYMENT.md#health-checks) - Health monitoring
3. [API.md#error-responses](./API.md#error-responses) - Error codes

### 📊 **Product Manager**
Start here:
1. [README.md#overview](./README.md#overview) - System capabilities
2. [API.md](./API.md) - Feature endpoints
3. [README.md#message-flow](./README.md#message-flow) - Data pipeline

## Service Documentation

Each microservice has its own documentation in `/services/<service-name>/`:

- **post_fetcher**: Reddit post fetching service
- **url_extractor**: Article content extraction
- **ml_analyzer**: Emotion analysis with ML models
- **country_aggregation**: Country-level emotion aggregation
- **cache_service**: Redis caching layer
- **search_service**: Elasticsearch full-text search
- **stats_service**: Analytics and metrics
- **db_cleanup**: Database maintenance (30-day cleanup)
- **api_gateway**: Request routing and load balancing
- **scheduler**: Smart country scheduling with priority
- **collective_analyzer**: Advanced collective event detection
- **cross_country_detector**: Multi-country post detection

## Common Tasks

### Start Development Environment
```bash
docker compose -f docker-compose.microservices.yml up -d
```
See: [DEPLOYMENT.md#development-deployment](./DEPLOYMENT.md#development-deployment)

### Deploy to Production
```bash
docker compose -f docker-compose.prod.yml up -d
```
See: [DEPLOYMENT.md#production-deployment](./DEPLOYMENT.md#production-deployment)

### Debug a Service
```bash
docker compose logs -f <service_name>
```
See: [ORCHESTRATION.md#monitoring-and-debugging](./ORCHESTRATION.md#monitoring-and-debugging)

### Scale a Service
```bash
docker compose up -d --scale ml_analyzer=5
```
See: [ORCHESTRATION.md#scaling-strategies](./ORCHESTRATION.md#scaling-strategies)

### Check System Health
```bash
curl http://localhost:8000/health
```
See: [API.md#health-check](./API.md#health-check)

## External Resources

- **Docker Documentation**: https://docs.docker.com
- **RabbitMQ Tutorials**: https://www.rabbitmq.com/tutorials
- **PostgreSQL Manual**: https://www.postgresql.org/docs/
- **Redis Documentation**: https://redis.io/docs/
- **Elasticsearch Guide**: https://www.elastic.co/guide/

## Contributing

When adding new services or features:
1. Update [README.md](./README.md) with architecture changes
2. Document new API endpoints in [API.md](./API.md)
3. Add orchestration details to [ORCHESTRATION.md](./ORCHESTRATION.md)
4. Update this index if adding new documentation files

## Version History

- **v2.0** (Dec 2025) - Microservices architecture
- **v1.0** (Archive) - Monolithic backend (see `/archive/old_monolith/`)

## Support

For questions or issues:
1. Check [ORCHESTRATION.md#troubleshooting](./ORCHESTRATION.md#troubleshooting)
2. Review service logs: `docker compose logs -f`
3. Open an issue on GitHub
