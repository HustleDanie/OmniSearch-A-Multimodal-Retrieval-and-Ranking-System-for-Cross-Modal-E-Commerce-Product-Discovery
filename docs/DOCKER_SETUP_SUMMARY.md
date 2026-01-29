# Docker Setup Summary

## What's Included

✅ **Dockerfile** - FastAPI service containerization
✅ **Dockerfile.embedding** - Embedding service containerization  
✅ **docker-compose.yml** - Full stack orchestration
✅ **mongo-init.js** - MongoDB schema and indexes
✅ **Comprehensive Documentation** - Guides and references

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│        OmniSearch Docker Stack               │
├─────────────────────────────────────────────┤
│                                             │
│  FastAPI (8000)  ←→  Embedding (8001)      │
│         │                    │              │
│         └────────┬───────────┘              │
│                  │                          │
│       ┌──────────┴──────────┐              │
│       │                     │              │
│   Weaviate (8080)    MongoDB (27017)       │
│   (Vector DB)        (Document DB)        │
│                                             │
│   Network: omnisearch-network              │
└─────────────────────────────────────────────┘
```

---

## Quick Start Commands

```bash
# 1. Start all services
docker-compose up -d

# 2. Verify status
docker-compose ps

# 3. Check API health
curl http://localhost:8000/health

# 4. Access FastAPI docs
open http://localhost:8000/docs

# 5. View logs
docker-compose logs -f

# 6. Stop services
docker-compose down
```

---

## Files Created

| File | Purpose |
|------|---------|
| `Dockerfile` | FastAPI container image |
| `Dockerfile.embedding` | Embedding service container |
| `docker-compose.yml` | Service orchestration & configuration |
| `scripts/mongo-init.js` | MongoDB database setup |
| `.dockerignore` | Build optimization |
| `.env.docker` | Environment variables template |
| `docs/DOCKER_GUIDE.md` | Comprehensive Docker reference |
| `docs/DOCKER_QUICKREF.md` | Quick command reference |
| `docs/DOCKER_DEPLOYMENT.md` | Deployment & operations guide |

---

## Service Details

### FastAPI (Port 8000)

**Image:** Custom (built from Dockerfile)
**Status:** http://localhost:8000/health
**Docs:** http://localhost:8000/docs

```yaml
Environment:
  - WEAVIATE_URL: http://weaviate:8080
  - MONGODB_URL: mongodb://mongo:27017
  - EMBEDDING_SERVICE_URL: http://embedding:8001
```

### Embedding Service (Port 8001)

**Image:** Custom (built from Dockerfile.embedding)
**Status:** http://localhost:8001/health
**Resources:** 2-4 CPU, 2-4GB RAM

```yaml
Environment:
  - TRANSFORMERS_CACHE: /app/models
  - CLIP_CACHE: /app/models
```

### Weaviate Vector DB (Port 8080)

**Image:** semitechnologies/weaviate:1.24.1
**Status:** http://localhost:8080/v1/.well-known/ready
**Storage:** weaviate-data volume

```yaml
REST API: http://localhost:8080
gRPC: localhost:50051
```

### MongoDB (Port 27017)

**Image:** mongo:7.0
**Credentials:** admin / password
**Database:** omnisearch

```yaml
Collections:
  - click_events (with TTL: 90 days)
  - impressions (with TTL: 90 days)
  - experiments

Indexes:
  - user_id + timestamp
  - query + timestamp
  - variant + timestamp
```

### MongoDB Express (Port 8081, Dev Only)

**URL:** http://localhost:8081
**Username:** admin
**Password:** admin

```bash
# Enable with
docker-compose --profile dev up -d
```

### Weaviate Console (Port 3000, Dev Only)

**URL:** http://localhost:3000

```bash
# Enable with
docker-compose --profile dev up -d
```

---

## Essential Commands

```bash
# Start/Stop
docker-compose up -d              # Start background
docker-compose down               # Stop services
docker-compose restart            # Restart services
docker-compose down -v            # Stop & remove volumes

# Viewing
docker-compose ps                 # List services
docker-compose logs               # View all logs
docker-compose logs -f fastapi    # Follow FastAPI logs
docker-compose logs --tail=50     # Last 50 lines

# Database Access
docker-compose exec mongo mongosh                    # MongoDB shell
docker-compose exec mongo mongosh --eval "db.adminCommand('ping')"  # Test
docker-compose exec mongo mongosh --eval "db.click_events.count()"  # Count

# Build/Rebuild
docker-compose build              # Build images
docker-compose build --no-cache   # Build from scratch
docker-compose up -d --build      # Build & start

