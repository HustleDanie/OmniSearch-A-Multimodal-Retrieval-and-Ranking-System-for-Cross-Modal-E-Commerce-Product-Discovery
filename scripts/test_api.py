"""
Example usage of the OmniSearch API using requests library.
"""
import requests
import json


API_BASE_URL = "http://localhost:8000"


def test_text_search():
    """Test text search endpoint."""
    print("=" * 80)
    print("Testing POST /search/text")
    print("=" * 80)
    
    # Prepare request
    payload = {
        "query": "red athletic shoes",
        "top_k": 5,
        "category": None,
        "color": None
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    # Make request
    response = requests.post(
        f"{API_BASE_URL}/search/text",
        json=payload
    )
    
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nFound {data['total_results']} results:\n")
        
        for i, result in enumerate(data['results'], 1):
            print(f"{i}. {result['title']}")
            print(f"   Category: {result['category']} | Color: {result['color']}")
            print(f"   Similarity: {result['similarity']:.4f}")
            print()
    else:
        print(f"\nError: {response.text}")


def test_text_search_with_filters():
    """Test text search with filters."""
    print("\n" + "=" * 80)
    print("Testing POST /search/text with filters")
    print("=" * 80)
    
    payload = {
        "query": "comfortable clothing",
        "top_k": 3,
        "category": "apparel"
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{API_BASE_URL}/search/text",
        json=payload
    )
    
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nFound {data['total_results']} results")
        print(json.dumps(data, indent=2))


def test_image_search():
    """Test image search endpoint."""
    print("\n" + "=" * 80)
    print("Testing POST /search/image")
    print("=" * 80)
    
    # Path to test image
    image_path = "path/to/test/image.jpg"
    
    print(f"\nUploading image: {image_path}")
    
    try:
        with open(image_path, "rb") as f:
            files = {"file": (image_path, f, "image/jpeg")}
            params = {"top_k": 5}
            
            response = requests.post(
                f"{API_BASE_URL}/search/image",
                files=files,
                params=params
            )
        
        print(f"\nResponse status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nFound {data['total_results']} results for '{data['filename']}':\n")
            
            for i, result in enumerate(data['results'], 1):
                print(f"{i}. {result['title']}")
                print(f"   Similarity: {result['similarity']:.4f}")
                print()
        else:
            print(f"\nError: {response.text}")
            
    except FileNotFoundError:
        print(f"\nImage file not found: {image_path}")
        print("\nExample: Upload an image file to search for similar products")
        print("  with open('query_image.jpg', 'rb') as f:")
        print("      files = {'file': ('image.jpg', f, 'image/jpeg')}")
        print("      response = requests.post(f'{API_BASE_URL}/search/image', files=files)")


def test_multimodal_text_only():
    """Test multimodal endpoint with text-only payload."""
    print("\n" + "=" * 80)
    print("Testing POST /search/multimodal (text-only)")
    print("=" * 80)
    
    data = {
        "text": "blue denim jacket",
        "top_k": 5,
        "image_weight": 0.6,
        "text_weight": 0.4
    }
    
    response = requests.post(
        f"{API_BASE_URL}/search/multimodal",
        data=data
    )
    
    print(f"\nResponse status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"\nQuery text: {data.get('text')}")
        print(f"Results: {data['total_results']}\n")
        for i, result in enumerate(data['results'], 1):
            print(f"{i}. {result['title']} (similarity: {result['similarity']:.4f})")
    else:
        print(f"\nError: {response.text}")


def test_multimodal_with_image():
    """Test multimodal endpoint with image + text (requires real image)."""
    print("\n" + "=" * 80)
    print("Testing POST /search/multimodal (image + optional text)")
    print("=" * 80)
    
    image_path = "path/to/test/image.jpg"
    
    try:
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f, "image/jpeg")}
            data = {"text": "blue jacket", "top_k": 5}
            response = requests.post(
                f"{API_BASE_URL}/search/multimodal",
                files=files,
                data=data
            )
        
        print(f"\nResponse status: {response.status_code}")
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"\nError: {response.text}")
    except FileNotFoundError:
        print(f"\nImage file not found: {image_path}")
        print("Provide an image to test combined multimodal search.")


def test_health():
    """Test health check endpoint."""
    print("\n" + "=" * 80)
    print("Testing GET /search/health")
    print("=" * 80)
    
    response = requests.get(f"{API_BASE_URL}/search/health")
    
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nHealth status:")
        print(json.dumps(data, indent=2))
    else:
        print(f"\nError: {response.text}")


def test_root():
    """Test root endpoint."""
    print("\n" + "=" * 80)
    print("Testing GET /")
    print("=" * 80)
    
    response = requests.get(f"{API_BASE_URL}/")
    
    print(f"\nResponse status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    print("\n🔍 OmniSearch API Test Suite\n")
    print(f"API Base URL: {API_BASE_URL}\n")
    
    try:
        # Test all endpoints
        test_root()
        test_health()
        test_text_search()
        test_text_search_with_filters()
        test_image_search()
        test_multimodal_text_only()
        test_multimodal_with_image()
        
        print("\n" + "=" * 80)
        print("✓ All tests completed!")
        print("=" * 80)
        print("\nView API documentation at:")
        print(f"  Swagger UI: {API_BASE_URL}/docs")
        print(f"  ReDoc: {API_BASE_URL}/redoc")
        
    except requests.exceptions.ConnectionError:
        print(f"\n✗ Error: Could not connect to API at {API_BASE_URL}")
        print("\nMake sure the API is running:")
        print("  python main.py")
        print("\nOr:")
        print("  uvicorn main:app --reload")
