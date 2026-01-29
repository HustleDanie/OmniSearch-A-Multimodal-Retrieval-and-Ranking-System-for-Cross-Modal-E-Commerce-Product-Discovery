# Scalability Strategy

## Overview

OmniSearch is designed to scale from 1K to 100M products while maintaining sub-100ms query latency. This document outlines the architecture, bottlenecks, and scaling strategies.

---

## Current Architecture

```
┌─────────────────────────────────────────┐
│         Users / Requests                │
│        (QPS ↔ Capacity)                 │
└────────────────┬────────────────────────┘
                 │
         ┌───────▼────────┐
         │  Load Balancer │
         │  (Nginx/HAProxy)│
         └───────┬────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼────┐  ┌───▼────┐  ┌───▼────┐
│FastAPI │  │FastAPI │  │FastAPI │
│Node 1  │  │Node 2  │  │Node 3  │
└───┬────┘  └───┬────┘  └───┬────┘
    │           │           │
    └───────────┼───────────┘
                │
        ┌───────▼──────────┐
        │  Vector Database │
        │  (Weaviate)      │
        └─────────────────┘
                │
        ┌───────▼──────────┐
        │  Metadata DB     │
        │  (MongoDB)       │
        └─────────────────┘
```

---

## Scaling Dimensions

### 1. Query Throughput (QPS)

**Current bottleneck:** Single API server

```
Single FastAPI server:
├─ CPU: 4 cores
├─ Memory: 8GB
├─ Connections: 100
└─ Throughput: 100-200 QPS

Limiting factor: CPU bound on query execution
```

**Solution: Horizontal scaling**

```
Load balancer distributes to 3 servers:
├─ Server 1: 100-200 QPS
├─ Server 2: 100-200 QPS
├─ Server 3: 100-200 QPS
└─ Total: 300-600 QPS
```

**Scaling formula:**
```
QPS_total = QPS_per_server × num_servers
300 QPS = 100 QPS × 3 servers
```

### 2. Data Volume (Products)

**Current bottleneck:** Vector DB index size

```
1M products:
├─ Index size: 2GB
├─ Memory usage: 4GB (with cache)
├─ Query latency: 100ms
└─ Throughput: 200 QPS

10M products:
├─ Index size: 20GB
├─ Memory usage: 40GB
├─ Query latency: 200ms (degraded)
└─ Throughput: 100 QPS (limited)
```

**Solution: Data sharding**

```
Split 10M products across 2 shards:
├─ Shard 1: 5M products (10GB index, 20GB memory)
├─ Shard 2: 5M products (10GB index, 20GB memory)
├─ Query routed to appropriate shard
├─ Query latency: 100ms (restored)
└─ Throughput: 200 QPS (restored)
```

### 3. Latency (Query Response Time)

**Target: <100ms P99**

```
Latency breakdown for typical query:

Network request:        5ms
├─ Client → LB
├─ LB → Server
└─ Response → Client

Query execution:       80ms
├─ CLIP encoding:      50ms  (embedding model)
├─ Vector search:      20ms  (Weaviate)
├─ Filtering:           5ms  (metadata)
└─ Ranking:             5ms

JSON serialization:     5ms

Total:                 90ms (P99: 120ms)
```

---

## Scaling Timeline

### Phase 1: Current State (0-6 months)

**Capacity:**
- Products: 1M
- QPS: 100-200
- DAU: 10K

**Infrastructure:**
```
├─ 1x API server (4 CPU, 8GB RAM)
├─ 1x Vector DB (16GB RAM, 50GB SSD)
├─ 1x MongoDB (8GB RAM, 100GB SSD)
└─ 1x Load balancer
```

**Cost:** ~$500/month

### Phase 2: Horizontal Growth (6-12 months)

**Capacity:**
- Products: 5M
- QPS: 300-600
- DAU: 50K

**Infrastructure:**
```
├─ 3x API servers (load balanced)
├─ 2x Vector DB (sharded by category)
├─ 1x MongoDB (with read replicas)
└─ 1x Load balancer + monitoring
```

