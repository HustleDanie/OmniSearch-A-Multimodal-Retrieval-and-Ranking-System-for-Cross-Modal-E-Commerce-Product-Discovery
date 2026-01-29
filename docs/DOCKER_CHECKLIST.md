# Docker Setup Checklist

## Pre-Deployment Setup

- [ ] Docker installed and running
- [ ] Docker Compose installed (v1.29+)
- [ ] At least 8GB RAM available
- [ ] 20GB+ disk space for volumes
- [ ] Required ports free (8000, 8001, 8080, 27017)
- [ ] Clone/access OmniSearch repository

## Files Verification

- [ ] `Dockerfile` exists
- [ ] `Dockerfile.embedding` exists
- [ ] `docker-compose.yml` exists
- [ ] `scripts/mongo-init.js` exists
- [ ] `.dockerignore` exists
- [ ] `requirements.txt` exists with all dependencies

## Pre-Start Configuration

- [ ] Review `docker-compose.yml`
- [ ] Verify port mappings
- [ ] Check environment variables
- [ ] Confirm MongoDB credentials (admin/password)
- [ ] Plan volume locations
- [ ] Decide on dev vs production profile

## Starting Services

- [ ] `docker-compose build` (build images)
- [ ] `docker-compose up -d` (start services)
- [ ] `docker-compose ps` (verify all running)
- [ ] Wait 30 seconds for services to fully initialize
- [ ] Check logs: `docker-compose logs`

## Service Health Verification

**FastAPI (8000)**
- [ ] API responsive: `curl http://localhost:8000/health`
- [ ] Docs available: `http://localhost:8000/docs`
- [ ] Status shows "healthy"

**Embedding Service (8001)**
- [ ] Service responsive: `curl http://localhost:8001/health`
- [ ] Models downloaded
- [ ] Status shows "healthy"

**Weaviate (8080)**
- [ ] Ready endpoint: `curl http://localhost:8080/v1/.well-known/ready`
- [ ] Schema accessible: `curl http://localhost:8080/v1/schema`
- [ ] Status shows healthy

**MongoDB (27017)**
- [ ] Connection successful: `docker-compose exec mongo mongosh -u admin -p password`
- [ ] Database created: `omnisearch`
- [ ] Collections exist: click_events, impressions, experiments
- [ ] Indexes created
- [ ] TTL configured (90 days)

## Network Verification

- [ ] Container communication: `docker-compose exec fastapi ping weaviate`
- [ ] MongoDB from FastAPI: `docker-compose exec fastapi ping mongo`
- [ ] Embedding from FastAPI: `docker-compose exec fastapi ping embedding`
- [ ] All containers on same network: `docker network inspect omnisearch_omnisearch-network`

## Volume Verification

- [ ] List volumes: `docker volume ls | grep omnisearch`
- [ ] `weaviate-data` exists and accessible
- [ ] `mongodb-data` exists and accessible
- [ ] `embedding-models` created
- [ ] `logs` volume created
- [ ] Volumes show correct size (grows over time)

## Development Setup (if using --profile dev)

- [ ] MongoDB Express running on 8081
  - [ ] Access `http://localhost:8081`
  - [ ] Login: admin/admin
  - [ ] Browse omnisearch database

- [ ] Weaviate Console running on 3000
  - [ ] Access `http://localhost:3000`
  - [ ] Can view schemas and objects

## API Testing

```bash
# Test FastAPI search endpoint
curl -X POST http://localhost:8000/search/text \
  -H "Content-Type: application/json" \
  -d '{"query": "blue shoes", "top_k": 10}'

# Expected: Results with vectors or empty (if no data yet)
```

- [ ] Search endpoint responds
- [ ] Returns valid JSON
- [ ] Error handling works

## Database Testing

```bash
# Test MongoDB connection
docker-compose exec mongo mongosh --eval "db.click_events.count()"

# Expected: Returns 0 (or count if data exists)
```

- [ ] Can connect to MongoDB
- [ ] Can query collections
- [ ] Indexes working

## Logs Review

- [ ] Check FastAPI logs: `docker-compose logs fastapi --tail=20`
- [ ] Check Embedding logs: `docker-compose logs embedding --tail=20`
- [ ] Check Weaviate logs: `docker-compose logs weaviate --tail=20`
- [ ] Check MongoDB logs: `docker-compose logs mongo --tail=20`
- [ ] No errors in logs
- [ ] Services initialized successfully

## Performance Baseline

- [ ] Test query latency: `time curl http://localhost:8000/health`
- [ ] Monitor resource usage: `docker stats`
  - [ ] CPU usage reasonable (< 50%)
  - [ ] Memory usage acceptable
  - [ ] No memory leaks

