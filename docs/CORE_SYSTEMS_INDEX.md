# OmniSearch Core Systems Documentation Index

## Overview

Complete documentation for three critical systems that power OmniSearch at scale:

1. **Experimentation System** - A/B testing framework for search variants
2. **Vector Database Tuning** - Weaviate optimization for vector search
3. **Scalability Strategy** - Infrastructure scaling from 1M to 100M products

---

## 📚 Documentation Files

### 1. Experimentation System
**File:** [EXPERIMENTATION_SYSTEM.md](EXPERIMENTATION_SYSTEM.md)

**Purpose:** A/B testing framework for comparing search algorithm variants

**Key Topics:**
- User variant assignment
- Event tracking (search, click, impression)
- Metrics calculation (CTR, dwell time)
- Statistical significance testing
- Experiment lifecycle

**Key Classes:**
```python
ExperimentVariant         # enum: SEARCH_V1, SEARCH_V2
ExperimentAssignment      # user → variant mapping
SearchEvent               # tracks search queries
ClickEvent                # tracks user interactions
ExperimentService         # main service
```

**Quick Start:**
```python
# Assign user to variant
ab_service = ABTestingService()
assignment = ab_service.assign_user("user_123")

# Track search
event = SearchEvent(
    user_id="user_123",
    variant=assignment.variant,
    query="blue shoes",
    results_count=42
)
ab_service.track_event(event)

# Calculate metrics
metrics = ab_service.calculate_ctr(variant_filter="search_v2")
```

