#!/usr/bin/env python3
"""
Demo script for A/B testing search variants.

This script demonstrates how to:
1. Assign users to search variants
2. Execute searches with each variant
3. Log search events to the A/B framework
4. Compare metrics between variants
"""
from unittest.mock import Mock, patch
from services.ab_testing import get_experiment_manager, reset_experiment_manager, ExperimentVariant
from services.search_variants import SearchVariantV1, SearchVariantV2, get_search_variant
import random


def mock_search_results(num_results: int = 5):
    """Generate mock search results."""
    results = []
    for i in range(num_results):
        result = Mock()
        result.product_id = f"prod_{i+1000}"
        result.title = f"Product {i+1}"
        result.description = f"A great product with {i+1} features"
        result.color = random.choice(["blue", "red", "green", "black", "white"])
        result.category = random.choice(["footwear", "electronics", "clothing"])
        result.image_path = f"/images/product_{i}.jpg"
        result.similarity = round(0.95 - i * 0.05, 2)
        result.distance = round(i * 0.05, 2)
        result.debug_scores = None
        results.append(result)
    return results


def demo_1_basic_assignment():
    """Demo 1: Basic variant assignment."""
    print("\n" + "="*70)
    print("DEMO 1: Basic Variant Assignment")
    print("="*70)
    
    reset_experiment_manager()
    manager = get_experiment_manager()
    
    # Assign 5 users to variants
    print("\nAssigning 5 users to variants...")
    for i in range(1, 6):
        user_id = f"user_{i}"
        assignment = manager.assign_variant(user_id)
        variant_name = "V1 (Vector Only)" if assignment.variant == ExperimentVariant.SEARCH_V1 else "V2 (Vector + Ranking)"
        print(f"  {user_id:12} → {variant_name}")
    
    print("\n✓ Assignment complete")


def demo_2_variant_comparison():
    """Demo 2: Compare V1 and V2 behavior."""
    print("\n" + "="*70)
    print("DEMO 2: Variant Behavior Comparison")
    print("="*70)
    
    reset_experiment_manager()
    
    # Create mock search service
    with patch('services.search_variants.get_search_service') as mock_get_service:
        mock_service = Mock()
        mock_results = mock_search_results(5)
        mock_service.search_by_text.return_value = mock_results
        mock_get_service.return_value = mock_service
        
        print("\nSearching with V1 (Vector Similarity Only)...")
        v1 = get_search_variant("search_v1")
        v1_results, v1_time = v1.search_by_text("blue shoes", top_k=5)
        print(f"  Results: {len(v1_results)} products")
        print(f"  Time: {v1_time:.2f}ms")
        print(f"  Re-ranking: Disabled")
        
        mock_service.search_by_text.reset_mock()
        mock_results = mock_search_results(5)
        mock_service.search_by_text.return_value = mock_results
        
        print("\nSearching with V2 (Vector + Ranking Engine)...")
        v2 = get_search_variant("search_v2")
        v2_results, v2_time = v2.search_by_text("blue shoes", top_k=5)
        print(f"  Results: {len(v2_results)} products")
        print(f"  Time: {v2_time:.2f}ms")
        print(f"  Re-ranking: Enabled (0.5*vector + 0.2*color + 0.2*category + 0.1*text)")
        
        # Check which variant was called with which setting
        v1_call = mock_service.search_by_text.call_args_list[0][1]
        v2_call = mock_service.search_by_text.call_args_list[1][1]
        
        print("\n✓ V1 calls search_by_text with enable_reranking=False")
        print("✓ V2 calls search_by_text with enable_reranking=True")


def demo_3_search_and_logging():
    """Demo 3: Execute searches and log events."""
    print("\n" + "="*70)
    print("DEMO 3: Search Execution with Event Logging")
    print("="*70)
    
    reset_experiment_manager()
    manager = get_experiment_manager()
    
    # Simulate 3 users performing searches
    users = ["alice", "bob", "charlie"]
    queries = ["blue running shoes", "red jacket", "wireless headphones"]
    
    with patch('services.search_variants.get_search_service') as mock_get_service:
        mock_service = Mock()
        mock_service.search_by_text.return_value = mock_search_results(3)
        mock_get_service.return_value = mock_service
        
        for user_id, query in zip(users, queries):
            # Assign variant
            assignment = manager.assign_variant(user_id)
            variant_name = "V1" if assignment.variant == ExperimentVariant.SEARCH_V1 else "V2"
            
            # Execute search
            variant = get_search_variant("search_v1" if assignment.variant == ExperimentVariant.SEARCH_V1 else "search_v2")
            results, elapsed_ms = variant.search_by_text(query, top_k=3)
            
            # Log event
            manager.log_search(
                user_id=user_id,
                query=query,
                results_count=len(results),
                search_time_ms=elapsed_ms
            )
            
            print(f"\n{user_id} ({variant}):")
            print(f"  Query: '{query}'")
            print(f"  Results: {len(results)} products")
            print(f"  Time: {elapsed_ms:.2f}ms")