# Cleanup
docker-compose down -v --rmi all  # Remove everything
docker system prune -a            # Clean unused resources
```

---

## Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| FastAPI API | http://localhost:8000 | Search endpoints |
| Swagger UI | http://localhost:8000/docs | Interactive API docs |
| ReDoc | http://localhost:8000/redoc | API documentation |
| Weaviate REST | http://localhost:8080 | Vector DB API |
| MongoDB | localhost:27017 | Database connection |
| MongoDB Express | http://localhost:8081 | DB UI (dev) |
| Weaviate Console | http://localhost:3000 | DB UI (dev) |

---

## Database Setup

### MongoDB

Automatically initialized with:
- Database: `omnisearch`
- Username: `admin`
- Password: `password`
- Collections: click_events, impressions, experiments
- Indexes: Created on user_id, query, variant, timestamp
- TTL: 90-day expiration on event data

### Weaviate

Configured with:
- Vector index: HNSW (configurable)
- Modules: text2vec-huggingface, ref2vec-centroid
- Authentication: Anonymous access enabled
- Backup path: `/var/lib/weaviate/backups`

---

## Development Workflow

```bash
# 1. Start with dev profile
docker-compose --profile dev up -d

# 2. Edit code (auto-reloaded)
vim services/search.py

# 3. Check logs
docker-compose logs -f fastapi

# 4. Access admin UIs
# FastAPI Docs: http://localhost:8000/docs
# MongoDB UI: http://localhost:8081
# Weaviate UI: http://localhost:3000

# 5. Stop when done
docker-compose down
```

---

## Production Deployment

### Key Steps

1. **Update Credentials**
   - Change MongoDB password in docker-compose.yml
   - Update environment variables in .env

2. **Configure Resources**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '4'
         memory: 4G
   ```

3. **Enable Security**
   - Use HTTPS for external APIs
   - Enable authentication
   - Restrict CORS origins

4. **Setup Monitoring**
   - Configure log aggregation
   - Setup health check monitoring
   - Enable alerting

5. **Backup Strategy**
   - Automated daily MongoDB backups
   - Weaviate volume snapshots
   - Test restore procedures

---

## Volumes

| Volume | Purpose | Content |
|--------|---------|---------|
| weaviate-data | Weaviate storage | Vector indexes, schemas |
| mongodb-data | MongoDB storage | Database documents |
| mongodb-config | MongoDB config | Replica set config |
| embedding-models | Model cache | Transformer models |
| logs | Application logs | Log files |

```bash
# View volumes
docker volume ls | grep omnisearch

# Inspect volume
docker volume inspect omnisearch_mongodb-data

# Backup volume
docker run --rm -v omnisearch_mongodb-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/backup.tar.gz -C /data .
```

---

## Health Checks

```bash
# FastAPI
curl http://localhost:8000/health

# Weaviate
curl http://localhost:8080/v1/.well-known/ready

# MongoDB
docker-compose exec mongo mongosh --eval "db.adminCommand('ping')"

# All services
docker-compose ps
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port already in use | Change port in docker-compose.yml |
| Services won't start | Check logs: `docker-compose logs` |
| Memory issues | Increase Docker memory limit |
| MongoDB won't initialize | Check mongo-init.js permissions |
| Slow embeddings | Add GPU or increase CPU allocation |
| High disk usage | Clean volumes: `docker-compose down -v` |

---

## Performance Tips

1. **FastAPI Performance**
   - Use multiple workers
   - Enable caching
   - Connection pooling

2. **MongoDB Performance**
   - Create appropriate indexes (done automatically)
   - Monitor query performance
   - Use connection pooling

3. **Embedding Performance**
   - Use GPU if available
   - Cache models locally
   - Batch requests

4. **Weaviate Performance**
   - Tune index parameters (HNSW ef, maxConnections)
   - Monitor query times
   - Use compression

---

## Next Steps

1. **Start Services**
   ```bash
   docker-compose up -d
   ```

2. **Verify Deployment**
   ```bash
   docker-compose ps
   curl http://localhost:8000/health
   ```

3. **Load Sample Data**
   ```bash
   python scripts/load_sample_data.py
   ```

4. **Run Tests**
   ```bash
   docker-compose exec fastapi pytest
   ```

5. **Monitor Logs**
   ```bash
   docker-compose logs -f
   ```

---

## Documentation

Full documentation available in:
- `docs/DOCKER_GUIDE.md` - Complete reference
- `docs/DOCKER_QUICKREF.md` - Quick commands
- `docs/DOCKER_DEPLOYMENT.md` - Operations guide

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Verify services: `docker-compose ps`
3. Test connectivity: `docker-compose exec fastapi ping weaviate`
4. Consult documentation: `docs/DOCKER_GUIDE.md`

---

## Key Takeaways

✅ Complete containerized stack ready to run
✅ Services communicate on private network
✅ Automatic database initialization
✅ Development and production profiles
✅ Comprehensive health checks
✅ Volume persistence
✅ Full documentation included

**Get started:** `docker-compose up -d`
