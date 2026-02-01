#!/usr/bin/env python3
"""Debug script to test search functionality."""
import numpy as np
from db import WeaviateConnection
from services import get_clip_service

# Check database
with WeaviateConnection() as client:
    info = client.get_collection_info()
    print(f'Total products in database: {info.get("total_objects", 0)}')
    
    # Test different queries
    clip_service = get_clip_service()
    
    queries = ["black jeep", "green piano"]
    
    for query in queries:
        print(f"\n--- Searching for: '{query}' ---")
        
        # Get query embedding
        query_vector = clip_service.embed_text(query)
        print(f"Query embedding shape: {query_vector.shape}")
        print(f"Query embedding (first 10): {query_vector[:10]}")
        
        # Search
        result = client.search_by_vector(
            query_vector=query_vector,
            limit=3
        )
        
        print(f"Results:")
        for i, r in enumerate(result):
            props = r['properties']
            sim = r['similarity']
            print(f"{i+1}. {props.get('title')} ({props.get('color')} {props.get('category')}) - Similarity: {sim:.4f}")