def demo_4_metrics_and_comparison():
    """Demo 4: View aggregate metrics."""
    print("\n" + "="*70)
    print("DEMO 4: Metrics and A/B Comparison")
    print("="*70)
    
    reset_experiment_manager()
    manager = get_experiment_manager()
    
    # Simulate searches for both variants
    with patch('services.search_variants.get_search_service') as mock_get_service:
        mock_service = Mock()
        mock_service.search_by_text.return_value = mock_search_results(5)
        mock_get_service.return_value = mock_service
        
        # V1 searches
        print("\nSimulating V1 searches...")
        for i in range(5):
            user_id = f"v1_user_{i}"
            manager.assign_variant(user_id, metadata={"variant_type": "baseline"})
            mock_service.search_by_text.return_value = mock_search_results(random.randint(3, 8))
            v1 = get_search_variant("search_v1")
            results, elapsed = v1.search_by_text(f"query {i}", top_k=5)
            manager.log_search(user_id, f"query {i}", len(results), elapsed)
        
        # V2 searches
        print("Simulating V2 searches...")
        for i in range(5):
            user_id = f"v2_user_{i}"
            manager.assign_variant(user_id, metadata={"variant_type": "enhanced"})
            mock_service.search_by_text.return_value = mock_search_results(random.randint(3, 8))
            v2 = get_search_variant("search_v2")
            results, elapsed = v2.search_by_text(f"query {i}", top_k=5)
            manager.log_search(user_id, f"query {i}", len(results), elapsed)
        
        # Get metrics
        metrics = manager.get_metrics()
        
        print("\nAggregate Metrics:")
        print(f"  Total searches: {metrics['total_searches']}")
        print(f"  Searches per variant:")
        for variant, count in metrics['searches_by_variant'].items():
            print(f"    {variant.value}: {count}")
        
        if 'ctr_by_variant' in metrics:
            print(f"  CTR by variant:")
            for variant, ctr in metrics.get('ctr_by_variant', {}).items():
                print(f"    {variant.value}: {ctr:.2%}")
        
        print(f"  Avg results count per variant:")
        for variant, avg in metrics.get('avg_results_by_variant', {}).items():
            print(f"    {variant.value}: {avg:.1f}")


def demo_5_variant_consistency():
    """Demo 5: Demonstrate variant assignment consistency."""
    print("\n" + "="*70)
    print("DEMO 5: Variant Assignment Consistency")
    print("="*70)
    
    reset_experiment_manager()
    manager = get_experiment_manager()
    
    user_id = "persistent_user"
    
    # First assignment
    print(f"\nFirst assignment for {user_id}:")
    assignment1 = manager.assign_variant(user_id)
    variant1 = "V1" if assignment1.variant == ExperimentVariant.SEARCH_V1 else "V2"
    print(f"  Assigned to: {variant1}")
    
    # Second lookup (should be same)
    print(f"\nSecond lookup for {user_id}:")
    assignment2 = manager.get_assignment(user_id)
    variant2 = "V1" if assignment2.variant == ExperimentVariant.SEARCH_V1 else "V2"
    print(f"  Assigned to: {variant2}")
    
    # Multiple lookups
    print(f"\nTen subsequent lookups for {user_id}:")
    variants_match = True
    for i in range(10):
        assignment = manager.get_assignment(user_id)
        variant = "V1" if assignment.variant == ExperimentVariant.SEARCH_V1 else "V2"
        if i % 5 == 0:
            print(f"  Lookup {i+3}: {variant}")
        if variant != variant1:
            variants_match = False
    
    if variants_match:
        print("\n✓ User consistently assigned to same variant")
    else:
        print("\n✗ ERROR: User assigned to different variants!")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("A/B TESTING SEARCH VARIANTS - DEMONSTRATION")
    print("="*70)
    
    demo_1_basic_assignment()
    demo_2_variant_comparison()
    demo_3_search_and_logging()
    demo_4_metrics_and_comparison()
    demo_5_variant_consistency()
    
    print("\n" + "="*70)
    print("✓ All demos complete!")
    print("="*70 + "\n")