**Changes:**
- Add API nodes: Scale-out
- Add Vector DB nodes: Sharded
- Add MongoDB replicas: Read scaling

**Cost:** ~$2,000/month

### Phase 3: Geographic Distribution (12-24 months)

**Capacity:**
- Products: 50M
- QPS: 1000-2000
- DAU: 200K

**Infrastructure:**
```
US Region:
├─ 5x API servers
├─ 4x Vector DB shards
├─ 1x MongoDB primary
└─ Monitoring & alerting

EU Region (read-only):
├─ 3x API servers
├─ 4x Vector DB replicas
└─ 1x MongoDB replica

Sync: Real-time replication
```

**Cost:** ~$8,000/month

### Phase 4: Global Scale (24+ months)

**Capacity:**
- Products: 100M+
- QPS: 5000+
- DAU: 1M+

**Infrastructure:**
```
Multiple regions (US, EU, APAC):
├─ Regional data centers
├─ Local Vector DB clusters
├─ MongoDB sharded across regions
├─ Global load balancing
└─ Real-time replication
```

**Cost:** $20,000+/month

---

## Scaling Strategies

### Strategy 1: Vertical Scaling (Add Resources)

**Increase single server capacity:**

```yaml
# Before
CPU: 4 cores    → After: 16 cores
Memory: 8GB     → After: 64GB
Disk: 50GB SSD  → After: 500GB SSD

# Result
QPS: 200 → 800 (4x)
Latency: 100ms → 50ms (2x faster)
Cost: $100/month → $400/month
```

**Pros:** Simple, no code changes
**Cons:** Expensive, hits hardware limits

**When to use:** Temporary solution before horizontal scaling

### Strategy 2: Horizontal Scaling (Add Servers)

**Distribute load across multiple servers:**

```
Load Balancer
    ├─ Server 1 (FastAPI)
    ├─ Server 2 (FastAPI)
    ├─ Server 3 (FastAPI)
    └─ Server 4 (FastAPI)

Result:
- QPS: 200 → 800 (4 servers)
- Latency: Stays ~100ms
- Cost: $100 → $300/month
```

**Pros:** Cost-effective, linear scaling
**Cons:** Requires load balancer, session management

**When to use:** Primary scaling approach

### Strategy 3: Data Sharding

**Partition data across databases:**

```
Shard Key: category

Vector DB 1: category in ["shoes", "boots"]
├─ 2.5M products
├─ 5GB index

Vector DB 2: category in ["shirts", "pants"]
├─ 2.5M products
├─ 5GB index

Query routing:
if category == "shoes":
    search(vector_db_1)
else:
    search(vector_db_2)
```

**Pros:** Scales data volume, improves latency
**Cons:** Complex routing, uneven distribution

**When to use:** Approaching Vector DB size limits

### Strategy 4: Caching

**Cache frequent queries:**

```
Query: "blue shoes" → Embedding cache

First query:
1. Compute CLIP embedding (50ms)
2. Vector search (20ms)
Total: 70ms

Second query (cached embedding):
1. Use cached embedding (0ms)
2. Vector search (20ms)
Total: 20ms

With 80% hit rate:
Average latency: 0.8 × 20 + 0.2 × 70 = 30ms
```

**Cache key:** `hash(query_text + filters)`

**Pros:** Reduces latency, saves CPU
**Cons:** Memory overhead, stale results

**When to use:** After horizontal scaling

### Strategy 5: Read Replicas

**Separate read and write paths:**

```
Write Path (1 server):
└─ Write requests (indexing)

Read Path (5 servers):
├─ Server 1: Search queries
├─ Server 2: Search queries
├─ Server 3: Search queries
├─ Server 4: Search queries
└─ Server 5: Search queries

Sync: Real-time replication
```

**Pros:** Unlimited read scalability
**Cons:** Replication complexity, eventual consistency

**When to use:** Read-heavy workloads

---

## Bottleneck Analysis

### CPU Bottleneck

**When:** Single server at 90%+ CPU

