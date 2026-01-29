# Docker Compose Deployment Guide

## Quick Deployment

### 1. Start All Services (Production)

```bash
# Start in background
docker-compose up -d

# Verify all services running
docker-compose ps

# Expected output:
# NAME                   STATUS              PORTS
# omnisearch-fastapi     Up (healthy)        0.0.0.0:8000->8000/tcp
# omnisearch-embedding   Up (healthy)        0.0.0.0:8001->8001/tcp
# omnisearch-weaviate    Up (healthy)        0.0.0.0:8080->8080/tcp
# omnisearch-mongodb     Up (healthy)        0.0.0.0:27017->27017/tcp
```

### 2. Start with Development Tools

```bash
# Includes admin UIs for MongoDB and Weaviate
docker-compose --profile dev up -d

# Additional services:
# - MongoDB Express (http://localhost:8081)
# - Weaviate Console (http://localhost:3000)
```

### 3. Verify Services are Healthy

```bash
# Check all endpoints
echo "FastAPI:" && curl -s http://localhost:8000/health
echo "Embedding:" && curl -s http://localhost:8001/health
echo "Weaviate:" && curl -s http://localhost:8080/v1/.well-known/ready
echo "MongoDB:" && docker-compose exec mongo mongosh --eval "db.adminCommand('ping')"
```

---

## File Overview

| File | Purpose |
|------|---------|
| `Dockerfile` | FastAPI service image |
| `Dockerfile.embedding` | Embedding service image |
| `docker-compose.yml` | Service orchestration |
| `.dockerignore` | Build context optimization |
| `.env.docker` | Environment variables template |
| `scripts/mongo-init.js` | MongoDB initialization |

---

## Service Architecture

```
docker-compose.yml
├── fastapi (port 8000)
│   ├── depends_on: weaviate, mongo, embedding
│   ├── volumes: ./, logs/
│   └── networks: omnisearch-network
├── embedding (port 8001)
│   ├── volumes: ./, embedding-models/, logs/
│   ├── resources: 2-4 CPU, 2-4GB RAM
│   └── networks: omnisearch-network
├── weaviate (port 8080, 50051)
│   ├── image: semitechnologies/weaviate:1.24.1
│   ├── volumes: weaviate-data/
│   └── networks: omnisearch-network
├── mongo (port 27017)
│   ├── image: mongo:7.0
│   ├── volumes: mongodb-data/, mongodb-config/
│   ├── init: scripts/mongo-init.js
│   └── networks: omnisearch-network
├── mongo-express (port 8081, dev only)
│   ├── profile: dev
│   └── networks: omnisearch-network
└── weaviate-console (port 3000, dev only)
    ├── profile: dev
    └── networks: omnisearch-network
```

---

## Common Deployment Scenarios

### Scenario 1: Local Development

```bash
# Start with dev profile
docker-compose --profile dev up -d

# All services + admin UIs
# Access:
#   FastAPI: http://localhost:8000/docs
#   MongoDB Express: http://localhost:8081
#   Weaviate Console: http://localhost:3000
```

### Scenario 2: Production-Like Environment

```bash
# Start only core services
docker-compose up -d

# Verify:
docker-compose ps
docker-compose logs -f fastapi
```

### Scenario 3: Testing Environment

```bash
# Start with minimal resources
docker-compose up -d

# Run tests
docker-compose exec fastapi pytest tests/

# View test results
docker-compose logs fastapi
```

### Scenario 4: Rebuild After Code Changes

```bash
# Rebuild all images
docker-compose build

# Start with new images
docker-compose up -d

# Or combine
docker-compose up -d --build
```

---

## Monitoring and Maintenance

### Monitor Services

```bash
# Real-time stats
docker stats

# Service logs
docker-compose logs -f

# Specific service
docker-compose logs -f fastapi

# With tail limit
docker-compose logs --tail=50 -f fastapi
```

### Database Maintenance

```bash
# MongoDB shell
docker-compose exec mongo mongosh -u admin -p password

# List databases
docker-compose exec mongo mongosh --eval "db.adminCommand('listDatabases')"

# Collections in omnisearch
docker-compose exec mongo mongosh --eval "db.getCollectionNames()"

# Count records
docker-compose exec mongo mongosh --eval "db.click_events.count()"

# Create index
docker-compose exec mongo mongosh --eval "db.click_events.createIndex({user_id: 1, timestamp: -1})"
```

### Weaviate Management

```bash
# Check schema
curl http://localhost:8080/v1/schema

# Get statistics
curl http://localhost:8080/v1/nodes

# List all objects
curl http://localhost:8080/v1/objects?limit=10
```

---

## Scaling and Performance

### Increase Resource Allocation

Edit `docker-compose.yml`:

```yaml
services:
  embedding:
    deploy:
      resources:
        limits:
          cpus: '8'        # Increase
          memory: 8G       # Increase
```

Then restart:
```bash
docker-compose up -d
```

### Connection Pooling

MongoDB connection string:
```
mongodb://admin:password@mongo:27017?maxPoolSize=50
```

### Caching Strategy

```yaml
services:
  fastapi:
    environment:
      - REDIS_URL=redis://redis:6379  # Optional redis
      - CACHE_TTL=3600
```

---

## Backup and Recovery

### Backup MongoDB

