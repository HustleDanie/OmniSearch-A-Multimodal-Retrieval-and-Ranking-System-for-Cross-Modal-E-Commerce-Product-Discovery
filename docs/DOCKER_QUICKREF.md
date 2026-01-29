# Docker Quick Reference

## One-Liner Start

```bash
docker-compose up -d
```

---

## Services & Ports

| Service | Port | URL |
|---------|------|-----|
| FastAPI | 8000 | http://localhost:8000 |
| Embedding | 8001 | http://localhost:8001 |
| Weaviate | 8080 | http://localhost:8080 |
| MongoDB | 27017 | mongodb://localhost:27017 |
| MongoDB Express (dev) | 8081 | http://localhost:8081 |
| Weaviate Console (dev) | 3000 | http://localhost:3000 |

---

## Essential Commands

```bash
# Start all services
docker-compose up -d

# View status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild images
docker-compose build

# Development with admin UIs
docker-compose --profile dev up -d
```

---

## API Access

```bash
# FastAPI
curl http://localhost:8000/health
curl http://localhost:8000/docs                    # Swagger UI
curl http://localhost:8000/redoc                   # ReDoc

# Weaviate
curl http://localhost:8080/v1/.well-known/ready

# Embedding Service
curl http://localhost:8001/health
```

---

## Database Access

```bash
# MongoDB shell
docker-compose exec mongo mongosh -u admin -p password

# MongoDB in omnisearch database
docker-compose exec mongo mongosh -u admin -p password omnisearch

# Count click events
docker-compose exec mongo mongosh --eval "db.click_events.count()"

# MongoDB Express UI (dev)
# http://localhost:8081
# Username: admin, Password: admin
```

---

## Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs fastapi
docker-compose logs weaviate
docker-compose logs mongo

# Follow real-time
docker-compose logs -f

# Last 50 lines
docker-compose logs --tail=50
```

---

## Development Workflow

```bash
# 1. Start with dev profile (includes admin UIs)
docker-compose --profile dev up -d

# 2. Edit code (auto-reloaded in FastAPI)
# Your local changes appear in container

# 3. View logs
docker-compose logs -f fastapi

# 4. Access APIs
# FastAPI Docs: http://localhost:8000/docs
# MongoDB UI: http://localhost:8081
# Weaviate UI: http://localhost:3000

# 5. Stop when done
docker-compose down
```

---

## Database Credentials

```
MongoDB:
  URL: mongodb://admin:password@localhost:27017
  Username: admin
  Password: password
  Database: omnisearch

MongoDB Express (dev):
  URL: http://localhost:8081
  Username: admin
  Password: admin
```

---

## Troubleshooting

```bash
# Check if services are running
docker-compose ps

# View service errors
docker-compose logs fastapi

# Stop and restart a service
docker-compose restart fastapi

# Check network connectivity
docker-compose exec fastapi ping weaviate

# Rebuild and restart
docker-compose build --no-cache && docker-compose up -d
```

---

## Clean Up

```bash
# Stop services (keep volumes)
docker-compose down

# Stop services and remove volumes
docker-compose down -v

# Stop services and remove images
docker-compose down -v --rmi all

# Remove unused Docker resources
docker system prune -a
```

---

## Performance Monitoring

```bash
# Container stats
docker stats

# Specific container
docker stats omnisearch-fastapi

# Check resource usage
docker-compose ps
```

---

## Backup/Restore

```bash
# Backup MongoDB
docker-compose exec -T mongo mongodump --uri "mongodb://admin:password@localhost:27017" --out /backup

# Backup Weaviate volume
docker cp omnisearch-weaviate:/var/lib/weaviate ./weaviate-backup

# Check volumes
docker volume ls
```

---

## Environment Variables

Set in `docker-compose.yml`:

```yaml
environment:
  - WEAVIATE_URL=http://weaviate:8080
  - MONGODB_URL=mongodb://mongo:27017
  - EMBEDDING_SERVICE_URL=http://embedding:8001
```

Or in `.env` file:
```
WEAVIATE_URL=http://weaviate:8080
MONGODB_URL=mongodb://mongo:27017
EMBEDDING_SERVICE_URL=http://embedding:8001
```

---

## Full Documentation

See [DOCKER_GUIDE.md](../docs/DOCKER_GUIDE.md) for:
- Complete service descriptions
- Configuration details
- Advanced deployment options
- CI/CD integration
- Production security
- Troubleshooting guide
