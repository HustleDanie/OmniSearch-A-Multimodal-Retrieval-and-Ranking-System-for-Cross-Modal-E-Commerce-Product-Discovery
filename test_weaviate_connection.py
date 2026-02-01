#!/usr/bin/env python
"""Quick test script to verify Weaviate connection."""
from db import WeaviateClient

client = WeaviateClient()
try:
    client.connect()
    print("✓ Success! Weaviate is connected.")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
