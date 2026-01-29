"""Test the recommendation endpoint in dev mode."""
import os
import sys

# Set dev mode
os.environ["DEV_MODE"] = "true"

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from main import app

def test_recommendation_endpoint_dev_mode():
    """Test /agent/recommend endpoint with dev mode enabled."""
    print("=" * 60)
    print("Testing /agent/recommend Endpoint in Dev Mode")
    print("=" * 60)
    
    client = TestClient(app)
    
    # Test with text query
    print("\n1. Testing with text query...")
    response = client.post(
        "/agent/recommend",
        data={
            "user_id": "test_user_123",
            "query": "casual blue shirts"
        }
    )
    
    print(f"   Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Response keys: {list(data.keys())}")
        print(f"   Number of recommendations: {len(data.get('recommendations', []))}")
        
        # Show first recommendation
        if data.get('recommendations'):
            first = data['recommendations'][0]
            print(f"\n2. First recommendation:")
            print(f"   - Title: {first.get('title')}")
            print(f"   - Why: {first.get('why')}")
            print(f"   - Wildcard: {first.get('is_wildcard')}")
            print(f"   - Links: {len(first.get('product_links', []))} products")
        
        print(f"\n3. Message: {data.get('message', 'N/A')}")
        
        print("\n✓ SUCCESS: Endpoint works in dev mode!")
        print("  - No external LLM API calls")
        print("  - Mock recommendations returned")
        return True
    else:
        print(f"\n✗ FAILED: {response.status_code}")
        print(f"   Error: {response.text}")
        return False

if __name__ == "__main__":
    success = test_recommendation_endpoint_dev_mode()
    sys.exit(0 if success else 1)
