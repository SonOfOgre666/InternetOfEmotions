# Deployment Guide

## Prerequisites

### System Requirements
- **OS**: Linux, macOS, or Windows with WSL2
- **CPU**: 4+ cores (8+ recommended for ML processing)
- **RAM**: 8GB minimum (16GB recommended)
- **Disk**: 20GB free space
- **Docker**: 20.10+ with Docker Compose v2

### Required Accounts
- **Reddit API**: Get credentials from https://www.reddit.com/prefs/apps
  - Client ID
  - Client Secret

## Environment Setup

### 1. Clone Repository
```bash
git clone https://github.com/YourUsername/InternetOfEmotions.git
cd InternetOfEmotions
```

### 2. Create Environment File
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```bash
# Reddit API
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=InternetOfEmotions/2.0

# Database
DB_PASSWORD=your_secure_password_here

# RabbitMQ
RABBITMQ_USER=ioe_user
RABBITMQ_PASSWORD=your_secure_password_here

# Elasticsearch
ELASTIC_PASSWORD=your_elastic_password_here

# Optional: Custom Configuration
MAX_POST_AGE_DAYS=28
LOG_LEVEL=INFO
```

### 3. Verify Docker
```bash
docker --version  # Should be 20.10+
docker compose version  # Should be v2.0+
```

## Development Deployment

### Quick Start (All Services)
```bash
# Start all services
docker compose -f docker-compose.microservices.yml up -d

# Check status
docker compose -f docker-compose.microservices.yml ps

# View logs
docker compose -f docker-compose.microservices.yml logs -f

# Verify tests are passing
./run_tests.sh
```

### Selective Service Startup
```bash
# Infrastructure only
docker compose up -d postgres rabbitmq redis elasticsearch

# Backend services
docker compose up -d post_fetcher url_extractor ml_analyzer country_aggregation

# Frontend
docker compose up -d api_gateway frontend
```

### Access Services
- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **RabbitMQ Management**: http://localhost:15672 (user: ioe_user)
- **Elasticsearch**: http://localhost:9200

## Production Deployment

### 1. Security Hardening

#### Update Passwords
```bash
# Generate strong passwords
openssl rand -base64 32  # For DB_PASSWORD
openssl rand -base64 32  # For RABBITMQ_PASSWORD
openssl rand -base64 32  # For ELASTIC_PASSWORD
```

#### Configure Firewall
```bash
# Allow only necessary ports
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 22/tcp    # SSH

# Block direct access to backend services
ufw deny 5001:5008/tcp
ufw deny 5432/tcp
ufw deny 6379/tcp
```

#### Use Secrets Management
```bash
# Docker Swarm secrets
echo "my_db_password" | docker secret create db_password -
echo "my_rabbitmq_password" | docker secret create rabbitmq_password -
```

### 2. Use Production Compose File
```bash
# Create production override
cp docker-compose.microservices.yml docker-compose.prod.yml
```

Edit `docker-compose.prod.yml`:
```yaml
services:
  api_gateway:
    environment:
      - ALLOWED_ORIGINS=https://yourdomain.com
    restart: always
  
  ml_analyzer:
    deploy:
      resources:
        limits:
          memory: 16G
        reservations:
          memory: 8G
      replicas: 3
```

### 3. Set Up Reverse Proxy (Nginx)

#### Install Nginx
```bash
sudo apt install nginx certbot python3-certbot-nginx
```

#### Configure
```nginx
# /etc/nginx/sites-available/internetofemotions
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # CORS headers
        add_header Access-Control-Allow-Origin https://yourdomain.com;
    }
}
```

#### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/internetofemotions /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### SSL Certificate
```bash
sudo certbot --nginx -d yourdomain.com
```

### 4. Deploy
```bash
docker compose -f docker-compose.prod.yml up -d
```

## Cloud Deployment

### AWS (EC2 + RDS + ElastiCache)

#### 1. Launch EC2 Instance
- **Instance Type**: t3.xlarge or larger
- **AMI**: Ubuntu 22.04 LTS
- **Storage**: 50GB EBS
- **Security Group**: Allow ports 80, 443, 22

#### 2. Set Up RDS (PostgreSQL)
```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier ioe-postgres \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 15.3 \
  --master-username ioe_user \
  --master-user-password YourSecurePassword \
  --allocated-storage 100

# Get endpoint
aws rds describe-db-instances --db-instance-identifier ioe-postgres
```

