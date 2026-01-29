# Docker & Docker Compose Guide for OmniSearch

## Quick Start

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│           OmniSearch Docker Architecture            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐      ┌──────────────┐            │
│  │   FastAPI    │      │   Embedding  │            │
│  │   (8000)     │      │   (8001)     │            │
│  └──────────────┘      └──────────────┘            │
│         │                      │                    │
│         └──────────┬───────────┘                    │
│                    │                                │
│        ┌───────────┴──────────────┐                │
│        │                          │                │
│  ┌─────────────┐         ┌─────────────────┐      │
│  │  Weaviate   │         │    MongoDB      │      │
│  │  (8080)     │         │    (27017)      │      │
│  └─────────────┘         └─────────────────┘      │
│                                                     │
│  Network: omnisearch-network (bridge)             │
└─────────────────────────────────────────────────────┘
```

---

## Services Overview

### FastAPI Service (Port 8000)

**Image:** Custom (built from Dockerfile)

**Purpose:** Main search API

**Environment Variables:**
```
WEAVIATE_URL=http://weaviate:8080
MONGODB_URL=mongodb://mongo:27017
MONGODB_DB=omnisearch
EMBEDDING_SERVICE_URL=http://embedding:8001
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO
```

**Volumes:**
- `./:/app` - Code mount for development
- `logs:/app/logs` - Application logs

**Health Check:** `GET /health` endpoint

**Dependencies:**
- Weaviate (must be healthy)
- MongoDB (must be healthy)
- Embedding service (must be healthy)

**Startup Command:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

### Embedding Service (Port 8001)

**Image:** Custom (built from Dockerfile.embedding)

**Purpose:** CLIP embedding generation

**Environment Variables:**
```
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO
TRANSFORMERS_CACHE=/app/models
CLIP_CACHE=/app/models
```

**Volumes:**
- `./:/app` - Code mount
- `embedding-models:/app/models` - Model cache (persisted)
- `logs:/app/logs` - Logs

**Resource Limits:**
- CPU: 2-4 cores
- Memory: 2-4 GB

**Health Check:** `GET /health` endpoint

**Startup Command:**
```bash
python services/embedding_service.py
```

---

### Weaviate Vector Database (Port 8080)

**Image:** `semitechnologies/weaviate:1.24.1`

**Purpose:** Vector similarity search

**Ports:**
- `8080` - REST API
- `50051` - gRPC

**Environment Variables:**
```
QUERY_DEFAULTS_LIMIT=20
DEFAULT_VECTORIZER_MODULE=none
PERSISTENCE_DATA_PATH=/var/lib/weaviate
ENABLE_MODULES=text2vec-huggingface,ref2vec-centroid
AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true
BACKUP_FILESYSTEM_PATH=/var/lib/weaviate/backups
LOG_LEVEL=info
```

**Volumes:**
- `weaviate-data:/var/lib/weaviate` - Persistent data

**Health Check:** `GET /v1/.well-known/ready`

---

### MongoDB (Port 27017)

**Image:** `mongo:7.0`

**Purpose:** Document database for analytics and metadata

**Credentials:**
```
Username: admin
Password: password
```

**Environment Variables:**
```
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_INITDB_ROOT_PASSWORD=password
MONGO_INITDB_DATABASE=omnisearch
```

**Volumes:**
- `mongodb-data:/data/db` - Database data
- `mongodb-config:/data/configdb` - Configuration
- `./scripts/mongo-init.js:/docker-entrypoint-initdb.d/init.js` - Init script

**Collections Created:**
- `click_events` - User interactions
- `impressions` - Search impressions
- `experiments` - A/B test experiments

**Indexes:**
- TTL index (90 days) on click_events and impressions
- Compound indexes on user_id + timestamp
- Unique index on experiment name

**Health Check:** `mongosh ping` command

**Replication:** Single node replica set enabled

---

### MongoDB Express (Port 8081) - Development Only

**Image:** `mongo-express:latest`

**Purpose:** Web UI for MongoDB management

**Credentials:**
```
Username: admin
Password: admin
```

**Profile:** `dev` (enable with `--profile dev`)

**Access:** http://localhost:8081

---

### Weaviate Console (Port 3000) - Development Only

**Image:** `semitechnologies/weaviate-console:latest`

**Purpose:** Web UI for Weaviate management

**Profile:** `dev` (enable with `--profile dev`)

**Access:** http://localhost:3000

---

## Docker Compose Profiles

### Production Profile (Default)
```bash
docker-compose up -d
# Includes:
# - FastAPI
# - Embedding service
# - Weaviate
# - MongoDB
```

### Development Profile
```bash
docker-compose --profile dev up -d
# Also includes:
# - MongoDB Express (http://localhost:8081)
# - Weaviate Console (http://localhost:3000)
```

---

## Common Commands

### Start Services

```bash
# Start in background
docker-compose up -d

