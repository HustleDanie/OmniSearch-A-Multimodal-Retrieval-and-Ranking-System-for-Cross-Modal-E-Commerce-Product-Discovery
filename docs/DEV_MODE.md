# Dev Mode Configuration

## Overview

Dev mode allows the API to work without external LLM API calls by using mocked responses. This is useful for:
- Testing without API keys
- Local development without internet
- CI/CD pipelines
- Cost-free demos

## How to Enable

### Option 1: Environment Variable

Set `DEV_MODE=true` in your environment:

**Linux/Mac:**
```bash
export DEV_MODE=true
python main.py
```

**Windows PowerShell:**
```powershell
$env:DEV_MODE="true"
python main.py
```

**Windows CMD:**
```cmd
set DEV_MODE=true
python main.py
```

### Option 2: .env File

Add to your `.env` file:
```env
DEV_MODE=true
```

Then run normally:
```bash
python main.py
```

## What Gets Mocked

When `DEV_MODE=true`:

1. **LLM Client** - Returns predefined mock recommendations
2. **No API Calls** - OpenAI/external APIs are not called
3. **Instant Responses** - No network latency
4. **No API Keys Required** - Works without `OPENAI_API_KEY`

## Mock Response Format

The mock LLM returns this JSON structure:

```json
{
  "recommendations": [
    {
      "title": "Blue Casual Shirt",
      "why": "Matches your preference for casual blue apparel",
      "is_wildcard": false
    },
    {
      "title": "Black Formal Blazer",
      "why": "Complements your style with professional pieces",
      "is_wildcard": false
    },
    {
      "title": "Navy Chinos",
      "why": "Versatile neutral piece that works with multiple styles",
      "is_wildcard": false
    },
    {
      "title": "Vintage Denim Jacket",
      "why": "A wildcard piece that adds character to your wardrobe",
      "is_wildcard": true
    }
  ]
}
```

## Testing Dev Mode

### Test 1: Direct LLM Client

```python
import os
os.environ["DEV_MODE"] = "true"

from services.llm_client import get_llm_client, reset_llm_client

# Reset to pick up new environment
reset_llm_client()

# Get client
client = get_llm_client()
print(f"Provider: {client.provider}")  # Should be "mock"

# Generate response
response = client.generate("recommend products")
print(response)  # Mock JSON response
```

### Test 2: Run Test Script

```bash
python scripts/test_dev_mode.py
```

Expected output:
```
============================================================
Testing Dev Mode with Mocked LLM Responses
============================================================

1. DEV_MODE setting: True
Dev mode enabled: Using mock LLM responses (no external API calls)
2. LLM Provider: mock
3. LLM Model: gpt-3.5-turbo

4. Generating mock recommendation...

5. Response received (478 chars)
...

✓ SUCCESS: Dev mode is working correctly!
  - No external API calls made
  - Mock responses returned instantly
```

### Test 3: API Endpoint

With dev mode enabled, the `/agent/recommend` endpoint will:
1. Accept requests normally
2. Perform multimodal search (still real)
3. Use mocked LLM recommendations
4. Return properly formatted response

```bash
# Start server with dev mode
DEV_MODE=true uvicorn main:app --reload

# Test endpoint
curl -X POST "http://localhost:8000/agent/recommend" \
  -F "user_id=test_user" \
  -F "query=casual shirts"
```

## Production vs Dev Mode

| Feature | Production | Dev Mode |
|---------|-----------|----------|
| LLM API Calls | Real (OpenAI) | Mocked |
| API Key Required | Yes | No |
| Response Time | ~1-3s | Instant |
| Cost | Per request | Free |
| Recommendations | AI-generated | Predefined |
| Search | Real vector search | Real vector search |
| Database | Real MongoDB | Real MongoDB |

## Environment Variables Summary

```env
# Required for production
OPENAI_API_KEY=sk-...

# Enable dev mode (optional)
DEV_MODE=true

# Other settings
DEBUG=false
LOG_LEVEL=INFO
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=omnisearch
WEAVIATE_URL=http://localhost:8080
```

## Implementation Details

### Settings (config/settings.py)

```python
class Settings:
    DEV_MODE: bool = os.getenv("DEV_MODE", "False").lower() == "true"
    # ... other settings
```

### LLM Client (services/llm_client.py)

```python
def _initialize_client(self):
    # Check if dev mode is enabled
    if settings.DEV_MODE:
        print("Dev mode enabled: Using mock LLM responses")
        self.provider = "mock"
        self.client = None
        return
    # ... normal initialization
```

## When to Use Dev Mode

✅ **Use dev mode for:**
- Local development
- Running tests
- CI/CD pipelines
- Demos without API costs
- Development without internet

❌ **Don't use dev mode for:**
- Production deployments
- Real user recommendations
- Quality/accuracy testing
- Performance benchmarking

## Customizing Mock Responses

To customize the mock response, edit `services/llm_client.py`:

```python
def _mock_response(self, prompt: str) -> str:
    """Generate a mock response for testing/demo."""
    return (
        '{"recommendations": ['
        '{"title": "Your Product", "why": "Your reason", "is_wildcard": false},'
        # ... add more recommendations
        "]}"
    )
```

## Troubleshooting

### Dev mode not activating?

1. Check environment variable is set:
   ```bash
   echo $DEV_MODE  # Linux/Mac
   echo %DEV_MODE%  # Windows CMD
   $env:DEV_MODE   # Windows PowerShell
   ```

2. Verify in code:
   ```python
   from config.settings import settings
   print(settings.DEV_MODE)
   ```

3. Reset LLM client if already initialized:
   ```python
   from services.llm_client import reset_llm_client
   reset_llm_client()
   ```

### Still seeing "OPENAI_API_KEY not set" warning?

This is normal! The warning appears before dev mode check. If you see "Dev mode enabled" message after, it's working correctly.

### Mock response format incorrect?

The mock response must be valid JSON matching the expected schema. Check `services/llm_client.py` `_mock_response()` method.