**Indicators:**
```
top -b -n 1 | grep python
# Python process consuming 350% CPU (3.5 cores)

# Each query takes: 50ms CLIP + 20ms Vector search
# At 200 QPS: 200 * 0.07s = 14 CPU-seconds per second
# Max capacity: 4 cores * 1000ms / 70ms = ~57 QPS per core
# 4 cores * 57 = ~228 QPS
```

**Solution: Add servers**
```python
if cpu_usage > 80:
    add_server()  # Auto-scale
```

### Memory Bottleneck

**When:** Vector DB running out of memory

**Indicators:**
```
free -h
# 1M products: 4GB used / 16GB available ✓ OK
# 10M products: 40GB used / 16GB available ✗ OOM

# Solution: Add shards
if memory_usage > 80:
    add_shard()
```

### Network Bottleneck

**When:** Latency > 100ms P99

**Indicators:**
```
# Check network latency
ping vector_db_host
# > 50ms indicates network issue

# Solution: Colocate services
# Same data center: <5ms latency
# Different region: >50ms latency
```

### Storage Bottleneck

**When:** Disk space running out

**Indicators:**
```
df -h /data
# 450GB used / 500GB available ✗ 90% full

# Solution: Archive old data
if disk_usage > 80:
    archive_old_products()
```

---

## Auto-Scaling Policy

### CPU-based Scaling

```python
def auto_scale_cpu():
    """Scale based on CPU usage"""
    
    cpu_usage = get_cpu_usage()
    num_servers = get_server_count()
    
    if cpu_usage > 80 and num_servers < 10:
        # Add server
        launch_server()
        log("✓ Launched new server (total: {num_servers+1})")
    
    elif cpu_usage < 20 and num_servers > 1:
        # Remove server
        shutdown_server()
        log("✓ Shutdown idle server (total: {num_servers-1})")

# Run every 60 seconds
schedule.every(60).seconds.do(auto_scale_cpu)
```

### QPS-based Scaling

```python
def auto_scale_qps():
    """Scale based on query throughput"""
    
    current_qps = get_qps()
    threshold_per_server = 150
    num_servers = get_server_count()
    
    required_servers = ceil(current_qps / threshold_per_server)
    
    if required_servers > num_servers:
        # Scale up
        for _ in range(required_servers - num_servers):
            launch_server()
    
    elif required_servers < num_servers:
        # Scale down
        for _ in range(num_servers - required_servers):
            shutdown_server()

# Run every 60 seconds
schedule.every(60).seconds.do(auto_scale_qps)
```

### Memory-based Sharding

```python
def auto_shard_data():
    """Add shards when memory limit reached"""
    
    for shard in shards:
        memory_usage = shard.get_memory_usage()
        
        if memory_usage > 80:  # 80% of capacity
            # Add new shard and rebalance
            new_shard = create_shard()
            rebalance_data(shards + [new_shard])
            log(f"✓ Created new shard (total: {len(shards)+1})")

# Run every 300 seconds
schedule.every(300).seconds.do(auto_shard_data)
```

---

## Performance Optimization

### CLIP Caching

```python
class CLIPCache:
    """Cache CLIP embeddings for queries"""
    
    def __init__(self, capacity=10000):
        self.cache = {}
        self.capacity = capacity
    
    def encode(self, text):
        # Check cache first
        if text in self.cache:
            return self.cache[text]
        
        # Compute embedding
        embedding = clip_model.encode(text)
        
        # Store in cache (with LRU eviction)
        if len(self.cache) > self.capacity:
            oldest = min(self.cache.items(), key=lambda x: x[1]['time'])
            del self.cache[oldest[0]]
        
        self.cache[text] = {
            'embedding': embedding,
            'time': time.time()
        }
        
        return embedding

# Cache hit rate monitoring
cache_hits = 0
cache_misses = 0

def get_hit_rate():
    return cache_hits / (cache_hits + cache_misses)
# Target: > 80% hit rate
```

### Batch Processing

