"""
Simple test script to query the OmniSearch API with a text search.
"""
import requests
import json


def search_products(query: str, top_k: int = 10):
    """
    Send a text search query to the API.
    
    Args:
        query: Text query string
        top_k: Number of results to return
    """
    # API endpoint
    url = "http://localhost:8000/search/text"
    
    # Prepare request payload
    payload = {
        "query": query,
        "top_k": top_k
    }
    
    print(f"Searching for: '{query}'\n")
    print(f"Sending request to {url}...")
    
    try:
        # Send POST request
        response = requests.post(url, json=payload)
        
        # Check response status
        if response.status_code != 200:
            print(f"\n✗ Error: {response.status_code}")
            print(response.text)
            return
        
        # Parse response
        data = response.json()
        
        # Print results
        print(f"\n✓ Found {data['total_results']} products:\n")
        print("=" * 80)
        
        for i, product in enumerate(data['results'], 1):
            print(f"\n{i}. {product['title']}")
            print(f"   Product ID: {product['product_id']}")
            print(f"   Category: {product['category']} | Color: {product['color']}")
            print(f"   Description: {product['description']}")
            print(f"   Similarity Score: {product['similarity']:.4f}")
            print(f"   Image: {product['image_path']}")
        
        print("\n" + "=" * 80)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to API at http://localhost:8000")
        print("\nMake sure the API is running:")
        print("  python main.py")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    # Test query
    query = "blue denim jacket"
    
    # Search for products
    search_products(query, top_k=10)
