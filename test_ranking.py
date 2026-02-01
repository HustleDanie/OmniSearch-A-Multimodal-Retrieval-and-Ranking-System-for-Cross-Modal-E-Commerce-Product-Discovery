#!/usr/bin/env python3
"""Test the updated ranking with workout equipment query."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import get_search_service

search_service = get_search_service()

# Test the query
results = search_service.search_by_text(
    query_text="workout equipment",
    top_k=5,
    enable_reranking=True,
    enable_debug=True
)

print("Search Results for 'workout equipment':")
print("=" * 70)
for i, result in enumerate(results, 1):
    print(f"\n{i}. {result.title}")
    print(f"   Category: {result.category}")
    print(f"   Color: {result.color}")
    print(f"   Similarity: {result.similarity:.4f}")
    if result.debug_scores:
        print(f"   Debug Scores:")
        for key, val in result.debug_scores.items():
            print(f"     - {key}: {val:.4f}")
