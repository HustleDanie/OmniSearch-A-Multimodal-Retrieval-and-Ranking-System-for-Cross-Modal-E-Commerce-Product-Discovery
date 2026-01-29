"""
Example: Complete workflow using retrieve_context for LLM-powered personalization.

This example demonstrates:
1. Performing a multimodal search
2. Retrieving user preferences
3. Generating LLM-formatted context
4. Using context for recommendations

Run this to see retrieve_context in action:
    python examples/llm_personalization_example.py
"""

from typing import List, Dict, Any
import json


def example_multimodal_search() -> List[Dict[str, Any]]:
    """
    Simulates performing a multimodal search.
    In production, this would call ProductSearchService.
    """
    return [
        {
            "title": "Blue Casual Cotton Shirt",
            "description": "Comfortable everyday cotton shirt with breathable fabric",
            "color": "blue",
            "category": "apparel",
            "price": 49.99,
            "score": 0.96,
            "brand": "StyleCo",
            "size": "M-L"
        },
        {
            "title": "Navy Elegant Linen Blazer",
            "description": "Premium linen blend blazer perfect for professional settings",
            "color": "navy",
            "category": "apparel",
            "price": 129.99,
            "score": 0.92,
            "brand": "Premium Wear"
        },
        {
            "title": "White Classic Casual Shoes",
            "description": "Versatile white sneakers with premium comfort technology",
            "color": "white",
            "category": "footwear",
            "price": 89.99,
            "score": 0.88,
            "brand": "ComfortStride"
        },
        {
            "title": "Blue Comfortable Loafers",
            "description": "Slip-on loafers in rich blue with cushioned sole",
            "color": "blue",
            "category": "footwear",
            "price": 99.99,
            "score": 0.85,
            "brand": "StyleCo"
        },
        {
            "title": "Gray Classic Sweater",
            "description": "Soft wool blend sweater in neutral gray",
            "color": "gray",
            "category": "apparel",
            "price": 69.99,
            "score": 0.82,
            "brand": "Premium Wear"
        }
    ]


def example_llm_context() -> str:
    """
    Simulates the output of retrieve_context() function.
    Shows what formatted context looks like for LLM consumption.
    """
    return """USER PREFERENCES:
- Preferred Colors: blue (5), black (3), white (2)
- Favorite Categories: apparel (8), footwear (4)
- Style Profile: Classic elegant style with casual comfort elements
- Popular Styles: casual, elegant, comfortable, classic
- Price Range: $50-$150
- Size Preference: Medium

SEARCH RESULTS (5 items):

Result 1: Blue Casual Cotton Shirt
Description: Comfortable everyday cotton shirt with breathable fabric
Category: apparel
Color: blue
Price: $49.99
Relevance Score: 0.96
Brand: StyleCo
Size: M-L

Result 2: Navy Elegant Linen Blazer
Description: Premium linen blend blazer perfect for professional settings
Category: apparel
Color: navy
Price: $129.99
Relevance Score: 0.92
Brand: Premium Wear

Result 3: White Classic Casual Shoes
Description: Versatile white sneakers with premium comfort technology
Category: footwear
Color: white
Price: $89.99
Relevance Score: 0.88
Brand: ComfortStride

Result 4: Blue Comfortable Loafers
Description: Slip-on loafers in rich blue with cushioned sole
Category: footwear
Color: blue
Price: $99.99
Relevance Score: 0.85
Brand: StyleCo

Result 5: Gray Classic Sweater
Description: Soft wool blend sweater in neutral gray
Category: apparel
Color: gray
Price: $69.99
Relevance Score: 0.82
Brand: Premium Wear"""


def example_llm_prompts(context: str) -> Dict[str, str]:
    """
    Example LLM prompts that use the retrieve_context output.
    """
    return {
        "recommendation": f"""
Based on this user's style preferences and purchase history:

{context}

Recommend the top product from these results and explain why it's the best match 
for this user. Consider their color preferences, style profile, and category interests.
Consider the relevance score, price, and brand quality.
""",
        
        "personalized_description": f"""
{context}

Create a personalized product description for the top result that appeals to this 
specific user's style preferences. Highlight aspects that match their known preferences.
""",
        
        "outfit_suggestion": f"""
{context}

Based on the user's style profile and these products, suggest a complete outfit 
combining multiple items from the results. Explain how each piece works together 
for their style.
""",
        
        "color_justification": f"""
{context}

The top search result is blue. Explain how this color choice aligns with this 
specific user's color preferences and style profile.
""",
        
        "price_guidance": f"""
{context}

The user's typical price range is $50-$150. Analyze if these products fit their 
budget and value perception. Recommend the best value option.
"""
    }


