# OmniSearch Architecture: RAG, User Memory, and Agent vs Search

This document explains how OmniSearch uses Retrieval-Augmented Generation (RAG), how user memory influences results, and how the PersonalShopperAgent differs from standard search.

- RAG Architecture
- How User Memory Influences Results
- Agent vs. Standard Search
- References

## RAG Architecture

OmniSearch blends vector retrieval with LLM generation to deliver grounded, personalized recommendations.

1) Retrieval (Vector Search)
- Inputs: text query and/or image
- Embeddings: Text and image embeddings via CLIP; fused into a single query vector
- Store: Weaviate vector database contains product vectors and metadata
- Search: Top-K similar products returned with ids, titles, attributes, and optional scores

Key code:
- Vector flow: [api/search.py](../api/search.py)
- Weaviate client: [db](../db) (e.g., `WeaviateClient` usage)
- CLIP embeddings: [services](../services) (e.g., `get_clip_service()` usage)

2) Augmentation (Context Building)
- User context: Preferences (colors, categories, price range) + recent purchases from MongoDB
- Search context: Top-K retrieved products (titles, attributes)
- Prompt context: `ContextRetriever` composes a concise, structured context for the LLM

Key code and docs:
- Context building: see CONTEXT_RETRIEVAL docs
  - [CONTEXT_RETRIEVAL.md](../CONTEXT_RETRIEVAL.md)
  - [CONTEXT_RETRIEVAL_SUMMARY.md](../CONTEXT_RETRIEVAL_SUMMARY.md)
  - Components referenced: `PreferenceAnalyzer`, `UserProfileService`

3) Generation (LLM Orchestration)
- `PersonalShopperAgent` calls the LLM with the constructed context
- Output: Structured JSON with 3 personalized recommendations + 1 wildcard
- DEV mode: When `DEV_MODE=true`, [services/llm_client.py](../services/llm_client.py) returns a mocked, deterministic JSON response to avoid external calls

Key code and docs:
- Endpoint orchestration and contracts: [docs/README_RECOMMEND.md](README_RECOMMEND.md), [docs/ENDPOINT_RECOMMEND.md](ENDPOINT_RECOMMEND.md), [models/agent.py](../models/agent.py)
- LLM client + DEV mode: [services/llm_client.py](../services/llm_client.py), [docs/DEV_MODE.md](DEV_MODE.md)

4) Post-processing
- The API shapes the agent response into `Recommendation` models with per-item product links
- The response preserves “why” explanations and 'wildcard' tagging

Key code:
- Response models and endpoint: [models/agent.py](../models/agent.py), [api](../api)

Summary diagram (conceptual):
Query/Image → Embeddings → Weaviate Top-K → ContextRetriever(User + Search) → LLM (Agent) → JSON Recommendations → API Response

## How User Memory Influences Results

User memory is captured and updated over time, then used to personalize both context and final recommendations.

1) Memory Capture and Updates
- Purchases/clicked recommendations flow into `UserProfileService.update_user_memory()`
  - Adds item to `past_purchases`
  - Extracts and adds `preferred_colors` and `preferred_categories`
  - Expands `price_range` when a product falls outside the current bounds
- Auto-create: creates a user profile if one doesn’t exist
- Configurable: `auto_update_preferences=False` (e.g., gifts) skips preference changes

Key code and docs:
- Update logic: [db/user_service.py](../db/user_service.py)
- Full guide and examples: [docs/UPDATE_USER_MEMORY.md](UPDATE_USER_MEMORY.md), [docs/UPDATE_USER_MEMORY_SUMMARY.md](UPDATE_USER_MEMORY_SUMMARY.md)

2) Memory → Retrieval + Generation
- Retrieval bias: Preferences can be used to influence ranking and filtering (e.g., favor colors/categories); implementation emphasizes soft influence via prompt/context rather than hard filters to keep diversity
- Context augmentation: `ContextRetriever` injects user preferences, recent purchases, and price profile into the LLM context
- Generation alignment: The agent asks the LLM to explain “why” each item matches the user (e.g., “Matches your preference for casual blue apparel”), reinforcing preference-aware results

3) Practical Effects
- Color affinity: A user with `blue` in `preferred_colors` sees more blue apparel surfaced and picked by the agent
- Category focus: Categories the user interacts with are emphasized in the context presented to the LLM
- Price calibration: `price_range` helps the agent avoid outliers; range expands only when the user meaningfully purchases outside it
- Noise handling: Empty or missing fields are safely handled; matching is case-insensitive for a smooth UX

4) Controls and Edge Cases
- Gifts/browsing: Use `auto_update_preferences=False` to avoid skewing a user’s long-term profile
- Cold start: New users are auto-created, with defaults that quickly adapt as `update_user_memory()` is called

## Agent vs. Standard Search

Standard Search
- Operation: Compute embedding → nearest neighbors in Weaviate → return products
- Characteristics: Deterministic, fast, no LLM, minimal personalization, no “why” explanations
- Best for: Quick similarity lookups, keyword-to-vector retrieval, and infrastructure-level APIs

PersonalShopperAgent (Agent)
- Orchestration: Retrieve (Weaviate) + Augment (user + search context) + Generate (LLM)
- Personalization: Learns and applies user preferences (colors, categories, price) and purchase history
- Output: Structured JSON with explanations and a deliberate “wildcard” item for exploration
- Multimodal: Accepts text and/or image, fuses signals for richer retrieval
- Trade-offs: Slightly higher latency and cost in production (LLM), mitigated by `DEV_MODE` and caching strategies
- Robustness: DEV mode ensures reliable local/dev operation without external calls

When to use which
- Use Standard Search for raw nearest-neighbor results, infrastructure integration, or when LLM is not desired
- Use PersonalShopperAgent for tailored, explainable, and more delightful shopping experiences that adapt to the user over time

## References
- Endpoint overview and flows: [docs/README_RECOMMEND.md](README_RECOMMEND.md), [docs/ENDPOINT_RECOMMEND.md](ENDPOINT_RECOMMEND.md), [docs/IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- Context and memory: [CONTEXT_RETRIEVAL.md](../CONTEXT_RETRIEVAL.md), [CONTEXT_RETRIEVAL_SUMMARY.md](../CONTEXT_RETRIEVAL_SUMMARY.md), [docs/UPDATE_USER_MEMORY.md](UPDATE_USER_MEMORY.md)
- Agent models and contracts: [models/agent.py](../models/agent.py)
- LLM client and dev mode: [services/llm_client.py](../services/llm_client.py), [docs/DEV_MODE.md](DEV_MODE.md)
- Settings: [config/settings.py](../config/settings.py)
