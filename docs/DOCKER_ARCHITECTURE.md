# Docker Architecture & Networking Diagrams

## Service Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Host Machine                              │
│                  (localhost / 127.0.0.1)                     │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │       Docker Network: omnisearch-network (bridge)       │ │
│  │                                                          │ │
│  │  ┌──────────────┐              ┌──────────────┐         │ │
│  │  │   FastAPI    │              │  Embedding   │         │ │
│  │  │  Container   │              │  Container   │         │ │
│  │  │   (8000)     │              │   (8001)     │         │ │
│  │  │              │◄────────────►│              │         │ │
│  │  │ • Search API │  HTTP/REST   │ • CLIP Model │         │ │
│  │  │ • Routes     │              │ • Embeddings │         │ │
│  │  └──────┬───────┘              └──────┬───────┘         │ │
│  │         │                             │                  │ │
│  │         └────────────┬────────────────┘                  │ │
│  │                      │ Docker Network Communication      │ │
│  │         ┌────────────┴──────────────┐                    │ │
│  │         │                          │                    │ │
│  │  ┌──────▼──────────┐        ┌──────▼───────────┐        │ │
│  │  │   Weaviate      │        │    MongoDB       │        │ │
│  │  │   Container     │        │    Container     │        │ │
│  │  │   (8080)        │        │    (27017)       │        │ │
│  │  │                 │        │                  │        │ │
│  │  │ • Vector DB     │        │ • Document DB    │        │ │
│  │  │ • HNSW Index    │        │ • Collections    │        │ │
│  │  │ • REST API      │        │ • Indexes        │        │ │
│  │  └─────────────────┘        └──────────────────┘        │ │
│  │                                                          │ │
│  │  Volumes:                                               │ │
│  │  • weaviate-data     (persistence)                      │ │
│  │  • mongodb-data      (persistence)                      │ │
│  │  • embedding-models  (model cache)                      │ │
│  │  • logs             (application logs)                  │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
│  Port Mappings (Host ← Docker):                              │
│  • 8000 ← 8000 (FastAPI)                                    │
│  • 8001 ← 8001 (Embedding)                                  │
│  • 8080 ← 8080 (Weaviate)                                   │
│  • 27017 ← 27017 (MongoDB)                                  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
User / Client
    │
    │ HTTP POST /search/text
    │ {"query": "blue shoes"}
    ▼
┌────────────────┐
│   FastAPI      │
│   Service      │
│ (port 8000)    │
└────┬───────────┘
     │
     ├─────────────────────────┬─────────────────────────┐
     │                         │                         │
     ▼                         ▼                         ▼
  Query Text              Call Embedding           Fetch Results
     │                     Service                 from Cache
     │                        │                         │
     ▼                        ▼                         ▼
Query processed         ┌──────────────┐          Check MongoDB
by FastAPI             │  Embedding    │          for cached
                        │  Service      │          results
     │                  │ (port 8001)   │             │
     │                  └────┬─────────┘             │
     │                       │                       │
     │              Process with CLIP               │
     │              model (768-dim vector)          │
     │                       │                       │
     │◄──────────────────────┘                       │
     │                                               │
     ├────────────────────────┬──────────────────────┘
     │                        │
     ▼                        ▼
Vector embedding      Cache & DB updates
(768-dim)                    │
     │                       │
     │   ┌──────────────────┘
     │   │
     ▼   ▼
┌────────────────────┐
│   Weaviate         │
│ (Vector Database)  │
│   (port 8080)      │
└──────┬─────────────┘
       │
       │ Find similar vectors (HNSW search)
       │
       ▼
   Top K results (10)
       │
       ├─────────────────────┐
       │                     │
       ▼                     ▼
Store in MongoDB        Return to FastAPI
  • click_events      ┌──────────────────┐
  • impressions       │  Return Results   │
  • experiments       │  with metadata    │
       │              └────────┬─────────┘
       │                       │
       │                       ▼
       │                   HTTP Response
       │                   {"results": [...]}
       │                       │
       └──────────────────────►│
                               ▼
                           User / Client
```

---

## Network Topology

```
Docker Network: omnisearch-network (bridge)