# Start with specific services
docker-compose up -d fastapi mongo weaviate

# Start with dev tools
docker-compose --profile dev up -d

# Start and view logs
docker-compose up
```

### View Status

```bash
# List running containers
docker-compose ps

# View logs for all services
docker-compose logs

# View logs for specific service
docker-compose logs fastapi

# Follow logs in real-time
docker-compose logs -f

# View logs with timestamps
docker-compose logs --timestamps
```

### Stop Services

```bash
# Stop without removing
docker-compose stop

# Stop specific service
docker-compose stop fastapi

# Stop and remove containers
docker-compose down

# Stop and remove everything including volumes
docker-compose down -v

# Stop and remove images too
docker-compose down -v --rmi all
```

### Rebuild Services

```bash
# Rebuild FastAPI image
docker-compose build fastapi

# Rebuild all images
docker-compose build

# Rebuild without cache
docker-compose build --no-cache

# Build and start
docker-compose up -d --build
```

### Database Access

```bash
# Connect to MongoDB
docker-compose exec mongo mongosh -u admin -p password

# Access MongoDB shell for omnisearch database
docker-compose exec mongo mongosh -u admin -p password --authenticationDatabase admin omnisearch

# Execute command
docker-compose exec mongo mongosh --eval "db.click_events.count()"

# Import data
docker-compose exec -T mongo mongoimport --uri "mongodb://admin:password@localhost:27017/omnisearch" --collection events < events.json
```

### Weaviate Access

```bash
# Weaviate REST API
curl http://localhost:8080/v1/.well-known/ready

# List schemas
curl http://localhost:8080/v1/schema

# Query health
curl http://localhost:8080/v1/nodes
```

### Execute Commands in Containers

```bash
# Run Python in FastAPI container
docker-compose exec fastapi python -c "import requests; print(requests.__version__)"

# Run tests
docker-compose exec fastapi pytest tests/

# Install new package
docker-compose exec fastapi pip install new-package

# Run database migration
docker-compose exec fastapi python scripts/migrate.py
```

---

## Logs and Debugging

### View All Logs

```bash
# Last 100 lines
docker-compose logs --tail=100

# Last 100 lines with timestamps
docker-compose logs --tail=100 --timestamps

# Follow logs in real-time
docker-compose logs -f

# Specific service
docker-compose logs -f fastapi
```

### Check Service Health

```bash
# Get detailed info about all services
docker-compose ps

# Check specific container
docker-compose exec fastapi curl http://localhost:8000/health

# Check Weaviate
docker-compose exec weaviate curl http://localhost:8080/v1/.well-known/ready

# Check MongoDB
docker-compose exec mongo mongosh --eval "db.adminCommand('ping')"
```

### Troubleshooting

```bash
# View service events
docker-compose events

# Inspect container
docker-compose exec fastapi sh

# Check network
docker-compose exec fastapi ping weaviate

# View network details
docker network inspect omnisearch_omnisearch-network

# Check volume status
docker volume ls
docker volume inspect omnisearch_mongodb-data
```

---

## Development Workflow

### Setup Development Environment

```bash
# 1. Clone repository
git clone <repo>
cd omnisearch

# 2. Create .env file (optional)
cat > .env << EOF
WEAVIATE_URL=http://weaviate:8080
MONGODB_URL=mongodb://admin:password@mongo:27017
EOF

# 3. Start services with dev profile
docker-compose --profile dev up -d

# 4. Verify services are running
docker-compose ps

# 5. Check logs
docker-compose logs -f fastapi
```

### Modify Code and Test

```bash
# Edit code locally (volume mounted)
# Changes auto-reload in FastAPI

# Run tests
docker-compose exec fastapi pytest

# Run specific test
docker-compose exec fastapi pytest tests/test_search.py::test_search_text