```python
async def batch_search(queries):
    """Process multiple queries efficiently"""
    
    # Vectorize all at once (faster)
    embeddings = clip_model.encode_batch(queries)
    
    # Parallel vector search
    tasks = [
        search_vector_db(emb, limit=10)
        for emb in embeddings
    ]
    
    results = await asyncio.gather(*tasks)
    return results

# Performance improvement:
# 10 sequential queries: 700ms
# 10 batch queries: 150ms
# Speedup: 4.7x
```

### Connection Pooling

```python
# Configure connection pools
vector_db_pool = ConnectionPool(
    min_connections=10,
    max_connections=100,
    idle_timeout=300
)

mongodb_pool = ConnectionPool(
    min_connections=5,
    max_connections=50,
    idle_timeout=300
)

# Benefits:
# - Reuse connections (faster)
# - Limit resource usage
# - Better latency (no reconnect overhead)
```

---

## Cost Optimization

### Phase 1 → Phase 2 (100x growth)

```
Infrastructure Cost Breakdown:

Phase 1 (1M products, 100 QPS):
├─ 1 API server (t3.medium):        $30/month
├─ 1 Vector DB (m5.large):          $100/month
├─ 1 MongoDB (m5.large):            $100/month
├─ Load balancer:                   $20/month
└─ Total:                           $250/month

Phase 2 (10M products, 1000 QPS):
├─ 3 API servers (t3.medium):       $90/month
├─ 2 Vector DB (r5.2xlarge):        $600/month
├─ 1 MongoDB primary (r5.xlarge):   $300/month
├─ 1 MongoDB replica (r5.large):    $150/month
├─ Load balancer + VPC:             $50/month
└─ Total:                           $1,190/month

Cost per QPS:
Phase 1: $250 / 100 QPS = $2.50/QPS
Phase 2: $1,190 / 1,000 QPS = $1.19/QPS
Efficiency improvement: 2.1x
```

### Cost Reduction Tips

1. **Use spot instances** (30-50% cheaper)
   ```yaml
   Instance type: t3.medium (spot)
   Regular price: $30/month
   Spot price: $12/month
   Savings: 60%
   ```

2. **Reserved instances** (20-40% cheaper)
   ```yaml
   1-year: 30% discount
   3-year: 40% discount
   ```

3. **Data tiering**
   ```
   Hot data (last 30 days):    SSD (expensive)
   Warm data (30-90 days):     Standard disk (cheaper)
   Cold data (>90 days):       Archive (very cheap)
   ```

4. **Consolidate services**
   ```
   Before: 5 separate servers
   After: 2 consolidated servers
   Savings: 60%
   ```

---

## Monitoring & Alerts

### Key Metrics

```python
# Latency
metrics.histogram("query_latency_ms", latency)
alert_if("query_latency_p99 > 200ms")

# Throughput
metrics.counter("queries_total", 1)
alert_if("qps < 50")  # Dropped below minimum

# Resource usage
metrics.gauge("cpu_percent", cpu_usage)
metrics.gauge("memory_percent", memory_usage)
alert_if("cpu_percent > 85")

# Errors
metrics.counter("search_errors_total", 1, {"type": "timeout"})
alert_if("error_rate > 0.5%")

# Database
metrics.gauge("vector_db_documents", count)
metrics.gauge("vector_db_memory_gb", memory)
alert_if("vector_db_memory_gb > threshold")
```

### Dashboard

```
Omnisearch Monitoring Dashboard
├─ Real-time Metrics
│  ├─ QPS (current): 450
│  ├─ Latency P99: 95ms
│  ├─ Error rate: 0.1%
│  └─ Cache hit rate: 82%
│
├─ Resource Usage
│  ├─ API servers: 3/3 healthy
│  ├─ Vector DB: 35GB / 64GB (55%)
│  ├─ MongoDB: 8GB / 16GB (50%)
│  └─ Network: 250 Mbps / 1000 Mbps (25%)
│
├─ Scaling Metrics
│  ├─ Auto-scaling trigger: <30% CPU
│  ├─ Last scale-up: 2 hours ago
│  ├─ Current shards: 2
│  └─ Shard imbalance: 5%
│
└─ Alerts
   ├─ ⚠️ Vector DB memory at 80%
   └─ ✓ All systems operational
```