## Backup Configuration

- [ ] Plan backup strategy
- [ ] Test MongoDB backup: `docker-compose exec -T mongo mongodump`
- [ ] Test volume backup
- [ ] Document restore procedure
- [ ] Test restore on clean system

## Security Checklist

- [ ] MongoDB credentials changed (if production)
- [ ] .env file not committed to git
- [ ] `.dockerignore` properly configured
- [ ] No secrets in Dockerfiles
- [ ] Authentication enabled where needed
- [ ] Network isolation verified

## Production Deployment Prep

- [ ] Resource limits configured
- [ ] Restart policies set
- [ ] Health checks tuned
- [ ] Logging aggregation planned
- [ ] Monitoring setup complete
- [ ] Alerting configured
- [ ] Runbook created
- [ ] Team trained on operations

## Documentation Review

- [ ] Read `docs/DOCKER_GUIDE.md`
- [ ] Understand service architecture
- [ ] Reviewed common commands
- [ ] Bookmarked troubleshooting guide
- [ ] Saved quick reference

## Cleanup (if not needed)

```bash
# Stop and remove everything
docker-compose down -v --rmi all

# Or just stop
docker-compose down
```

- [ ] Services stopped
- [ ] Volumes removed (if desired)
- [ ] Images cleaned up
- [ ] Network removed

---

## Daily Operations Checklist

### Morning

- [ ] Check services running: `docker-compose ps`
- [ ] Review logs for errors: `docker-compose logs --since 24h`
- [ ] Monitor resource usage: `docker stats`
- [ ] Verify backups completed

### During Day

- [ ] Monitor log aggregation
- [ ] Check alert dashboard
- [ ] Review performance metrics
- [ ] Respond to issues

### End of Day

- [ ] Archive logs if needed
- [ ] Run backup: `./scripts/backup.sh`
- [ ] Review incident log
- [ ] Plan for next day

---

## Weekly Maintenance

- [ ] Clean up old logs: `docker-compose logs --tail=0 > archive.log`
- [ ] Verify backups: Test restore on test system
- [ ] Review resource usage trends
- [ ] Update documentation if needed
- [ ] Security audit logs
- [ ] Performance analysis

---

## Monthly Maintenance

- [ ] Full capacity planning review
- [ ] Update dependencies
- [ ] Security patches
- [ ] Disaster recovery drill
- [ ] Document lessons learned
- [ ] Plan for scaling if needed

---

## Troubleshooting Checklist

If services fail to start:

- [ ] Check Docker daemon: `docker ps`
- [ ] Check logs: `docker-compose logs`
- [ ] Verify ports available: `netstat -ano | findstr :8000`
- [ ] Check disk space: `docker volume ls`
- [ ] Review .env configuration
- [ ] Rebuild images: `docker-compose build --no-cache`
- [ ] Clear cache: `docker system prune`

If database issues:

- [ ] Check MongoDB: `docker-compose exec mongo mongosh`
- [ ] Verify data files: `docker volume inspect omnisearch_mongodb-data`
- [ ] Check indexes: `docker-compose exec mongo mongosh --eval "db.click_events.getIndexes()"`
- [ ] Review MongoDB logs
- [ ] Test backup restore

If performance issues:

- [ ] Check resource usage: `docker stats`
- [ ] Verify network: `docker-compose exec fastapi ping weaviate`
- [ ] Monitor query latency
- [ ] Check for memory leaks
- [ ] Review Weaviate index settings
- [ ] Optimize database queries

---

## Success Criteria

✅ All services running and healthy
✅ All endpoints responding correctly
✅ Database operations working
✅ Logs clean and informative
✅ Health checks passing
✅ Performance within acceptable range
✅ Backup and restore tested
✅ Team trained and comfortable with operations
✅ Documentation up to date
✅ Ready for production traffic

---

## Sign-Off

- [ ] Deployment lead: _________________ Date: _______
- [ ] DevOps engineer: _________________ Date: _______
- [ ] QA approved: _________________ Date: _______

**Status:** ☐ Ready for Production ☐ Needs Work

---

## Quick Reference Links

- **Docker Guide:** `docs/DOCKER_GUIDE.md`
- **Quick Reference:** `docs/DOCKER_QUICKREF.md`
- **Architecture:** `docs/DOCKER_ARCHITECTURE.md`
- **Deployment:** `docs/DOCKER_DEPLOYMENT.md`
- **Setup Summary:** `docs/DOCKER_SETUP_SUMMARY.md`

---

Use this checklist before every deployment!
