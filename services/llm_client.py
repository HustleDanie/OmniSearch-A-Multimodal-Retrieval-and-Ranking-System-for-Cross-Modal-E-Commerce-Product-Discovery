"""
LLM Client for generating product recommendations.
Provides a simple interface to different LLM providers.
"""
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

from config.settings import settings


class LLMClient:
    """Simple LLM client interface."""
    
    def __init__(self, provider: str = "openai", model: str = "gpt-3.5-turbo"):
        """
        Initialize LLM client.
        
        Args:
            provider: LLM provider ("openai", "mock", etc.)
            model: Model name for the provider
        """
        self.provider = provider
        self.model = model
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the underlying LLM client based on provider."""
        # Check if dev mode is enabled
        if settings.DEV_MODE:
            print("Dev mode enabled: Using mock LLM responses (no external API calls)")
            self.provider = "mock"
            self.client = None
            return
            
        if self.provider == "openai":
            try:
                import openai
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    print("Warning: OPENAI_API_KEY not set. Using mock client.")
                    self.provider = "mock"
                    self.client = None
                else:
                    self.client = openai.OpenAI(api_key=api_key)
            except ImportError:
                print("Warning: openai package not installed. Using mock client.")
                self.provider = "mock"
                self.client = None
        else:
            self.client = None
    
    def generate(self, prompt: str) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            The LLM's response text
        """
        if self.provider == "openai" and self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1000,
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"OpenAI API error: {e}. Falling back to mock response.")
                return self._mock_response(prompt)
        else:
            return self._mock_response(prompt)
    
    def _mock_response(self, prompt: str) -> str:
        """Generate a mock response for testing/demo."""
        return (
            '{"recommendations": ['
            '{"title": "Blue Casual Shirt", "why": "Matches your preference for casual blue apparel", "is_wildcard": false},'
            '{"title": "Black Formal Blazer", "why": "Complements your style with professional pieces", "is_wildcard": false},'
            '{"title": "Navy Chinos", "why": "Versatile neutral piece that works with multiple styles", "is_wildcard": false},'
            '{"title": "Vintage Denim Jacket", "why": "A wildcard piece that adds character to your wardrobe", "is_wildcard": true}'
            "]}"
        )


# Global LLM client instance
_llm_client_instance: Optional[LLMClient] = None


def get_llm_client() -> Optional[LLMClient]:
    """
    Get or create a global LLM client instance.
    
    Returns:
        LLMClient instance or None if initialization fails
    """
    global _llm_client_instance
    if _llm_client_instance is None:
        try:
            provider = os.getenv("LLM_PROVIDER", "openai")
            model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
            _llm_client_instance = LLMClient(provider=provider, model=model)
        except Exception as e:
            print(f"Error initializing LLM client: {e}")
            return None
    
    return _llm_client_instance


def reset_llm_client():
    """Reset the global LLM client (useful for testing)."""
    global _llm_client_instance
    _llm_client_instance = None