```bash
# Create backup directory
mkdir backups

# Backup entire database
docker-compose exec -T mongo mongodump \
  --uri "mongodb://admin:password@localhost:27017" \
  --out /backup

# Copy backup to host
docker cp omnisearch-mongodb:/backup ./backups/mongodb-$(date +%Y%m%d-%H%M%S)
```

### Restore MongoDB

```bash
# Copy backup to container
docker cp ./backups/mongodb-backup omnisearch-mongodb:/backup

# Restore
docker-compose exec -T mongo mongorestore \
  --uri "mongodb://admin:password@localhost:27017" \
  /backup
```

### Backup Weaviate Data

```bash
# Get volume path
docker volume inspect omnisearch_weaviate-data

# Backup volume
docker run --rm \
  -v omnisearch_weaviate-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/weaviate-$(date +%Y%m%d).tar.gz -C /data .
```

### Restore Weaviate Data

```bash
# Extract backup
tar xzf backups/weaviate-*.tar.gz -C /tmp/weaviate-restore

# Copy to volume
docker run --rm \
  -v omnisearch_weaviate-data:/data \
  -v /tmp/weaviate-restore:/backup \
  alpine cp -r /backup/* /data/
```

---

## Troubleshooting

### Services Not Starting

```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs fastapi

# Check if ports are available
netstat -ano | findstr :8000
netstat -ano | findstr :27017
```

### MongoDB Connection Failed

```bash
# Verify MongoDB is running
docker-compose ps mongo

# Check MongoDB logs
docker-compose logs mongo

# Test connection
docker-compose exec mongo mongosh -u admin -p password --eval "db.adminCommand('ping')"
```

### Weaviate Connection Failed

```bash
# Check Weaviate logs
docker-compose logs weaviate

# Test connection
curl http://localhost:8080/v1/.well-known/ready

# Check network
docker-compose exec fastapi ping weaviate
```

### High Memory Usage

```bash
# Check resource usage
docker stats

# Reduce cache sizes
docker-compose down -v

# Restart with limited resources
docker-compose up -d
```

### Service Port Already in Use

```bash
# Find process using port
netstat -ano | findstr :8000

# Change port in docker-compose.yml
# Or kill existing process
```

---

## Networking

### Service Communication

Services can communicate using service names:

```python
# From FastAPI container
import requests
response = requests.get("http://weaviate:8080/v1/.well-known/ready")

# MongoDB connection
from pymongo import MongoClient
client = MongoClient("mongodb://admin:password@mongo:27017")

# Embedding service
response = requests.post("http://embedding:8001/embed", json={...})
```

### External Network Access

```yaml
# Services are accessible on host machine via localhost
FastAPI:     http://localhost:8000
Embedding:   http://localhost:8001
Weaviate:    http://localhost:8080
MongoDB:     localhost:27017
```

---

## Environment Configuration

### Using .env File

```bash
# Create .env from template
cp .env.docker .env

# Edit with your settings
nano .env

# Services will load from .env
docker-compose up -d
```

### Environment Variables

Set in `docker-compose.yml` or `.env`:

```yaml
environment:
  - WEAVIATE_URL=http://weaviate:8080
  - MONGODB_URL=mongodb://admin:password@mongo:27017
  - EMBEDDING_SERVICE_URL=http://embedding:8001
  - LOG_LEVEL=INFO
```

---

## Production Checklist

- [ ] Use strong MongoDB password (change from default)
- [ ] Enable authentication in all services
- [ ] Use external managed services (cloud) if possible
- [ ] Set resource limits for all services
- [ ] Configure log rotation
- [ ] Setup automated backups
- [ ] Monitor disk space for volumes
- [ ] Use health checks in production
- [ ] Setup alerting for failed services
- [ ] Test disaster recovery procedures
- [ ] Document deployment process
- [ ] Secure .env file (don't commit to git)

---

## Performance Tuning

### FastAPI Tuning

```yaml
services:
  fastapi:
    environment:
      - WORKERS=4
      - THREADS_PER_WORKER=2
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### MongoDB Tuning

```yaml
services:
  mongo:
    command: >
      --auth
      --wiredTigerCacheSizeGB=4
      --replSet rs0
      --bind_ip_all
      --maxConnections=1000
```

### Weaviate Tuning

```yaml
services:
  weaviate:
    environment:
      - POOLING_QUERY_BUFFER_COUNT=100
      - QUERY_DEFAULTS_LIMIT=100
      - KEEP_RATE_LIMITER_ENABLED=true
```

---

## Cleanup Commands

```bash
# Stop services (keep volumes)
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Remove everything including images
docker-compose down -v --rmi all

# Remove unused Docker resources
docker system prune -a

# Clean up specific volumes
docker volume rm omnisearch_mongodb-data
```

---

## CI/CD Integration

### GitHub Actions

```yaml
- name: Start Docker services
  run: docker-compose up -d

- name: Wait for services
  run: sleep 10

- name: Run tests
  run: docker-compose exec -T fastapi pytest

- name: Cleanup
  if: always()
  run: docker-compose down -v
```

### GitLab CI

```yaml
docker:compose:test:
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - docker-compose up -d
    - sleep 10
  script:
    - docker-compose exec -T fastapi pytest
  after_script:
    - docker-compose down -v
```

---

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Spec](https://github.com/compose-spec/compose-spec)
- [Weaviate Docker Setup](https://weaviate.io/developers/weaviate/installation/docker-compose)
- [MongoDB Docker Hub](https://hub.docker.com/_/mongo)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/docker/)
