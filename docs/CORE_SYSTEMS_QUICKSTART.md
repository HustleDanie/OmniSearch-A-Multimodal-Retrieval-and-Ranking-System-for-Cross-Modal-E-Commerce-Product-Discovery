# 🚀 Quick Start: Core Systems

**3 essential systems documented. Start here.**

---

## 📍 What You Need to Know

### System 1: Experimentation 🧪
**What**: A/B test search variants  
**Where**: [EXPERIMENTATION_SYSTEM.md](EXPERIMENTATION_SYSTEM.md)  
**Use for**: Compare search algorithms, measure impact

**Quick Example:**
```python
# Assign user to variant
ab_service = ABTestingService()
assignment = ab_service.assign_user("user_123")  # Gets SEARCH_V1 or SEARCH_V2

# Track their actions
event = SearchEvent(
    user_id="user_123",
    variant=assignment.variant,
    query="blue shoes",
    results_count=42
)
ab_service.track_event(event)

# Calculate winner
stats = ab_service.compare_variants("search_v1", "search_v2", metric="ctr")
# Output: V2 wins by 6.4% (p=0.0012) ✓ SIGNIFICANT
```

---

### System 2: Vector DB Tuning 🎯
**What**: Optimize vector search performance  
**Where**: [VECTOR_DB_TUNING.md](VECTOR_DB_TUNING.md)  
**Use for**: Improve query latency, scale to millions of products

**Quick Example:**
```python
# Optimized query (10x faster)
results = collection.query.near_vector(
    near_vector=embedding,
    where=Filter.by_property("category").equal("shoes"),  # Filter first
    limit=10,
    return_properties=["product_id", "title", "price"]  # Only needed fields
)

# Tuning parameter: ef=128 (good default)
# For 95% recall + 150ms latency
```

---

### System 3: Scalability 📈
**What**: Scale infrastructure as product catalog grows  
**Where**: [SCALABILITY_STRATEGY.md](SCALABILITY_STRATEGY.md)  
**Use for**: Plan growth, auto-scale, optimize costs

**Quick Example:**
```python
# Auto-scaling policy
def auto_scale():
    if cpu_usage > 80:
        launch_server()      # Add server
    elif memory_usage > 80:
        add_shard()          # Split data
    
# Growth phases:
# Phase 1: 1M products, 100 QPS, $500/mo
# Phase 2: 5M products, 300 QPS, $2k/mo
# Phase 3: 50M products, 1k QPS, $8k/mo
```

---

## 🎯 By Your Role

### 👨‍💼 Backend Engineer
1. **Integrate A/B testing**: [Usage section](EXPERIMENTATION_SYSTEM.md#usage)
2. **Optimize queries**: [Query optimization](VECTOR_DB_TUNING.md#query-optimization)
3. **Add caching**: [CLIPCache](SCALABILITY_STRATEGY.md#clip-caching)

**Time to implementation**: 2-4 hours

### 🏗️ DevOps Engineer
1. **Understand growth phases**: [Timeline](SCALABILITY_STRATEGY.md#scaling-timeline)
2. **Configure auto-scaling**: [Policies](SCALABILITY_STRATEGY.md#auto-scaling-policy)
3. **Monitor metrics**: [Dashboard](SCALABILITY_STRATEGY.md#dashboard)

**Time to implementation**: 4-8 hours

### 🔬 Data Scientist
1. **Design experiment**: [Lifecycle](EXPERIMENTATION_SYSTEM.md#experiment-lifecycle)
2. **Analyze results**: [Statistical analysis](EXPERIMENTATION_SYSTEM.md#statistical-analysis)
3. **Load test**: [Framework](SCALABILITY_STRATEGY.md#testing-for-scale)

**Time to implementation**: 3-6 hours

### 🎯 Product Manager
1. **Run experiment**: [Experiment lifecycle](EXPERIMENTATION_SYSTEM.md#experiment-lifecycle)
2. **Plan growth**: [Timeline](SCALABILITY_STRATEGY.md#scaling-timeline)
3. **Track metrics**: [KPIs](CORE_SYSTEMS_INDEX.md#-metrics--monitoring)

**Time to understand**: 30 minutes

---

## ⚡ 5-Minute Summary

### Experimentation System ✅
- Users assigned to variants (SEARCH_V1 vs SEARCH_V2)
- Events tracked (searches, clicks, impressions)
- Metrics calculated (CTR, dwell time, etc.)
- Statistics determine winner
- Deploy or rollback based on results

**Key metric**: CTR (click-through rate)

### Vector DB Tuning ✅
- HNSW index balances accuracy vs speed
- Filters reduce candidates before ranking
- Cache hits save 50% of latency
- Scales to millions of products

**Key metric**: Query latency (<100ms P99)

### Scalability Strategy ✅
- Add servers when CPU > 80%
- Add shards when memory > 80%
- Cache frequent queries
- Cost per QPS decreases with scale

**Key metric**: QPS (queries per second)

---

## 🚀 Today's Task

### Option 1: Just Learn (30 min)
→ Read [CORE_SYSTEMS_INDEX.md](CORE_SYSTEMS_INDEX.md)

### Option 2: Quick Implementation (2-4 hours)
1. Add one experimentation endpoint
2. Optimize one query with filters
3. Enable query caching

### Option 3: Full Setup (1-2 days)
1. Implement full A/B testing
2. Tune vector DB indexes
3. Set up auto-scaling

---

## 🔗 Files

```
docs/
├─ CORE_SYSTEMS_DELIVERY.md        ← This file (delivery summary)
├─ CORE_SYSTEMS_INDEX.md            ← Master index (integration map)
├─ EXPERIMENTATION_SYSTEM.md        ← A/B testing (15 pages)
├─ VECTOR_DB_TUNING.md              ← Performance (18 pages)
└─ SCALABILITY_STRATEGY.md          ← Infrastructure (20 pages)
```

---

## ❓ Common Questions

**Q: Where do I start?**  
A: Read [CORE_SYSTEMS_INDEX.md](CORE_SYSTEMS_INDEX.md) (10 min), then pick your topic.

**Q: How do I add a new search variant?**  
A: See [Experimentation System: Usage](EXPERIMENTATION_SYSTEM.md#usage)

**Q: Queries are too slow (>500ms)?**  
A: See [Vector DB: Issue 1](VECTOR_DB_TUNING.md#issue-1-slow-queries-500ms)

**Q: When should I add more servers?**  
A: See [Scalability: Bottleneck Analysis](SCALABILITY_STRATEGY.md#bottleneck-analysis)

**Q: How do I run an A/B test?**  
A: See [Experimentation: Experiment Lifecycle](EXPERIMENTATION_SYSTEM.md#experiment-lifecycle)

---

## 📊 By The Numbers

| System | Pages | Sections | Code Examples | Issues Covered |
|--------|-------|----------|----------------|-----------------|
| Experimentation | 15 | 12 | 15 | 3 |
| Vector DB | 18 | 12 | 25 | 3 |
| Scalability | 20 | 14 | 30 | 4 |
| **Total** | **53** | **38** | **70** | **10** |

---

## ✅ Next Steps

1. **Read** one document relevant to your role (30-60 min)
2. **Try** one code example (30 min)
3. **Ask** questions if stuck
4. **Implement** one recommendation (2-4 hours)

---

**Let's scale OmniSearch! 🚀**

---

**Status**: ✅ Complete  
**Created**: January 28, 2026  
**Location**: `docs/CORE_SYSTEMS_DELIVERY.md`
