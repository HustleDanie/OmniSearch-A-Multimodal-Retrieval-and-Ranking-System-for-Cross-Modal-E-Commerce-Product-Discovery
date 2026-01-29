"""
Example usage of Product Search Service.
Demonstrates text, image, and multimodal search capabilities.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import get_search_service
import numpy as np


def example_text_search():
    """Example: Search products by text query."""
    print("=" * 80)
    print("TEXT SEARCH EXAMPLE")
    print("=" * 80)
    
    search_service = get_search_service()
    
    # Search for products
    query = "red athletic shoes"
    print(f"\nQuery: '{query}'\n")
    
    results = search_service.search_by_text(
        query_text=query,
        top_k=10  # Get top 10 results
    )
    
    # Display results
    search_service.print_results(results)
    
    return results


def example_text_search_with_filters():
    """Example: Search with category and color filters."""
    print("\n" + "=" * 80)
    print("TEXT SEARCH WITH FILTERS")
    print("=" * 80)
    
    search_service = get_search_service()
    
    # Search with filters
    query = "comfortable clothing"
    print(f"\nQuery: '{query}'")
    print("Filter: category='apparel'\n")
    
    results = search_service.search_by_text(
        query_text=query,
        top_k=5,
        category_filter="apparel"
    )
    
    search_service.print_results(results)
    
    return results


def example_image_search():
    """Example: Search products by image (requires actual image)."""
    print("\n" + "=" * 80)
    print("IMAGE SEARCH EXAMPLE")
    print("=" * 80)
    
    search_service = get_search_service()
    
    # Try to search by image
    image_path = "path/to/query/image.jpg"
    
    print(f"\nQuery image: {image_path}\n")
    
    try:
        results = search_service.search_by_image(
            image_path=image_path,
            top_k=5
        )
        
        search_service.print_results(results)
        return results
        
    except FileNotFoundError:
        print("Note: Provide actual image path to test image search")
        print("\nExample usage:")
        print("  results = search_service.search_by_image('product.jpg', top_k=10)")
        print("  search_service.print_results(results)")


def example_multimodal_search():
    """Example: Search using both text and image."""
    print("\n" + "=" * 80)
    print("MULTIMODAL SEARCH EXAMPLE")
    print("=" * 80)
    
    search_service = get_search_service()
    
    text_query = "blue sports equipment"
    print(f"\nText query: '{text_query}'")
    print("(Would combine with image query if image path provided)\n")
    
    # For demo purposes, using text-only since we don't have real images
    results = search_service.search_by_text(
        query_text=text_query,
        top_k=5
    )
    
    search_service.print_results(results)
    
    print("\nNote: For true multimodal search with both text and image:")
    print("  results = search_service.search_multimodal(")
    print("      text_query='blue sports equipment',")
    print("      image_path='reference_image.jpg',")
    print("      text_weight=0.5  # 50% text, 50% image")
    print("  )")
    
    return results


def example_vector_search():
    """Example: Search using a raw vector."""
    print("\n" + "=" * 80)
    print("DIRECT VECTOR SEARCH EXAMPLE")
    print("=" * 80)
    
    search_service = get_search_service()
    
    # Generate a custom query vector
    print("\nGenerating query vector from text...\n")
    query_vector = search_service.clip_service.embed_text("black leather accessories")
    
    # Search directly with vector
    results = search_service.search_by_vector(
        query_vector=query_vector,
        top_k=5
    )
    
    search_service.print_results(results)
    
    return results


def example_formatted_results():
    """Example: Get results as dictionaries for API responses."""
    print("\n" + "=" * 80)
    print("FORMATTED RESULTS (API-READY)")
    print("=" * 80)
    
    search_service = get_search_service()
    
    # Perform search
    results = search_service.search_by_text("green backpack", top_k=3)
    
    # Format as dictionaries
    formatted = search_service.format_results(results)
    
    print("\nResults as JSON-serializable dictionaries:\n")
    import json
    print(json.dumps(formatted, indent=2))
    
    return formatted


def example_comparison_search():
    """Example: Compare different search queries."""
    print("\n" + "=" * 80)
    print("SEARCH COMPARISON")
    print("=" * 80)
    
    search_service = get_search_service()
    
    queries = [
        "red shoes",
        "athletic footwear",
        "casual sneakers"
    ]
    
    for query in queries:
        print(f"\n--- Query: '{query}' ---")
        results = search_service.search_by_text(query, top_k=3)
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.title} (similarity: {result.similarity:.4f})")


if __name__ == "__main__":
    print("\n🔍 Product Search Service Examples\n")
    
    try:
        # Run examples
        example_text_search()
        example_text_search_with_filters()
        example_image_search()
        example_multimodal_search()
        example_vector_search()
        example_formatted_results()
        example_comparison_search()
        
        print("\n✓ All examples completed!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure:")
        print("  1. Weaviate is running")
        print("  2. Products have been uploaded using generate_embeddings.py")
        print("  3. WEAVIATE_URL is set in .env file")
