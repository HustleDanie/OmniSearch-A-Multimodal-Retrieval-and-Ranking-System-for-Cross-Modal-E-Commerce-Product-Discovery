# Dev Mode Implementation Summary

## What Was Built

Added a **dev mode** configuration that allows the omnisearch API to work without external LLM API calls by using mocked responses.

## Changes Made

### 1. Configuration (config/settings.py)
- Added `DEV_MODE` setting that reads from environment variable
- Default: `false` (production mode)
- Set `DEV_MODE=true` to enable mock responses

```python
DEV_MODE: bool = os.getenv("DEV_MODE", "False").lower() == "true"
```

### 2. LLM Client (services/llm_client.py)
- Updated `_initialize_client()` to check dev mode first
- When `DEV_MODE=true`:
  - Skips OpenAI API initialization
  - Uses mock provider automatically
  - Prints confirmation message
  - Returns predefined JSON recommendations

```python
def _initialize_client(self):
    if settings.DEV_MODE:
        print("Dev mode enabled: Using mock LLM responses (no external API calls)")
        self.provider = "mock"
        self.client = None
        return
    # ... rest of initialization
```

### 3. Mock Response
The mock LLM returns 4 recommendations:
- 3 personalized recommendations (Blue Casual Shirt, Black Formal Blazer, Navy Chinos)
- 1 wildcard recommendation (Vintage Denim Jacket)

All in proper JSON format matching the expected schema.

## Testing

### Created Tests
1. **tests/test_dev_mode.py** (4 tests)
   - ✅ `test_dev_mode_enabled` - Verifies mock provider used
   - ✅ `test_dev_mode_disabled_without_api_key` - Falls back to mock
   - ✅ `test_mock_response_format` - Validates JSON structure
   - ✅ `test_dev_mode_message` - Confirms message printed

2. **scripts/test_dev_mode.py**
   - Interactive test showing dev mode in action
   - Prints configuration, provider, and response
   - Validates mock response content

### Existing Tests
All 7 existing agent endpoint tests continue to pass:
- ✅ Text query recommendations
- ✅ Missing input handling
- ✅ Without LLM client fallback
- ✅ Custom weights
- ✅ Response structure validation
- ✅ Invalid LLM response handling
- ✅ Root endpoint documentation

## Documentation

Created 3 comprehensive guides:

1. **docs/DEV_MODE.md** - Complete reference
   - How to enable (env vars, .env file)
   - What gets mocked
   - Testing procedures
   - Production vs dev comparison
   - Troubleshooting guide

2. **docs/QUICK_START_DEV_MODE.md** - Quick start guide
   - Step-by-step setup
   - Example requests (cURL, Python, API docs)
   - Expected responses
   - Next steps
   - Benefits and limitations

3. **scripts/test_dev_mode.py** - Runnable example
   - Demonstrates dev mode usage
   - Shows configuration
   - Validates responses

## How to Use

### Enable Dev Mode

**Option 1: Environment Variable**
```bash
# Linux/Mac
export DEV_MODE=true

# Windows
$env:DEV_MODE="true"
```

**Option 2: .env File**
```env
DEV_MODE=true
```

### Start Server
```bash
uvicorn main:app --reload
```

You'll see:
```
Dev mode enabled: Using mock LLM responses (no external API calls)
```

### Test Endpoint
```bash
curl -X POST "http://localhost:8000/agent/recommend" \
  -F "user_id=test_user" \
  -F "query=casual shirts"
```

## Benefits

| Benefit | Description |
|---------|-------------|
| 🚀 **Fast** | Instant responses, no network latency |
| 💰 **Free** | No OpenAI API costs |
| 🔌 **Offline** | Works without internet connection |
| 🔑 **No Keys** | No API keys required |
| 🧪 **Testing** | Perfect for CI/CD pipelines |
| 🎯 **Predictable** | Consistent responses for tests |

## Use Cases

✅ **Perfect for:**
- Local development
- Automated testing
- CI/CD pipelines
- Demos without API costs
- Development without internet
- Learning/experimenting with the API

❌ **Not suitable for:**
- Production deployments
- Real user recommendations
- Quality/accuracy testing
- Performance benchmarking

## Implementation Details

### Flow

```
Request → API Endpoint → PersonalShopperAgent
                              ↓
                        Check DEV_MODE
                              ↓
          ┌─────────────────┴─────────────────┐
          ↓                                   ↓
    DEV_MODE=true                      DEV_MODE=false
    Use mock LLM                       Use OpenAI API
    (instant)                          (requires key)
          ↓                                   ↓
          └─────────────────┬─────────────────┘
                            ↓
                    Format Response
                            ↓
                    Return to Client
```

### Configuration Priority

1. **DEV_MODE=true** → Always use mock
2. **DEV_MODE=false + No API key** → Fallback to mock with warning
3. **DEV_MODE=false + Valid API key** → Use OpenAI API

## Files Modified

| File | Changes | Lines |
|------|---------|-------|
| config/settings.py | Added DEV_MODE setting | +1 |
| services/llm_client.py | Check dev mode first | +8 |

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| tests/test_dev_mode.py | Unit tests | 100 |
| scripts/test_dev_mode.py | Interactive demo | 60 |
| docs/DEV_MODE.md | Complete reference | 200+ |
| docs/QUICK_START_DEV_MODE.md | Quick start guide | 150+ |
| docs/DEV_MODE_SUMMARY.md | This file | 150+ |

## Test Results

```
tests/test_dev_mode.py::test_dev_mode_enabled PASSED
tests/test_dev_mode.py::test_dev_mode_disabled_without_api_key PASSED
tests/test_dev_mode.py::test_mock_response_format PASSED
tests/test_dev_mode.py::test_dev_mode_message PASSED

4 passed in 1.99s ✅
```

```
tests/test_agent_endpoint.py (all existing tests)
7 passed in 0.73s ✅
```

## Validation

✅ Dev mode can be enabled via environment variable
✅ Dev mode uses mock provider automatically
✅ Mock responses are valid JSON
✅ Mock responses match expected schema
✅ Configuration message is printed
✅ All existing tests still pass
✅ No breaking changes to existing functionality
✅ Documentation is complete

## Future Enhancements

Possible improvements:
- [ ] Multiple mock response templates
- [ ] Configurable mock responses via file
- [ ] Mock response randomization
- [ ] Dev mode for other services (search, etc.)
- [ ] Mock response based on query keywords
- [ ] Dev mode metrics/logging

## Maintenance Notes

- Mock response is defined in `services/llm_client.py` `_mock_response()` method
- To customize mock data, edit this method
- Ensure mock JSON matches Pydantic models in `models/agent.py`
- Keep mock responses realistic for testing purposes

## Support

For issues or questions:
1. Check [docs/DEV_MODE.md](DEV_MODE.md) for troubleshooting
2. Try [scripts/test_dev_mode.py](../scripts/test_dev_mode.py) to verify setup
3. Review [docs/QUICK_START_DEV_MODE.md](QUICK_START_DEV_MODE.md) for examples