---

## Testing for Scale

### Load Testing

```python
from locust import HttpUser, task

class SearchUser(HttpUser):
    wait_time = between(1, 5)  # Wait 1-5s between requests
    
    @task(1)
    def text_search(self):
        """Simulate text search"""
        queries = ["shoes", "blue dress", "winter coat"]
        query = random.choice(queries)
        self.client.post("/search/text", json={
            "query": query,
            "top_k": 10
        })

# Run with locust:
# locust -f locustfile.py -u 100 -r 10 -t 1h
# 100 concurrent users, spawn 10/second, run for 1 hour
```

### Capacity Planning

```python
def calculate_capacity(
    products: int,
    qps: int,
    latency_p99_ms: int,
    availability: float
) -> Dict[str, Any]:
    """Calculate infrastructure needed"""
    
    # Vector DB: estimate memory needed
    memory_per_product_gb = 0.000004  # 4KB per vector
    vector_db_memory = products * memory_per_product_gb
    
    # API servers: estimate servers needed
    qps_per_server = 200
    api_servers = ceil(qps / qps_per_server)
    
    # MongoDB: estimate storage
    metadata_per_product_kb = 2
    mongodb_storage = (products * metadata_per_product_kb) / 1024 / 1024
    
    return {
        "vector_db_memory_gb": vector_db_memory,
        "api_servers": api_servers,
        "mongodb_storage_gb": mongodb_storage,
        "estimated_cost_monthly": api_servers * 100 + vector_db_memory * 50
    }

# Example
result = calculate_capacity(
    products=10_000_000,
    qps=1000,
    latency_p99_ms=100,
    availability=0.999
)

print(f"Vector DB: {result['vector_db_memory_gb']:.1f} GB")
print(f"API servers: {result['api_servers']}")
print(f"MongoDB: {result['mongodb_storage_gb']:.1f} GB")
print(f"Cost: ${result['estimated_cost_monthly']:.0f}/month")
```

---

## Migration Playbook

### From Single to Multi-Server

```yaml
Day 1: Preparation
  - Set up load balancer
  - Configure session tracking
  - Create deployment pipeline

Day 2: Deploy
  - Launch new servers (2 more)
  - Point 10% traffic to new servers
  - Monitor error rate

Day 3: Gradual Ramp
  - 25% traffic to new servers
  - Monitor latency and errors
  - Adjust if needed

Day 4: Full Cutover
  - 100% traffic to load balanced pool
  - Keep 1 original server as fallback
  - Monitor all metrics

Day 5: Cleanup
  - Remove fallback server
  - Document new setup
  - Update runbooks
```

### From Single to Multi-Shard

```yaml
Week 1: Planning
  - Analyze data distribution
  - Design shard key (category)
  - Plan rebalancing

Week 2: Setup
  - Create new shards
  - Set up replication
  - Test routing logic

Week 3: Migration
  - Gradually migrate data
  - Validate data integrity
  - Test query performance

Week 4: Cutover
  - Switch production traffic
  - Monitor for issues
  - Decommission old shard
```

---

## References

- [Microservices Architecture](https://martinfowler.com/microservices.html)
- [Database Sharding](https://en.wikipedia.org/wiki/Shard_(database_architecture))
- [Load Balancing](https://aws.amazon.com/elasticloadbalancing/)
- [Weaviate Scaling](https://weaviate.io/blog/scale-graphql-vector-search)
- [MongoDB Scaling](https://docs.mongodb.com/manual/sharding/)

---

## Scaling Checklist

- [ ] Load balancer configured
- [ ] Auto-scaling policies defined
- [ ] Database connection pooling enabled
- [ ] Caching layer implemented
- [ ] Monitoring and alerts in place
- [ ] Capacity planning completed
- [ ] Load testing performed
- [ ] Disaster recovery plan documented
- [ ] Runbooks updated
- [ ] Team trained on new architecture

---

**Status**: ✅ Complete
**Last Updated**: January 28, 2026