# Run with coverage
docker-compose exec fastapi pytest --cov=services tests/
```

### Access Admin UIs

```
# FastAPI Docs: http://localhost:8000/docs
# FastAPI ReDoc: http://localhost:8000/redoc
# MongoDB Express: http://localhost:8081 (dev profile)
# Weaviate Console: http://localhost:3000 (dev profile)
```

---

## Performance Tuning

### Increase Resource Allocation

Edit `docker-compose.yml`:

```yaml
services:
  embedding:
    deploy:
      resources:
        limits:
          cpus: '8'        # Increase from 4
          memory: 8G       # Increase from 4G
        reservations:
          cpus: '4'        # Increase from 2
          memory: 4G       # Increase from 2G
```

### Optimize Weaviate

```yaml
services:
  weaviate:
    environment:
      - QUERY_DEFAULTS_LIMIT=100    # Increase results
      - POOLING_QUERY_BUFFER_COUNT=100
```

### Optimize MongoDB

```yaml
services:
  mongo:
    command: >
      --auth
      --wiredTigerCacheSizeGB=4
      --replSet rs0
      --bind_ip_all
```

---

## Backup and Restore

### Backup MongoDB

```bash
# Backup all databases
docker-compose exec -T mongo mongodump --uri "mongodb://admin:password@localhost:27017" --out /backup

# Extract backup
docker cp omnisearch-mongodb:/backup ./backup_$(date +%Y%m%d)
```

### Restore MongoDB

```bash
# Copy backup to container
docker cp ./backup omnisearch-mongodb:/backup

# Restore
docker-compose exec -T mongo mongorestore --uri "mongodb://admin:password@localhost:27017" /backup
```

### Backup Weaviate

```bash
# Weaviate backup location
docker volume inspect omnisearch_weaviate-data

# Backup volume
docker run --rm -v omnisearch_weaviate-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/weaviate-backup-$(date +%Y%m%d).tar.gz -C /data .
```

---

## Production Deployment

### Security Considerations

```yaml
# Change MongoDB password
MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}

# Use environment variables for secrets
# Create .env file (DO NOT commit)
```

### Use External Services

```yaml
# Instead of Docker services, use managed services
environment:
  WEAVIATE_URL: https://weaviate.example.com
  MONGODB_URL: mongodb+srv://user:pass@cluster.mongodb.net
```

### Resource Limits

```yaml
services:
  fastapi:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
  embedding:
    deploy:
      resources:
        limits:
          cpus: '8'
          memory: 8G
```

---

## File Structure

```
omnisearch/
├── Dockerfile                 # FastAPI image
├── Dockerfile.embedding       # Embedding service image
├── docker-compose.yml         # Orchestration
├── requirements.txt           # Python dependencies
├── main.py                    # FastAPI app
├── services/
│   └── embedding_service.py   # Embedding server
├── scripts/
│   └── mongo-init.js          # MongoDB initialization
└── logs/                      # Application logs (created)
```

---

## Network Communication

### Service Discovery

Services can communicate using service names as hostnames:

```python
# In FastAPI container
requests.get("http://weaviate:8080/v1/.well-known/ready")
requests.get("http://embedding:8001/health")
# MongoDB connection
client = MongoClient("mongodb://mongo:27017")
```

### Port Mapping

```
Service          Container Port    Host Port
FastAPI          8000              8000
Embedding        8001              8001
Weaviate REST    8080              8080
Weaviate gRPC    50051             50051
MongoDB          27017             27017
Mongo Express    8081              8081
Weaviate Console 3000              3000
```

---

## Volumes and Persistence

### Volume Types

```yaml
volumes:
  weaviate-data:     # Named volume (persistent)
  mongodb-data:      # Named volume (persistent)
  mongodb-config:    # Named volume (persistent)
  embedding-models:  # Named volume (persistent)
  logs:              # Named volume (persistent)
```

### View Volume Details

```bash
# List all volumes
docker volume ls | grep omnisearch

# Inspect specific volume
docker volume inspect omnisearch_mongodb-data

# Mount volume locally
docker run -v omnisearch_mongodb-data:/data alpine ls /data
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Docker Build & Push

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker images
        run: docker-compose build
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Run tests
        run: docker-compose exec -T fastapi pytest
      
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker tag omnisearch-fastapi:latest $DOCKER_USERNAME/omnisearch-fastapi:latest
          docker push $DOCKER_USERNAME/omnisearch-fastapi:latest
```

---

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Weaviate Docker](https://weaviate.io/developers/weaviate/installation/docker-compose)
- [MongoDB Docker](https://hub.docker.com/_/mongo)
- [FastAPI Docker](https://fastapi.tiangolo.com/deployment/docker/)
