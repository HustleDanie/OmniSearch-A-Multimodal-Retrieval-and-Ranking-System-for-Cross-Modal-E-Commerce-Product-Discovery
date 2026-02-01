#!/usr/bin/env python3
"""Test category-aware search."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import get_search_service

search_service = get_search_service()

# Test the query
print("Search Results for 'blue electronics':")
print("=" * 70)

results = search_service.search_by_text(
    query_text="blue electronics",
    top_k=10,
    enable_reranking=True,
    enable_debug=False
)

for i, result in enumerate(results, 1):
    print(f"{i}. {result.title}")
    print(f"   Category: {result.category}")
    print(f"   Color: {result.color}")
    print(f"   Similarity: {result.similarity:.4f}")
    print()
