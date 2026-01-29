"""
Personal Shopper Agent for LLM-powered product recommendations.
Workflow:
- Fetch user profile
- Retrieve search results (provided or via injected search service)
- Build RAG context via retrieve_context
- Call LLM with structured prompt
- Return structured recommendations payload
"""
from typing import Any, Dict, List, Optional

from services.context_retrieval import ContextRetriever, retrieve_context
from db.user_service import UserProfileService


class PersonalShopperAgent:
    """Orchestrates personalization flow and calls an LLM for recommendations."""

    def __init__(
        self,
        llm_client: Any,
        user_service: Optional[UserProfileService] = None,
        search_service: Optional[Any] = None,
        context_retriever: Optional[ContextRetriever] = None,
    ) -> None:
        """
        Initialize the agent.

        Args:
            llm_client: Object with `.generate(prompt: str) -> str` method.
            user_service: Optional user profile service (must be connected externally).
            search_service: Optional search service with a `.search(query, user_id=None, top_k=10)` method
                            or any callable that returns a list of search results dicts.
            context_retriever: Optional context retriever instance (defaults to ContextRetriever()).
        """
        if not llm_client:
            raise ValueError("llm_client is required and must expose generate(prompt: str) -> str")

        self.llm_client = llm_client
        self.user_service = user_service
        self.search_service = search_service
        self.context_retriever = context_retriever or ContextRetriever()

    def build_prompt(self, context: str, template: Optional[str] = None) -> str:
        """Build the LLM prompt with a default structured format."""
        if template:
            return template.replace("{{context}}", context)

        return (
            "You are a fashion/product stylist. Use the user context to craft personalized picks.\n\n"
            "USER CONTEXT:\n"
            f"{context}\n\n"
            "TASKS:\n"
            "1) Recommend exactly 3 products from the search results.\n"
            "2) For each, explain why it matches the user's taste (cite colors, styles, categories, price fit).\n"
            "3) Add 1 wildcard item outside their norm but still plausible; explain the novelty.\n\n"
            "OUTPUT JSON ONLY (no extra text):\n"
            "{\n"
            '  "recommendations": [\n'
            '    {"title": str, "why": str, "is_wildcard": false},\n'
            '    {"title": str, "why": str, "is_wildcard": false},\n'
            '    {"title": str, "why": str, "is_wildcard": false},\n'
            '    {"title": str, "why": str, "is_wildcard": true}\n'
            "  ]\n"
            "}\n"
        )

    def recommend(
        self,
        user_id: str,
        query: Optional[str] = None,
        search_results: Optional[List[Dict[str, Any]]] = None,
        max_results: int = 5,
        prompt_template: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate structured recommendations.

        Args:
            user_id: Target user identifier.
            query: Optional search query if search_results not provided.
            search_results: Optional precomputed search results list of dicts.
            max_results: Maximum number of results to include in context.
            prompt_template: Optional prompt template containing {{context}} placeholder.

        Returns:
            Dict with prompt, context, LLM response, and the products used.
        """
        # 1) Get user profile (if available)
        user_profile = None
        if self.user_service:
            user_profile = self.user_service.get_user_profile(user_id)

        # 2) Retrieve search results
        results: List[Dict[str, Any]]
        if search_results is not None:
            results = search_results
        elif self.search_service and query is not None:
            if callable(getattr(self.search_service, "search", None)):
                results = self.search_service.search(query=query, user_id=user_id, top_k=max_results)
            elif callable(self.search_service):
                results = self.search_service(query, user_id=user_id, top_k=max_results)
            else:
                raise ValueError("search_service must have a .search(...) method or be callable")
        else:
            raise ValueError("search_results or (search_service and query) must be provided")

        # 3) Build RAG context
        context_text = retrieve_context(user_id=user_id, search_results=results, max_results=max_results)

        # 4) Build prompt and call LLM
        prompt = self.build_prompt(context=context_text, template=prompt_template)
        llm_response = self.llm_client.generate(prompt)

        # 5) Return structured payload
        return {
            "user_id": user_id,
            "prompt": prompt,
            "context": context_text,
            "llm_response": llm_response,
            "search_results": results[:max_results],
            "user_profile": user_profile,
        }
