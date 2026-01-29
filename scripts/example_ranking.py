"""
Example: Re-rank search results using combined factors.
"""
import sys
import os

# Make package importable when running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import get_search_service, rerank_results


def main():
    search_service = get_search_service()

    query_text = "blue denim jacket"
    query_color = "blue"
    query_category = "apparel"

    print("Querying Weaviate for initial vector results...")
    initial = search_service.search_by_text(query_text, top_k=10)

    print(f"Initial results: {len(initial)}")

    # Re-rank using our weighting formula
    reranked = rerank_results(
        results=[r.to_dict() for r in initial],
        query_text=query_text,
        query_color=query_color,
        query_category=query_category,
    )

    print("\nTop 5 after re-ranking:\n")
    for i, r in enumerate(reranked[:5], 1):
        print(f"{i}. {r['title']} | color={r.get('color')} | category={r.get('category')} | "
              f"vector={r.get('similarity'):.4f} | final={r.get('final_score'):.4f}")


if __name__ == "__main__":
    main()