def format_example_output():
    """
    Demonstrates the full workflow and outputs.
    """
    print("=" * 80)
    print("EXAMPLE: LLM-Powered Personalization with retrieve_context()")
    print("=" * 80)
    print()
    
    # Step 1: Simulate search
    print("STEP 1: Perform Multimodal Search")
    print("-" * 80)
    search_results = example_multimodal_search()
    print(f"Found {len(search_results)} relevant products")
    for i, result in enumerate(search_results[:3], 1):
        print(f"  {i}. {result['title']} (Score: {result['score']:.2f})")
    print()
    
    # Step 2: Retrieve context for LLM
    print("STEP 2: Call retrieve_context(user_id, search_results)")
    print("-" * 80)
    context = example_llm_context()
    print("Generated context (first 500 chars):")
    print(context[:500])
    print("...")
    print()
    
    # Step 3: Show example prompts
    print("STEP 3: Generate LLM Prompts with Context")
    print("-" * 80)
    prompts = example_llm_prompts(context)
    
    print("\nAvailable LLM prompts using the context:")
    for name in prompts.keys():
        print(f"  • {name}")
    
    print("\nExample: Recommendation Prompt")
    print("---")
    print(prompts["recommendation"][:300])
    print("...")
    print()
    
    # Step 4: Show what LLM might return
    print("STEP 4: LLM Response Example")
    print("-" * 80)
    example_response = """
The Blue Casual Cotton Shirt is the perfect match for this user. Here's why:

1. **Color Match**: Blue is the user's dominant preferred color (5 purchases), 
   appearing twice in their recent purchase history. This immediately aligns 
   with their established color preferences.

2. **Style Alignment**: The 'casual' and 'comfortable' descriptors match their 
   style profile perfectly. While they appreciate elegant pieces, the casual 
   comfort elements show this is versatile for their lifestyle.

3. **Perfect Price Point**: At $49.99, this falls well within their typical 
   budget range of $50-$150, making it an accessible choice.

4. **Quality Brand**: StyleCo is a brand they've purchased from before 
   (shown in their Blue Comfortable Loafers), indicating trust and 
   satisfaction with the brand.

5. **Category Fit**: Apparel is their most frequent purchase category (8 items), 
   and shirts/tops are essential basics they consistently buy.

6. **High Relevance**: The 0.96 relevance score indicates strong semantic 
   similarity to their preferences.

Recommendation: Add to cart immediately. This is an excellent match for 
building their casual wardrobe while maintaining their classic elegant aesthetic.
    """
    print(example_response.strip())
    print()
    
    # Step 5: Show integration
    print("STEP 5: Integration Pattern")
    print("-" * 80)
    integration_code = '''
from services import retrieve_context
from llm_service import LLMClient

# In your API endpoint or service:
@app.post("/recommendations/{user_id}")
async def get_personalized_recommendations(user_id: str, query: str):
    # 1. Perform search
    search_results = search_service.search(query, user_id)
    
    # 2. Get context for LLM
    context = retrieve_context(user_id, search_results, max_results=5)
    
    # 3. Generate prompt
    prompt = f"""
    Based on user preferences and search results:
    
    {context}
    
    Provide personalized product recommendations.
    """
    
    # 4. Call LLM
    response = llm_client.generate(prompt)
    
    # 5. Return to user
    return {
        "recommendations": response,
        "products": search_results,
        "user_context": context  # Optionally include for debugging
    }
    '''
    print(integration_code)
    print()
    
    print("=" * 80)
    print("KEY BENEFITS:")
    print("=" * 80)
    print("""
✓ User Preferences: Automatically extracted from purchase history
✓ Structured Format: Ready for LLM consumption, no extra parsing needed
✓ Context Inclusion: Colors, categories, styles all in one formatted string
✓ Multiple Use Cases: Recommendations, descriptions, outfit suggestions, etc.
✓ Flexible: Works with any LLM (GPT-4, Claude, Llama, etc.)
✓ Scalable: Lazy-loaded services, minimal database queries
✓ Testable: 14+ unit tests verify correct formatting
    """.strip())
    print()


if __name__ == "__main__":
    format_example_output()
