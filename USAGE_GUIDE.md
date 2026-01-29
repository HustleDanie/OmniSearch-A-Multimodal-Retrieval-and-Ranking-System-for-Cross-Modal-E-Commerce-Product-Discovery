# OmniSearch Usage Guide 🚀

Complete guide to using **OmniSearch: A Multimodal Retrieval and Ranking System for Cross-Modal E-Commerce Product Discovery**

---

## Quick Start

### 1️⃣ Start the System

```powershell
# Start all services (FastAPI, Weaviate, MongoDB)
docker-compose up -d

# Check services are running
docker-compose ps

# View logs
docker-compose logs -f fastapi
```

**Services:**
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Weaviate**: http://localhost:8080
- **MongoDB**: localhost:27017

### 2️⃣ Check Health

```bash
curl http://localhost:8000/search/health
```

**Response:**
```json
{
  "status": "healthy",
  "clip_loaded": true,
  "weaviate_connected": true
}
```

---

## 📚 API Endpoints Overview

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/search/text` | POST | Search products using text |
| `/search/image` | POST | Search products using an image |
| `/search/multimodal` | POST | Search using both text AND image |
| `/agent/recommend` | POST | Get AI-powered personalized recommendations |
| `/search/health` | GET | Check system health |
| `/ab/assign` | POST | Get A/B test variant assignment |
| `/ab/metrics` | GET | View A/B test metrics |

---

## 🔍 Search Methods

### Method 1: Text Search

Find products using natural language.

**PowerShell:**
```powershell
$body = @{
    query = "red dress with floral pattern"
    top_k = 10
    category = "dresses"
    color = "red"
    debug = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/search/text" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

**Python:**
```python
import requests

response = requests.post("http://localhost:8000/search/text", json={
    "query": "red dress with floral pattern",
    "top_k": 10,
    "category": "dresses",  # Optional filter
    "color": "red",         # Optional filter
    "debug": False          # Set to True for scoring breakdown
})

results = response.json()
print(f"Found {results['total_results']} products")

for product in results['results']:
    print(f"- {product['title']}")
    print(f"  Similarity: {product['similarity']:.3f}")
    print(f"  Category: {product['category']}, Color: {product['color']}")
```

**cURL:**
```bash
curl -X POST "http://localhost:8000/search/text" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "red dress with floral pattern",
    "top_k": 10,
    "category": "dresses",
    "color": "red"
  }'
```

**Response:**
```json
{
  "query": "red dress with floral pattern",
  "results": [
    {
      "product_id": "P12345",
      "title": "Floral Summer Dress - Red",
      "description": "Beautiful red dress with white floral pattern",
      "color": "red",
      "category": "dresses",
      "image_path": "/images/dress_12345.jpg",
      "similarity": 0.892,
      "distance": 0.108,
      "debug_scores": null
    }
  ],
  "total_results": 10
}
```

---

### Method 2: Image Search

Find products similar to an uploaded image.

**PowerShell:**
```powershell
# Upload an image file
$imagePath = "C:\path\to\your\image.jpg"

$form = @{
    file = Get-Item -Path $imagePath
}

Invoke-RestMethod -Uri "http://localhost:8000/search/image?top_k=10&category=dresses" `
    -Method POST `
    -Form $form
```

**Python:**
```python
import requests

# Open image file
with open("my_dress_photo.jpg", "rb") as image_file:
    files = {"file": ("dress.jpg", image_file, "image/jpeg")}
    params = {
        "top_k": 10,
        "category": "dresses",  # Optional
        "color": "red",         # Optional
        "debug": False
    }
    
    response = requests.post(
        "http://localhost:8000/search/image",
        files=files,
        params=params
    )

results = response.json()
print(f"Found {results['total_results']} similar products")
```

**cURL:**
```bash
curl -X POST "http://localhost:8000/search/image?top_k=10" \
  -F "file=@/path/to/image.jpg" \
  -F "category=dresses"
```

**Response:**
```json
{
  "filename": "dress.jpg",
  "results": [
    {
      "product_id": "P67890",
      "title": "Summer Floral Midi Dress",
      "similarity": 0.935,
      "distance": 0.065,
      "category": "dresses",
      "color": "red"
    }
  ],
  "total_results": 10
}
```

---

### Method 3: Multimodal Search 🌟

**Most powerful**: Combine text AND image for best results.

**PowerShell:**
```powershell
$imagePath = "C:\path\to\dress.jpg"

$form = @{
    file = Get-Item -Path $imagePath
    text = "elegant evening dress"
    image_weight = 0.6  # 60% image, 40% text
    text_weight = 0.4
}

Invoke-RestMethod -Uri "http://localhost:8000/search/multimodal?top_k=10" `
    -Method POST `
    -Form $form
```

**Python:**
```python
import requests

with open("elegant_dress.jpg", "rb") as image_file:
    files = {"file": ("dress.jpg", image_file, "image/jpeg")}
    data = {
        "text": "elegant evening dress",
        "image_weight": 0.6,  # Adjust weights
        "text_weight": 0.4
    }
    params = {"top_k": 10}
    
    response = requests.post(
        "http://localhost:8000/search/multimodal",
        files=files,
        data=data,
        params=params
    )

results = response.json()
```

**Use Cases:**
- **Image + Text**: "Show me dresses like this photo but in blue"
- **Text Only**: Falls back to text search
- **Image Only**: Falls back to image search

---

### Method 4: AI Personal Shopper 🤖

Get personalized recommendations with explanations.

**Python:**
```python
import requests

with open("style_inspiration.jpg", "rb") as image_file:
    files = {"image": ("style.jpg", image_file, "image/jpeg")}
    data = {
        "user_id": "user_12345",
        "query": "casual summer outfit",
        "top_k": 5,
        "image_weight": 0.6,
        "text_weight": 0.4
    }
    
    response = requests.post(
        "http://localhost:8000/agent/recommend",
        files=files,
        data=data
    )

recommendations = response.json()
for rec in recommendations["recommendations"]:
    print(f"\n{rec['title']}")
    print(f"Why: {rec['explanation']}")
    print(f"Wildcard: {rec['is_wildcard']}")
```

**Response:**
```json
{
  "user_id": "user_12345",
  "query": "casual summer outfit",
  "recommendations": [
    {
      "title": "Linen Summer Dress - White",
      "product_id": "P11111",
      "explanation": "Perfect for casual summer wear. Lightweight linen fabric keeps you cool. Matches your preference for comfortable styles.",
      "is_wildcard": false,
      "product_link": "/products/P11111"
    },
    {
      "title": "Bohemian Maxi Skirt",
      "product_id": "P22222",
      "explanation": "Stepping outside your usual style - this bohemian piece could add variety to your wardrobe!",
      "is_wildcard": true,
      "product_link": "/products/P22222"
    }
  ],
  "total_recommendations": 4
}
```

---

## 🧪 A/B Testing

### Assign User to Experiment

```python
import requests

response = requests.post("http://localhost:8000/ab/assign", json={
    "user_id": "user_12345"
})

assignment = response.json()
print(f"User assigned to: {assignment['variant']}")
# Output: "search_v1" or "search_v2"
```

### Search with A/B Variant

```python
# Use A/B testing endpoint
response = requests.post("http://localhost:8000/search-ab/text", json={
    "user_id": "user_12345",
    "query": "blue sneakers",
    "top_k": 10
})

results = response.json()
print(f"Variant: {results['variant']}")
print(f"Results: {len(results['results'])}")
```

### View A/B Metrics

```python
response = requests.get("http://localhost:8000/ab/metrics")
metrics = response.json()

for variant, data in metrics.items():
    print(f"\n{variant}:")
    print(f"  Searches: {data['search_count']}")
    print(f"  Clicks: {data['click_count']}")
    print(f"  CTR: {data['ctr']:.2%}")
```

---

## 🐍 Complete Python Example

```python
import requests
from pathlib import Path

class OmniSearchClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def text_search(self, query, top_k=10, category=None, color=None):
        """Search by text query."""
        response = requests.post(f"{self.base_url}/search/text", json={
            "query": query,
            "top_k": top_k,
            "category": category,
            "color": color
        })
        return response.json()
    
    def image_search(self, image_path, top_k=10, category=None):
        """Search by image file."""
        with open(image_path, "rb") as f:
            files = {"file": (Path(image_path).name, f, "image/jpeg")}
            params = {"top_k": top_k, "category": category}
            response = requests.post(
                f"{self.base_url}/search/image",
                files=files,
                params=params
            )
        return response.json()
    
    def multimodal_search(self, text=None, image_path=None, 
                         image_weight=0.6, text_weight=0.4, top_k=10):
        """Search with both text and image."""
        if not text and not image_path:
            raise ValueError("Provide at least text or image_path")
        
        files = {}
        data = {"image_weight": image_weight, "text_weight": text_weight}
        
        if text:
            data["text"] = text
        
        if image_path:
            files["file"] = open(image_path, "rb")
        
        try:
            response = requests.post(
                f"{self.base_url}/search/multimodal",
                files=files if files else None,
                data=data,
                params={"top_k": top_k}
            )
            return response.json()
        finally:
            for f in files.values():
                f.close()
    
    def get_recommendations(self, user_id, query=None, image_path=None, top_k=5):
        """Get AI-powered recommendations."""
        files = {}
        data = {"user_id": user_id, "top_k": top_k}
        
        if query:
            data["query"] = query
        
        if image_path:
            files["image"] = open(image_path, "rb")
        
        try:
            response = requests.post(
                f"{self.base_url}/agent/recommend",
                files=files if files else None,
                data=data
            )
            return response.json()
        finally:
            for f in files.values():
                f.close()


# Usage Example
if __name__ == "__main__":
    client = OmniSearchClient()
    
    # 1. Text search
    print("=== Text Search ===")
    results = client.text_search("red summer dress", top_k=5)
    for product in results["results"][:3]:
        print(f"- {product['title']} (similarity: {product['similarity']:.3f})")
    
    # 2. Image search
    print("\n=== Image Search ===")
    results = client.image_search("my_dress.jpg", top_k=5)
    print(f"Found {results['total_results']} similar products")
    
    # 3. Multimodal search
    print("\n=== Multimodal Search ===")
    results = client.multimodal_search(
        text="elegant evening dress",
        image_path="inspiration.jpg",
        image_weight=0.7,
        text_weight=0.3
    )
    
    # 4. AI recommendations
    print("\n=== AI Recommendations ===")
    recs = client.get_recommendations(
        user_id="user_123",
        query="casual summer outfit",
        image_path="style_inspo.jpg"
    )
    for rec in recs["recommendations"]:
        print(f"\n{rec['title']}")
        print(f"  → {rec['explanation']}")
```

---

## 🌐 Interactive API Documentation

**Best way to test the API!**

1. Open browser: http://localhost:8000/docs
2. Click any endpoint to expand
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"
6. See response instantly

**Features:**
- ✅ Interactive forms for all endpoints
- ✅ File upload testing
- ✅ Response schema documentation
- ✅ Example responses
- ✅ Authentication testing (when enabled)

---

## 💡 Usage Tips

### 🎯 Search Quality

**For best results:**
- **Text**: Use natural, descriptive queries ("flowy summer dress with floral print")
- **Image**: Use clear, well-lit product photos
- **Multimodal**: Combine both for precision ("dress like this but in blue")

**Weight tuning:**
```python
# More image influence (similar visual style)
image_weight=0.8, text_weight=0.2

# More text influence (specific attributes)
image_weight=0.4, text_weight=0.6

# Balanced (default)
image_weight=0.6, text_weight=0.4
```

### 🔍 Filtering

Combine search with filters for precise results:
```python
response = client.text_search(
    query="summer dress",
    category="dresses",     # Only dresses
    color="red",           # Only red items
    top_k=20
)
```

### 🐛 Debug Mode

Enable debug scoring to understand results:
```python
response = requests.post("http://localhost:8000/search/text", json={
    "query": "blue sneakers",
    "top_k": 5,
    "debug": True  # ⭐ Enable debug
})

for product in response.json()["results"]:
    print(product["debug_scores"])
    # Shows: vector_similarity, text_similarity, color_match, category_match
```

### ⚡ Performance

**Batch searches** for better throughput:
```python
queries = ["red dress", "blue jeans", "white sneakers"]

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [
        executor.submit(client.text_search, query, top_k=10)
        for query in queries
    ]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]
```

---

## 🛠️ Troubleshooting

### Service Not Starting

```powershell
# Check service status
docker-compose ps

# View logs
docker-compose logs fastapi
docker-compose logs weaviate

# Restart services
docker-compose restart

# Full rebuild
docker-compose down
docker-compose up --build -d
```

### Connection Refused

**Issue**: `Connection refused on localhost:8000`

**Solution**:
```powershell
# Check if port is in use
netstat -ano | findstr :8000

# Wait for services to be healthy
docker-compose ps

# Check health endpoint
curl http://localhost:8000/search/health
```

### Slow Search Performance

**Causes**:
- First search loads CLIP model (takes 5-10 seconds)
- Large images (resize to < 1MB)
- High top_k values

**Solutions**:
```python
# 1. Warm up the model first
requests.post("http://localhost:8000/search/text", json={
    "query": "test", "top_k": 1
})

# 2. Reduce image size
from PIL import Image
img = Image.open("large_image.jpg")
img.thumbnail((800, 800))
img.save("optimized.jpg", quality=85)

# 3. Use reasonable top_k
top_k = 20  # Don't request 1000 results
```

### Empty Results

**Possible causes**:
1. **No products indexed** → Run `python scripts/generate_embeddings.py`
2. **Filters too strict** → Remove category/color filters
3. **Weaviate not ready** → Check `/search/health`

---

## 📊 Monitoring

### Check System Health

```python
import requests
import time

def monitor_health():
    while True:
        response = requests.get("http://localhost:8000/search/health")
        health = response.json()
        
        status = "🟢" if health["status"] == "healthy" else "🔴"
        print(f"{status} Status: {health['status']}")
        print(f"  CLIP: {'✓' if health['clip_loaded'] else '✗'}")
        print(f"  Weaviate: {'✓' if health['weaviate_connected'] else '✗'}")
        
        time.sleep(30)  # Check every 30 seconds

monitor_health()
```

### Track Search Latency

```python
import time
import statistics

latencies = []

for i in range(10):
    start = time.time()
    client.text_search("test query", top_k=10)
    latency = time.time() - start
    latencies.append(latency)
    print(f"Request {i+1}: {latency:.3f}s")

print(f"\nAverage: {statistics.mean(latencies):.3f}s")
print(f"P95: {statistics.quantiles(latencies, n=20)[18]:.3f}s")
```

---

## 🚀 Next Steps

1. **Load Sample Data**: `python scripts/generate_embeddings.py`
2. **Try Interactive Docs**: http://localhost:8000/docs
3. **Run Example Searches**: Use the Python client above
4. **Test A/B Framework**: Create experiments
5. **Monitor Performance**: Set up health checks

**Need Help?**
- 📖 Full docs: `docs/` folder
- 🔧 System validation: `SYSTEM_VALIDATION_REPORT.md`
- 🧪 Experimentation: `docs/EXPERIMENTATION_SYSTEM.md`
- 📈 Scalability: `docs/SCALABILITY_STRATEGY.md`

---

**Happy Searching! 🔎✨**