┌─────────────────────────────────────────────────────┐
│                    bridge network                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Gateway: 172.21.0.1                               │
│                                                     │
│  fastapi       ──► 172.21.0.2:8000                 │
│  embedding     ──► 172.21.0.3:8001                 │
│  weaviate      ──► 172.21.0.4:8080                 │
│  mongo         ──► 172.21.0.5:27017                │
│  mongo-express ──► 172.21.0.6:8081 (dev)          │
│  weaviate-console ──► 172.21.0.7:3000 (dev)       │
│                                                     │
│  All services can reach each other via service     │
│  names (DNS resolution within network)             │
│                                                     │
│  Example:                                           │
│    fastapi → http://weaviate:8080                  │
│    fastapi → mongodb://admin:pw@mongo:27017        │
│                                                     │
└─────────────────────────────────────────────────────┘

Host Port Mappings:
│
├─► localhost:8000   ◄────► FastAPI:8000
├─► localhost:8001   ◄────► Embedding:8001
├─► localhost:8080   ◄────► Weaviate:8080
├─► localhost:27017  ◄────► MongoDB:27017
├─► localhost:8081   ◄────► MongoDB Express:8081 (dev)
└─► localhost:3000   ◄────► Weaviate Console:3000 (dev)
```

---

## Container Lifecycle

```
docker-compose up -d

1. Pull Images
   ├─ fastapi (build from Dockerfile)
   ├─ embedding (build from Dockerfile.embedding)
   ├─ weaviate:1.24.1
   └─ mongo:7.0

2. Create Network
   └─ omnisearch-network (bridge)

3. Start Containers (in order)
   
   a) MongoDB (first)
      ├─ Create volume: mongodb-data
      ├─ Mount: scripts/mongo-init.js
      ├─ Run initialization script
      ├─ Wait for health check (mongosh ping)
      └─ Ready on 27017

   b) Weaviate (parallel)
      ├─ Create volume: weaviate-data
      ├─ Wait for health check (ready endpoint)
      └─ Ready on 8080

   c) Embedding Service (parallel)
      ├─ Create volume: embedding-models
      ├─ Download CLIP model on first run
      ├─ Wait for health check
      └─ Ready on 8001

   d) FastAPI (last)
      ├─ Depends on: mongo, weaviate, embedding (all healthy)
      ├─ Mount: ./ (code volume)
      ├─ Start uvicorn server
      └─ Ready on 8000

4. Optional: Start Dev Services
   ├─ MongoDB Express (port 8081)
   └─ Weaviate Console (port 3000)

5. Health Checks Running
   └─ All services monitored continuously
```

---

## Dependency Graph

```
docker-compose up -d

    │
    ├─► Weaviate ◄────────┐
    │   • Wait for ready    │
    │   • Health check      │
    │     (port 8080)       │
    │                       │
    ├─► MongoDB ◄────────┐ │
    │   • Initialize DB   │ │
    │   • Run mongo-init  │ │
    │   • Health check    │ │
    │     (port 27017)    │ │
    │                     │ │
    ├─► Embedding ◄───────┤
    │   • Download models │ │
    │   • Health check    │ │
    │     (port 8001)     │ │
    │                     │ │
    └─► FastAPI ◄────────┘
        • Depends on all 3 (healthy)
        • Start uvicorn
        • Health check (port 8000)
        • Ready for requests
```

---

## Volume Mounting

```
Host Machine (c:\omnisearch)
    │
    ├─ ./                    ◄── Project root
    │   │
    │   ├─ main.py           ◄── FastAPI app
    │   ├─ services/         ◄── Service code
    │   ├─ requirements.txt   ◄── Dependencies
    │   └─ scripts/
    │       └─ mongo-init.js ◄── MongoDB init
    │
    └─ Docker Named Volumes (managed by Docker)
        │
        ├─ weaviate-data
        │   └─ /var/lib/weaviate (in container)
        │       ├─ indices/
        │       ├─ schemas/
        │       └─ backups/
        │
        ├─ mongodb-data
        │   └─ /data/db (in container)
        │       └─ omnisearch.* (database files)
        │
        ├─ mongodb-config
        │   └─ /data/configdb (in container)
        │       └─ Replica set config
        │
        ├─ embedding-models
        │   └─ /app/models (in container)
        │       └─ Model cache (CLIP, transformers)
        │
        └─ logs
            └─ /app/logs (in container)
                └─ Application logs

