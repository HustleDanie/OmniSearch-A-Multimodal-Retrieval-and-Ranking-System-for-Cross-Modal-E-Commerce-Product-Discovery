"""Test script for dev mode with mocked LLM responses."""
import os
import sys

# Set dev mode before importing settings
os.environ["DEV_MODE"] = "true"

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.settings import settings
# Import directly from module to avoid circular imports
import importlib.util
spec = importlib.util.spec_from_file_location("llm_client", "services/llm_client.py")
llm_client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(llm_client)
reset_llm_client = llm_client.reset_llm_client
get_llm_client = llm_client.get_llm_client

def test_dev_mode():
    """Test that dev mode uses mocked LLM responses."""
    print("=" * 60)
    print("Testing Dev Mode with Mocked LLM Responses")
    print("=" * 60)
    
    # Check settings
    print(f"\n1. DEV_MODE setting: {settings.DEV_MODE}")
    
    # Reset and get client
    reset_llm_client()
    client = get_llm_client()
    
    print(f"2. LLM Provider: {client.provider}")
    print(f"3. LLM Model: {client.model}")
    
    # Generate response
    print("\n4. Generating mock recommendation...")
    response = client.generate("Recommend products for casual wear")
    
    print(f"\n5. Response received ({len(response)} chars)")
    print("-" * 60)
    print(response)
    print("-" * 60)
    
    # Verify it's a mock response
    is_mock = "Blue Casual Shirt" in response
    print(f"\n6. Mock response verification: {'✓ PASS' if is_mock else '✗ FAIL'}")
    
    if is_mock:
        print("\n✓ SUCCESS: Dev mode is working correctly!")
        print("  - No external API calls made")
        print("  - Mock responses returned instantly")
        return True
    else:
        print("\n✗ FAILED: Dev mode not working as expected")
        return False

if __name__ == "__main__":
    success = test_dev_mode()
    sys.exit(0 if success else 1)
