"""
Test script for debug scoring functionality in search endpoints.
"""
import requests
import json

BASE_URL = "http://localhost:8000/search"

def test_text_search_with_debug():
    """Test text search with debug=true"""
    print("=" * 60)
    print("Testing Text Search with Debug Mode")
    print("=" * 60)
    
    payload = {
        "query": "blue dress",
        "top_k": 3,
        "debug": True
    }
    
    response = requests.post(f"{BASE_URL}/text", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['total_results']} results\n")
        
        for i, result in enumerate(data['results'], 1):
            print(f"Result {i}: {result['title']}")
            print(f"  Category: {result['category']}, Color: {result['color']}")
            print(f"  Similarity: {result['similarity']:.4f}")
            
            if result.get('debug_scores'):
                debug = result['debug_scores']
                print(f"  Debug Scores:")
                print(f"    Vector Score:   {debug.get('vector_score', 0):.4f}")
                print(f"    Color Score:    {debug.get('color_score', 0):.4f}")
                print(f"    Category Score: {debug.get('category_score', 0):.4f}")
                print(f"    Text Score:     {debug.get('text_score', 0):.4f}")
                print(f"    Final Score:    {debug.get('final_score', 0):.4f}")
            else:
                print("  ⚠ No debug scores returned!")
            print()
    else:
        print(f"✗ Request failed: {response.status_code}")
        print(response.text)


def test_text_search_without_debug():
    """Test text search with debug=false (default)"""
    print("=" * 60)
    print("Testing Text Search WITHOUT Debug Mode")
    print("=" * 60)
    
    payload = {
        "query": "red shoes",
        "top_k": 2,
        "debug": False
    }
    
    response = requests.post(f"{BASE_URL}/text", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['total_results']} results\n")
        
        for i, result in enumerate(data['results'], 1):
            print(f"Result {i}: {result['title']}")
            print(f"  Similarity: {result['similarity']:.4f}")
            
            if result.get('debug_scores'):
                print("  ⚠ Unexpected: debug_scores present when debug=false")
            else:
                print("  ✓ No debug scores (as expected)")
            print()
    else:
        print(f"✗ Request failed: {response.status_code}")
        print(response.text)


def test_image_search_with_debug():
    """Test image search with debug=true"""
    print("=" * 60)
    print("Testing Image Search with Debug Mode")
    print("=" * 60)
    print("Note: Requires a test image file. Skipping for now.")
    print("To test manually, use:")
    print('  curl -X POST "http://localhost:8000/search/image?top_k=3&debug=true" \\')
    print('       -F "file=@path/to/image.jpg"')
    print()


def test_multimodal_search_with_debug():
    """Test multimodal search with debug=true"""
    print("=" * 60)
    print("Testing Multimodal Search with Debug Mode")
    print("=" * 60)
    print("Note: Testing text-only multimodal search with debug")
    
    data = {
        "text": "elegant evening gown",
        "top_k": 3,
        "debug": "true"  # Query param as string
    }
    
    response = requests.post(f"{BASE_URL}/multimodal?debug=true", data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Found {result['total_results']} results\n")
        
        for i, item in enumerate(result['results'], 1):
            print(f"Result {i}: {item['title']}")
            print(f"  Similarity: {item['similarity']:.4f}")
            
            if item.get('debug_scores'):
                debug = item['debug_scores']
                print(f"  Debug Scores:")
                print(f"    Vector Score:   {debug.get('vector_score', 0):.4f}")
                print(f"    Color Score:    {debug.get('color_score', 0):.4f}")
                print(f"    Category Score: {debug.get('category_score', 0):.4f}")
                print(f"    Text Score:     {debug.get('text_score', 0):.4f}")
                print(f"    Final Score:    {debug.get('final_score', 0):.4f}")
            else:
                print("  ⚠ No debug scores returned!")
            print()
    else:
        print(f"✗ Request failed: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    print("\n🔍 Debug Scoring Test Suite\n")
    
    try:
        # Test health endpoint first
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code == 200:
            print("✓ Server is running\n")
        else:
            print("⚠ Server responded but health check failed\n")
    except requests.exceptions.RequestException:
        print("✗ Cannot connect to server. Start it with: uvicorn main:app --reload\n")
        exit(1)
    
    # Run tests
    test_text_search_with_debug()
    test_text_search_without_debug()
    test_multimodal_search_with_debug()
    test_image_search_with_debug()
    
    print("=" * 60)
    print("Test suite complete!")
    print("=" * 60)