Volume Types:
├─ Bind Mount (/)     → Real-time code changes
├─ Named Volumes (*)  → Persistent data storage
└─ tmpfs               → Temporary storage (RAM)
```

---

## Docker-Compose File Structure

```
docker-compose.yml

version: '3.8'

services:
  ├─ fastapi (depends_on: weaviate, mongo, embedding)
  ├─ embedding
  ├─ weaviate
  ├─ mongo
  ├─ mongo-express (profile: dev)
  └─ weaviate-console (profile: dev)

networks:
  └─ omnisearch-network (bridge)

volumes:
  ├─ weaviate-data (local)
  ├─ mongodb-data (local)
  ├─ mongodb-config (local)
  ├─ embedding-models (local)
  └─ logs (local)
```

---

## Service Interactions

```
FastAPI (Core Service)
    │
    ├──► Weaviate
    │    • GET /v1/.well-known/ready (health check)
    │    • GET /v1/schema (get collections)
    │    • POST /v1/objects (create)
    │    • POST /v1/graphql (search)
    │
    ├──► MongoDB
    │    • click_events.insertOne() (log interactions)
    │    • impressions.insertOne() (log impressions)
    │    • experiments.find() (get experiments)
    │
    └──► Embedding Service
         • POST /embed (get embeddings)
         • GET /health (health check)
         • POST /batch-embed (batch processing)
```

---

## Health Check Chain

```
docker-compose ps

FastAPI (health)
    │
    ├─► depends_on Weaviate (healthy)
    │       │
    │       └─► GET /v1/.well-known/ready
    │           ✓ Returns 200 OK
    │
    ├─► depends_on MongoDB (healthy)
    │       │
    │       └─► mongosh --eval "db.adminCommand('ping')"
    │           ✓ Returns {"ok": 1}
    │
    └─► depends_on Embedding (healthy)
            │
            └─► GET /health
                ✓ Returns {"status": "healthy"}

FastAPI can start only when all dependencies are healthy
```

---

## Configuration Hierarchy

```
Environment Configuration Sources (priority order):

1. docker-compose.yml environment section (highest priority)
   └─ override: $WEAVIATE_URL=http://weaviate:8080

2. .env file (if present)
   └─ WEAVIATE_URL=http://weaviate:8080

3. .env.docker template (default values)
   └─ WEAVIATE_URL=http://weaviate:8080

4. Dockerfile default (lowest priority)
   └─ ENV WEAVIATE_URL=http://localhost:8080

Applied to:
├─ fastapi: Services URLs, logging, ports
├─ embedding: Model cache, device type
├─ weaviate: Query limits, modules, persistence
└─ mongo: Credentials, database name, parameters
```

---

## Scaling Architecture (Conceptual)

```
Production Scaling (not in default docker-compose.yml)

┌──────────────────────────────────────────────┐
│          Load Balancer (nginx/traefik)       │
└────────────┬─────────────────────────────────┘
             │
    ┌────────┼────────┬─────────────┐
    │        │        │             │
    ▼        ▼        ▼             ▼
┌────────┐┌────────┐┌────────┐   ┌────────┐
│FastAPI││FastAPI ││FastAPI │...│FastAPI │
│  #1   ││  #2   ││  #3   │   │  #N   │
└────────┘└────────┘└────────┘   └────────┘
    │        │        │             │
    └────────┼────────┴─────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
  Weaviate        MongoDB (Replica Set)
  Cluster         Primary + Secondaries

Volumes:
├─ Shared weaviate-data
└─ Replicated mongodb-data
```

---

## Summary

- **4 main containers**: FastAPI, Embedding, Weaviate, MongoDB
- **1 bridge network**: Services communicate via hostnames
- **5 named volumes**: Persistent data storage
- **2+ optional services**: Admin UIs (dev profile)
- **Health checks**: Automatic monitoring and restart
- **Dependency management**: Services start in correct order
- **Port mapping**: External access via localhost
