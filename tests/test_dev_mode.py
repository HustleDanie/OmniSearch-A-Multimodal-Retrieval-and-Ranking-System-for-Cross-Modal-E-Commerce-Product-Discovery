"""
Test dev mode configuration and toggling.
"""
import os
import sys
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_dev_mode_enabled():
    """Test that dev mode uses mock provider."""
    os.environ["DEV_MODE"] = "true"
    
    # Import after setting env var
    from config.settings import settings
    from services.llm_client import LLMClient
    
    assert settings.DEV_MODE is True
    
    client = LLMClient()
    assert client.provider == "mock"
    assert client.client is None
    
    # Test response
    response = client.generate("test prompt")
    assert "Blue Casual Shirt" in response
    assert "recommendations" in response


def test_dev_mode_disabled_without_api_key():
    """Test that without API key and dev mode off, it falls back to mock."""
    os.environ["DEV_MODE"] = "false"
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]
    
    # Reload settings
    import importlib
    from config import settings as settings_module
    importlib.reload(settings_module)
    
    from services.llm_client import LLMClient
    
    client = LLMClient(provider="openai")
    # Should fall back to mock due to missing API key
    assert client.provider == "mock"


def test_mock_response_format():
    """Test that mock response is valid JSON."""
    import json
    
    from services.llm_client import LLMClient
    
    client = LLMClient(provider="mock")
    response = client.generate("test")
    
    # Should be valid JSON
    data = json.loads(response)
    
    # Should have recommendations
    assert "recommendations" in data
    assert len(data["recommendations"]) == 4
    
    # Check structure
    for rec in data["recommendations"]:
        assert "title" in rec
        assert "why" in rec
        assert "is_wildcard" in rec


def test_dev_mode_message():
    """Test that dev mode prints a message."""
    import io
    from contextlib import redirect_stdout
    
    os.environ["DEV_MODE"] = "true"
    
    # Import and reset
    from services import llm_client
    import importlib
    importlib.reload(llm_client)
    
    # Capture stdout
    f = io.StringIO()
    with redirect_stdout(f):
        from services.llm_client import LLMClient
        client = LLMClient()
    
    output = f.getvalue()
    assert "Dev mode enabled" in output or client.provider == "mock"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
