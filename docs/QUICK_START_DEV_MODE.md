# Quick Start with Dev Mode

This guide shows you how to quickly test the omnisearch API using dev mode (no API keys needed).

## Prerequisites

- Python 3.8+
- MongoDB running (or use mocked database)
- No OpenAI API key needed!

## Step 1: Set Dev Mode

```bash
# Linux/Mac
export DEV_MODE=true

# Windows PowerShell
$env:DEV_MODE="true"

# Or add to .env file
echo "DEV_MODE=true" >> .env
```

## Step 2: Start the Server

```bash
# Install dependencies if needed
pip install -r requirements.txt

# Start server
uvicorn main:app --reload
```

You should see:
```
Dev mode enabled: Using mock LLM responses (no external API calls)
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## Step 3: Test the Endpoint

### Using cURL

```bash
curl -X POST "http://localhost:8000/agent/recommend" \
  -F "user_id=demo_user" \
  -F "query=casual blue shirts"
```

### Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/agent/recommend",
    data={
        "user_id": "demo_user",
        "query": "casual blue shirts"
    }
)

print(response.json())
```

### Using the API Docs

1. Open browser to http://localhost:8000/docs
2. Find `/agent/recommend` endpoint
3. Click "Try it out"
4. Fill in:
   - user_id: `demo_user`
   - query: `casual shirts`
5. Click "Execute"

## Expected Response

```json
{
  "recommendations": [
    {
      "title": "Blue Casual Shirt",
      "why": "Matches your preference for casual blue apparel",
      "product_links": [...],
      "is_wildcard": false
    },
    {
      "title": "Black Formal Blazer",
      "why": "Complements your style with professional pieces",
      "product_links": [...],
      "is_wildcard": false
    },
    {
      "title": "Navy Chinos",
      "why": "Versatile neutral piece that works with multiple styles",
      "product_links": [...],
      "is_wildcard": false
    },
    {
      "title": "Vintage Denim Jacket",
      "why": "A wildcard piece that adds character to your wardrobe",
      "product_links": [...],
      "is_wildcard": true
    }
  ],
  "message": "Here are some recommendations based on your preferences",
  "metadata": {
    "total_results": 4,
    "personalized_count": 3,
    "wildcard_count": 1
  }
}
```

## What's Happening?

In dev mode:

✅ **Mocked:** LLM recommendations (instant, free)
✅ **Real:** Vector search (if database configured)
✅ **Real:** Product matching and linking
✅ **Real:** User profile retrieval

## Next Steps

### 1. Test User Memory Updates

```python
from db.user_service import UserProfileService

service = UserProfileService()

# Simulate a purchase
product = {
    "title": "Blue Casual Shirt",
    "price": 29.99,
    "color": "blue",
    "category": "shirts"
}

updated_profile = service.update_user_memory("demo_user", product)
print(updated_profile)
```

### 2. Switch to Production Mode

When ready for real AI recommendations:

```bash
# Add your OpenAI API key
export OPENAI_API_KEY=sk-...
export DEV_MODE=false

# Restart server
uvicorn main:app --reload
```

### 3. Run Tests

```bash
# Test dev mode
python scripts/test_dev_mode.py

# Test endpoint
pytest tests/test_agent_endpoint.py -v

# Test user memory
pytest tests/test_update_user_memory.py -v
```

## Troubleshooting

### Issue: "OPENAI_API_KEY not set" warning

**Solution:** This is normal in dev mode! You'll see:
```
Warning: OPENAI_API_KEY not set. Using mock client.
Dev mode enabled: Using mock LLM responses (no external API calls)
```

The second line confirms dev mode is working.

### Issue: Import errors (torch, etc.)

**Solution:** Some dependencies are optional for dev mode:
```bash
# Minimal install for dev mode
pip install fastapi uvicorn python-dotenv pymongo pydantic
```

### Issue: MongoDB connection error

**Solution:** Mock the database or use a test database:
```bash
# Use test database
export MONGO_DB_NAME=omnisearch_test

# Or start local MongoDB
docker run -d -p 27017:27017 mongo
```

## Benefits of Dev Mode

| Benefit | Description |
|---------|-------------|
| 🚀 Fast | Instant responses, no API latency |
| 💰 Free | No API costs |
| 🔌 Offline | Works without internet |
| 🧪 Testing | Perfect for CI/CD |
| 🎯 Predictable | Same mock responses every time |

## Limitations

- Mock recommendations are not personalized
- Always returns same 4 products
- No actual AI reasoning

For production use, disable dev mode and use real LLM API.
