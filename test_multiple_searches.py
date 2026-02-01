#!/usr/bin/env python3
"""Test multiple category-aware searches."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import get_search_service

search_service = get_search_service()

test_queries = [
    "blue electronics",
    "red dress",
    "black shoes",
    "professional furniture"
]

for query in test_queries:
    print(f"\n{'='*70}")
    print(f"Search: '{query}'")
    print(f"{'='*70}")
    
    results = search_service.search_by_text(
        query_text=query,
        top_k=5,
        enable_reranking=True,
        enable_debug=False
    )
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.title:45s} | {result.category:15s} | Sim: {result.similarity:.4f}")
