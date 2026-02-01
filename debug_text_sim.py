#!/usr/bin/env python3
"""Debug text similarity scoring."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ranking import text_similarity, _bow, _cosine_sim

query = "workout equipment"
titles = [
    "Red Basketball",
    "Black Dumbbells",
    "Green Yoga Mat",
    "Black Tennis Racket",
    "Blue Skateboard"
]

print(f"Query: '{query}'")
print(f"Query bag-of-words: {_bow(query)}")
print("=" * 60)

for title in titles:
    sim = text_similarity(query, title)
    bow_title = _bow(title)
    print(f"\nTitle: '{title}'")
    print(f"  Bag-of-words: {bow_title}")
    print(f"  Text similarity: {sim:.4f}")
