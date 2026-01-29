#!/usr/bin/env python
"""
Demo script showing how to use the /agent/recommend endpoint.
Run this after starting the FastAPI server: python main.py
"""
import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"


def recommend_text(user_id: str, query: str, top_k: int = 5) -> dict:
    """Get recommendations based on text query."""
    print(f"\n📝 Recommending for text query: '{query}'")
    print(f"   User: {user_id}, Top K: {top_k}")
    
    response = requests.post(
        f"{BASE_URL}/agent/recommend",
        data={
            "user_id": user_id,
            "query": query,
        },
        params={"top_k": top_k}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Got {len(data['recommendations'])} recommendations")
        return data
    else:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   {response.json()}")
        return None


def recommend_image(user_id: str, image_path: str, top_k: int = 5) -> dict:
    """Get recommendations based on image."""
    print(f"\n🖼️  Recommending for image: {image_path}")
    print(f"   User: {user_id}, Top K: {top_k}")
    
    with open(image_path, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/agent/recommend",
            files={"image": f},
            data={"user_id": user_id},
            params={"top_k": top_k}
        )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Got {len(data['recommendations'])} recommendations")
        return data
    else:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   {response.json()}")
        return None


def recommend_multimodal(
    user_id: str,
    query: str,
    image_path: str,
    top_k: int = 5,
    image_weight: float = 0.6,
    text_weight: float = 0.4
) -> dict:
    """Get recommendations using both text and image (multimodal)."""
    print(f"\n🎯 Recommending with multimodal search")
    print(f"   Query: '{query}', Image: {image_path}")
    print(f"   Weights: image={image_weight}, text={text_weight}")
    
    with open(image_path, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/agent/recommend",
            files={"image": f},
            data={
                "user_id": user_id,
                "query": query,
            },
            params={
                "top_k": top_k,
                "image_weight": image_weight,
                "text_weight": text_weight
            }
        )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Got {len(data['recommendations'])} recommendations")
        return data
    else:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   {response.json()}")
        return None


def print_recommendations(data: dict) -> None:
    """Pretty print recommendations."""
    print("\n📊 Recommendations:")
    print("=" * 80)
    
    for rec in data.get("recommendations", []):
        badge = "⭐ WILDCARD" if rec.get("is_wildcard") else f"#{rec.get('rank')}"
        print(f"\n{badge}: {rec.get('title', 'Unknown')}")
        print(f"   Why: {rec.get('description', 'No description')}")
        if rec.get("product_link"):
            print(f"   Link: {rec['product_link']}")
        if rec.get("product_details"):
            details = rec["product_details"]
            print(f"   Details: {details.get('color', '?')} | {details.get('category', '?')} | ${details.get('price', '?')}")
    
    print(f"\n   Considered {data.get('search_results_count', '?')} products")
    print("=" * 80)


def main():
    """Run demo."""
    print("🚀 OmniSearch Agent Recommendation Demo")
    print("=" * 80)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Server not responding. Start with: python main.py")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server at {BASE_URL}")
        print("   Start with: python main.py")
        return
    
    # Example 1: Text query recommendations
    user_id = "demo_user_001"
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Text Query Recommendations")
    print("=" * 80)
    
    data = recommend_text(user_id, "blue casual shirt", top_k=5)
    if data:
        print_recommendations(data)
    
    # Example 2: Different query
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Different Query")
    print("=" * 80)
    
    data = recommend_text(user_id, "formal business attire", top_k=5)
    if data:
        print_recommendations(data)
    
    # Example 3: Image recommendations (if image exists)
    # Uncomment if you have a test image:
    # data = recommend_image(user_id, "/path/to/image.jpg", top_k=5)
    # if data:
    #     print_recommendations(data)
    
    print("\n✨ Demo complete!")
    print("\n💡 Try these in your app:")
    print("   • POST /agent/recommend with different queries")
    print("   • Upload images for visual recommendations")
    print("   • Adjust top_k and weights for different results")


if __name__ == "__main__":
    main()