Update `.env`:
```bash
DATABASE_URL=postgresql://ioe_user:password@your-rds-endpoint:5432/internet_of_emotions
```

#### 3. Set Up ElastiCache (Redis)
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id ioe-redis \
  --cache-node-type cache.t3.medium \
  --engine redis \
  --num-cache-nodes 1
```

#### 4. Deploy Application
SSH into EC2:
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Clone and deploy
git clone https://github.com/YourUsername/InternetOfEmotions.git
cd InternetOfEmotions
docker compose -f docker-compose.prod.yml up -d
```

### Google Cloud (GKE)

#### 1. Create Kubernetes Cluster
```bash
gcloud container clusters create ioe-cluster \
  --num-nodes=3 \
  --machine-type=n1-standard-4 \
  --zone=us-central1-a
```

#### 2. Deploy with Kubernetes
```bash
# Create namespace
kubectl create namespace internet-of-emotions

# Deploy services
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/rabbitmq.yaml
kubectl apply -f k8s/services.yaml
kubectl apply -f k8s/ingress.yaml
```

### Azure (AKS + Cosmos DB)

#### 1. Create Resource Group
```bash
az group create --name ioe-rg --location eastus
```

#### 2. Create AKS Cluster
```bash
az aks create \
  --resource-group ioe-rg \
  --name ioe-cluster \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --enable-addons monitoring
```

## Monitoring Setup

### Prometheus + Grafana

#### 1. Add to docker-compose.yml
```yaml
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

#### 2. Configure Prometheus
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'api_gateway'
    static_configs:
      - targets: ['api_gateway:8000']
  
  - job_name: 'services'
    static_configs:
      - targets: 
        - 'post_fetcher:5001'
        - 'ml_analyzer:5003'
```

### Application Performance Monitoring (APM)

#### New Relic
```bash
# Add to docker-compose.yml
environment:
  - NEW_RELIC_LICENSE_KEY=your_key
  - NEW_RELIC_APP_NAME=InternetOfEmotions
```

#### DataDog
```bash
docker run -d --name datadog-agent \
  -e DD_API_KEY=your_key \
  -e DD_SITE=datadoghq.com \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  datadog/agent:latest
```

## Backup and Recovery

### Database Backup
```bash
# Automated daily backups
docker exec ioe_postgres pg_dump -U ioe_user internet_of_emotions > backup_$(date +%Y%m%d).sql

# Upload to S3
aws s3 cp backup_$(date +%Y%m%d).sql s3://your-bucket/backups/
```

### Volume Backup
```bash
# Backup volumes
docker run --rm \
  -v internetofemotions_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_data.tar.gz /data
```

### Recovery
```bash
# Restore database
docker exec -i ioe_postgres psql -U ioe_user internet_of_emotions < backup.sql

# Restore volume
docker run --rm \
  -v internetofemotions_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/postgres_data.tar.gz -C /
```

## Scaling

### Horizontal Scaling
```bash
# Scale specific service
docker compose up -d --scale ml_analyzer=5

# Kubernetes
kubectl scale deployment ml-analyzer --replicas=5
```

### Auto-Scaling (Kubernetes)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ml-analyzer-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ml-analyzer
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Health Checks

### Liveness Check Script
```bash
#!/bin/bash
# healthcheck.sh

services=("api_gateway" "post_fetcher" "ml_analyzer" "country_aggregation")

for service in "${services[@]}"; do
  response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
  if [ $response -eq 200 ]; then
    echo "✓ $service is healthy"
  else
    echo "✗ $service is unhealthy (HTTP $response)"
    exit 1
  fi
done
```

## Troubleshooting

### Common Issues

**Services won't start**
```bash
# Check logs
docker compose logs <service_name>

# Verify environment
docker compose config

# Restart
docker compose restart <service_name>
```

**High memory usage**
```bash
# Check resource usage
docker stats

# Limit ML Analyzer memory
docker compose up -d --scale ml_analyzer=2
```

**Database connection errors**
```bash
# Check database status
docker compose ps postgres

# Test connection
docker exec -it ioe_postgres psql -U ioe_user -d internet_of_emotions -c "SELECT 1"
```

## Maintenance

### Update Services
```bash
# Pull latest images
docker compose pull

# Restart with zero downtime (Kubernetes)
kubectl rollout restart deployment/ml-analyzer
```

### Clean Up
```bash
# Remove unused images
docker image prune -a

# Remove old volumes
docker volume prune
```