**Key Sections:**
- [Architecture](#architecture) - System design
- [Core Components](#core-components) - Classes and data models
- [Usage](#usage) - Step-by-step integration
- [Data Storage](#data-storage) - MongoDB collections
- [Experiment Lifecycle](#experiment-lifecycle) - Design → Deploy → Analyze
- [Best Practices](#best-practices) - Sample size, duration, metrics
- [Common Patterns](#common-patterns) - Gradual rollout, holdouts
- [Troubleshooting](#troubleshooting) - Debug assignment, events, metrics

---

### 2. Vector Database Tuning
**File:** [VECTOR_DB_TUNING.md](VECTOR_DB_TUNING.md)

**Purpose:** Optimize Weaviate for vector search performance and scale

**Key Topics:**
- Schema design for optimal performance
- HNSW index configuration
- Query optimization techniques
- Performance tuning and bottleneck resolution
- Scaling strategies

**Key Concepts:**
```
ef_construction: 200        # Index quality vs speed
ef: 128                     # Query-time search breadth
max_connections: 32         # Graph connectivity
VECTOR_CACHE_SIZE: 80%      # Memory optimization
distance_metric: cosine     # Similarity computation
```

**Quick Start:**
```python
# Create optimized collection
client.collections.create(
    name="Product",
    vectorizer_config=None,  # Manual vectorization
    vector_config={
        "size": 512,              # CLIP dimension
        "distance": "cosine"
    }
)

# Optimized query
results = collection.query.near_vector(
    near_vector=query_embedding,
    where=Filter.by_property("category").equal("shoes"),
    limit=10,
    return_properties=["product_id", "title", "price"]
)
```

**Key Sections:**
- [Schema Design](#schema-design) - Property configuration
- [Indexing Strategy](#indexing-strategy) - HNSW parameters
- [Query Optimization](#query-optimization) - Performance techniques
- [Performance Tuning](#performance-tuning) - Memory, caching, monitoring
- [Scaling Strategies](#scaling-strategies) - 1M → 10M → 100M products
- [Common Issues](#common-issues--solutions) - Troubleshooting guide
- [Benchmarking](#benchmarking) - Performance testing

**Expected Performance:**
```
1M products:    100-150ms latency, 100-200 QPS
10M products:   80-120ms latency, 500-1000 QPS
100M products:  60-100ms latency, 2000-5000 QPS
```

---

### 3. Scalability Strategy
**File:** [SCALABILITY_STRATEGY.md](SCALABILITY_STRATEGY.md)

**Purpose:** Plan and execute infrastructure scaling as product catalog grows

**Key Topics:**
- Scaling dimensions (QPS, data volume, latency)
- Scaling timeline and phases
- Scaling strategies (vertical, horizontal, sharding, caching)
- Auto-scaling policies
- Cost optimization
- Performance optimization

**Architecture Layers:**
```
┌─ Load Balancer (Nginx/HAProxy)
├─ API Servers (FastAPI × N)
├─ Vector Database (Weaviate × shards)
├─ Metadata Store (MongoDB × replicas)
└─ Cache Layer (Redis)
```

**Scaling Timeline:**
```
Phase 1 (Current): 1M products, 100-200 QPS, $500/month
Phase 2 (6-12mo): 5M products, 300-600 QPS, $2,000/month
Phase 3 (12-24mo): 50M products, 1000-2000 QPS, $8,000/month
Phase 4 (24+mo): 100M+ products, 5000+ QPS, $20,000+/month
```

**Quick Start:**
```python
# Auto-scaling policy
def auto_scale_cpu():
    cpu = get_cpu_usage()
    if cpu > 80:
        launch_server()      # Add server
    elif cpu < 20:
        shutdown_server()    # Remove server

# Sharding strategy
if memory_usage > 80:
    add_shard()             # Split data
    rebalance_data()

# Caching strategy
cache = CLIPCache(capacity=10000)
embedding = cache.encode("blue shoes")  # ~80% hit rate
```

**Key Sections:**
- [Current Architecture](#current-architecture) - System design
- [Scaling Dimensions](#scaling-dimensions) - QPS, data, latency
- [Scaling Timeline](#scaling-timeline) - Growth phases
- [Scaling Strategies](#scaling-strategies) - Vertical, horizontal, sharding
- [Bottleneck Analysis](#bottleneck-analysis) - CPU, memory, network, storage
- [Auto-Scaling](#auto-scaling-policy) - Automated scaling
- [Performance Optimization](#performance-optimization) - Caching, batching
- [Cost Optimization](#cost-optimization) - Reducing expenses
- [Monitoring](#monitoring--alerts) - Key metrics and alerts

**Cost Per QPS Evolution:**
```
Phase 1: $2.50 per QPS
Phase 2: $1.19 per QPS (2.1x more efficient)
Phase 3: $0.35 per QPS (7x more efficient)
```

---

## 🔗 Integration Map

### How They Work Together

```
User Request
    │
    └─→ FastAPI Server
        │
        ├─→ A/B Testing [EXPERIMENTATION]
        │   └─ Assign user to variant
        │   └─ Route to appropriate search
        │
        ├─→ CLIP Encoding
        │   └─ Cache hits? [SCALABILITY]
        │
        ├─→ Vector Search [VECTOR_DB_TUNING]
        │   └─ Weaviate with HNSW index
        │   └─ Filter by metadata
        │
        ├─→ Track Event [EXPERIMENTATION]
        │   └─ Log search, click, impression
        │
        └─→ Response
            └─ Load Balancer [SCALABILITY]
```

### Data Flow

```
Database Layer:
├─ MongoDB
│  ├─ User assignments [EXPERIMENTATION]
│  ├─ Events (searches, clicks) [EXPERIMENTATION]
│  └─ Product metadata [VECTOR_DB_TUNING]
│
├─ Weaviate
│  ├─ Product vectors [VECTOR_DB_TUNING]
│  └─ Shards for scale [SCALABILITY]
│
└─ Redis
   └─ Embedding cache [SCALABILITY]
```

---

## 📊 Metrics & Monitoring

### Key Performance Indicators

| Metric | Target | Document | Scaling |
|--------|--------|----------|---------|
| Query Latency P99 | <100ms | [Vector DB](VECTOR_DB_TUNING.md#performance-tuning) | [Scalability](SCALABILITY_STRATEGY.md#monitoring--alerts) |
| Throughput (QPS) | 100-200 | [Scalability](SCALABILITY_STRATEGY.md#current-state--scale) | [Scaling Timeline](SCALABILITY_STRATEGY.md#scaling-timeline) |
| Vector Cache Hit Rate | >80% | [Scalability](SCALABILITY_STRATEGY.md#clip-caching) | [Optimization](SCALABILITY_STRATEGY.md#performance-optimization) |
| CTR (A/B Test) | Baseline | [Experimentation](EXPERIMENTATION_SYSTEM.md#metrics-calculation) | N/A |
| Statistical Significance | p<0.05 | [Experimentation](EXPERIMENTATION_SYSTEM.md#statistical-analysis) | N/A |
| Recall (Vector Search) | >90% | [Vector DB](VECTOR_DB_TUNING.md#issue-3-poor-recall-90) | N/A |

### Monitoring Dashboard

```
Real-time Metrics:
├─ Latency: 95ms P99 ✓
├─ QPS: 450 (capacity: 600) ✓
├─ Error Rate: 0.1% ✓
├─ Cache Hit Rate: 82% ✓
│
A/B Testing Metrics:
├─ Search V1: CTR 12.3%, N=2510
├─ Search V2: CTR 18.7%, N=2490
└─ Difference: +6.4% (p=0.0012) ✓ SIGNIFICANT
│
Vector DB Status:
├─ Index Size: 35GB / 64GB (55%)
├─ Query Time: 85ms avg
└─ Recall: 95% (target: 90%)
│
Scalability Status:
├─ CPU: 45% (threshold: 80%)
├─ Memory: 50% (threshold: 80%)
├─ Servers: 3/3 healthy
└─ Auto-scale: Idle
```

---

## 🚀 Quick Reference

### How to...

#### Run an A/B Test
See [Experimentation System: Experiment Lifecycle](EXPERIMENTATION_SYSTEM.md#experiment-lifecycle)

```python
# 1. Design
experiment = create_experiment(
    name="ranking_v2",
    hypothesis="Re-ranking improves CTR",
    sample_size=5000,
    duration_days=14
)

# 2. Run (automatic event tracking)
# Users assigned to variants, events logged

# 3. Analyze
report = generate_report(experiment_id)
```

#### Optimize Vector Search Query
See [Vector DB Tuning: Query Optimization](VECTOR_DB_TUNING.md#query-optimization)

```python
# Add filters early (reduce candidates)
results = collection.query.near_vector(
    near_vector=embedding,
    where=Filter.by_property("category").equal("shoes"),  # Early filter
    limit=10,
    return_properties=["product_id", "title"]  # Only needed fields
)
```

#### Scale from 100K to 1M QPS
See [Scalability Strategy: Scaling Strategies](SCALABILITY_STRATEGY.md#scaling-strategies)

```python
# 1. Horizontal scale (add servers)
launch_servers(n=3)  # 100 → 300 QPS

# 2. Add caching
cache = CLIPCache()  # 30% latency reduction

# 3. Shard data
add_shard()  # If Vector DB memory > 80%

# 4. Enable auto-scaling
enable_auto_scaling(cpu_threshold=80)
```

#### Debug Slow Queries
See [Vector DB Tuning: Issue Resolution](VECTOR_DB_TUNING.md#issue-1-slow-queries-500ms)

```python
# 1. Check latency breakdown
explain = query.near_vector(..., explain=True)

# 2. Reduce ef value
config.ef = 64  # Faster but less accurate

# 3. Add property indexes
db.create_index([("category", 1)])

# 4. Increase vector cache
VECTOR_CACHE_SIZE_PERCENT = 90  # Was 80%
```

---

## 📖 Reading Order

### For Operators/DevOps
1. [Scalability Strategy](SCALABILITY_STRATEGY.md) - Overall architecture
2. [Vector DB Tuning](VECTOR_DB_TUNING.md) - Performance optimization
3. [Experimentation System](EXPERIMENTATION_SYSTEM.md) - Monitoring metrics

### For Backend Engineers
1. [Experimentation System](EXPERIMENTATION_SYSTEM.md) - API integration
2. [Vector DB Tuning](VECTOR_DB_TUNING.md) - Query optimization
3. [Scalability Strategy](SCALABILITY_STRATEGY.md) - Performance planning

### For Data Scientists
1. [Experimentation System](EXPERIMENTATION_SYSTEM.md) - Statistical analysis
2. [Vector DB Tuning](VECTOR_DB_TUNING.md) - Embedding quality
3. [Scalability Strategy](SCALABILITY_STRATEGY.md) - Growth forecasting

### For Product Managers
1. [Experimentation System](EXPERIMENTATION_SYSTEM.md) - Feature validation
2. [Scalability Strategy](SCALABILITY_STRATEGY.md) - Growth capacity
3. [Vector DB Tuning](VECTOR_DB_TUNING.md) - Technical requirements

---

## 🔍 Key Concepts

### Experimentation System
- **Variant**: Different search algorithm (SEARCH_V1, SEARCH_V2)
- **Assignment**: User → Variant mapping (persistent per user)
- **Event**: Searchable interaction (query, click, impression)
- **Metric**: Computed KPI (CTR, dwell time, conversion)
- **Significance**: Statistical confidence in result (p-value < 0.05)

### Vector Database Tuning
- **HNSW**: Hierarchical Navigable Small World index (approximate search)
- **ef_construction**: Quality vs speed during indexing
- **ef**: Query-time search breadth (higher = more accurate, slower)
- **Recall**: % of true nearest neighbors found (target: >90%)
- **Latency**: Query response time (target: <100ms P99)

### Scalability Strategy
- **QPS**: Queries per second (throughput)
- **Latency**: Response time (target: <100ms)
- **Sharding**: Horizontal partitioning (scale data volume)
- **Replication**: Copies for read scaling or backup
- **Auto-scaling**: Automatic resource adjustment based on load

---

## 🔧 Configuration Files

### Experimentation
```python
# services/ab_testing.py
ExperimentVariant()      # Define variants
ExperimentAssignment()   # User assignment
SearchEvent()            # Event tracking
ABTestingService()       # Main service
```

### Vector Database
```python
# db/weaviate_client.py
create_product_schema()         # Schema setup
vector_config HNSW()           # Index config
query.near_vector()            # Query method
```

### Scalability
```yaml
# docker-compose.yml
services:
  api:
    replicas: 3                # Horizontal scaling
  weaviate:
    environment:
      VECTOR_CACHE_SIZE: 80%   # Optimization
  mongodb:
    replicas: 3                # High availability
```

---

## 📈 Success Metrics

### Experimentation ✅
- [ ] Assign users consistently (same variant each time)
- [ ] Track 100+ events per variant per day
- [ ] Calculate CTR with statistical significance
- [ ] Deploy winning variant based on results

### Vector Database ✅
- [ ] Query latency <100ms P99
- [ ] Recall >90% on test queries
- [ ] Index built in <30 minutes
- [ ] Support 1M+ products

### Scalability ✅
- [ ] Auto-scale from 100 to 1000 QPS
- [ ] Add shards when memory >80%
- [ ] Maintain latency during growth
- [ ] Cost per QPS decreases with scale

---

## 🆘 Support & Troubleshooting

### Quick Links
- **Experimentation Issues**: [Troubleshooting](EXPERIMENTATION_SYSTEM.md#troubleshooting)
- **Vector DB Issues**: [Problem Resolution](VECTOR_DB_TUNING.md#common-issues--solutions)
- **Scaling Issues**: [Bottleneck Analysis](SCALABILITY_STRATEGY.md#bottleneck-analysis)

### Common Problems

| Problem | Document | Solution |
|---------|----------|----------|
| Variant assignment inconsistent | [Experimentation](EXPERIMENTATION_SYSTEM.md#issue-variant-assignment-not-consistent) | Use hash-based assignment |
| Queries too slow | [Vector DB](VECTOR_DB_TUNING.md#issue-1-slow-queries-500ms) | Reduce ef, add indexes |
| Memory running out | [Vector DB](VECTOR_DB_TUNING.md#issue-2-high-memory-usage) | Enable compression, shard |
| Low recall | [Vector DB](VECTOR_DB_TUNING.md#issue-3-poor-recall-90) | Increase ef_construction |
| High CPU | [Scalability](SCALABILITY_STRATEGY.md#cpu-bottleneck) | Add servers |
| OOM errors | [Scalability](SCALABILITY_STRATEGY.md#memory-bottleneck) | Add shards |

---

## 📚 Additional Resources

### Official Documentation
- [Weaviate Docs](https://weaviate.io/developers/weaviate/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [A/B Testing Handbook](https://www.optimizely.com/ab-testing/)

### Academic Papers
- [HNSW Algorithm](https://arxiv.org/abs/1603.09320)
- [Vector Database Performance](https://arxiv.org/abs/2211.14626)
- [Experimentation at Scale](https://netflix.techblog.com/scaling-testing-at-netflix-5e74f02649a0)

### Tools & Frameworks
- [Load Testing: Locust](https://locust.io/)
- [Monitoring: Prometheus](https://prometheus.io/)
- [Logging: ELK Stack](https://www.elastic.co/what-is/elk-stack)

---

## 🎯 Next Steps

1. **Read** the relevant documentation for your role
2. **Understand** the architecture and key concepts
3. **Implement** the recommendations in your environment
4. **Monitor** using the provided metrics
5. **Iterate** based on observed performance

---

## 📝 Document Info

| Document | Pages | Last Updated | Status |
|----------|-------|--------------|--------|
| [EXPERIMENTATION_SYSTEM.md](EXPERIMENTATION_SYSTEM.md) | ~15 | Jan 28, 2026 | ✅ Complete |
| [VECTOR_DB_TUNING.md](VECTOR_DB_TUNING.md) | ~18 | Jan 28, 2026 | ✅ Complete |
| [SCALABILITY_STRATEGY.md](SCALABILITY_STRATEGY.md) | ~20 | Jan 28, 2026 | ✅ Complete |
| **Total** | **~53** | Jan 28, 2026 | ✅ Complete |

---

**Status**: ✅ Complete
**Total Content**: 53+ pages, 15,000+ lines, 3 systems
**Created**: January 28, 2026
