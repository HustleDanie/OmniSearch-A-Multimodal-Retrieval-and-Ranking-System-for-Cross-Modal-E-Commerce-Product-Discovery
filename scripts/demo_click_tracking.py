"""
Demo script for click tracking and analytics functionality.

This script demonstrates:
1. Logging search impressions
2. Logging click events
3. Retrieving CTR metrics
4. Analyzing rank metrics
5. Comparing variants
"""

import requests
import json
import random
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

def demo_1_basic_tracking():
    """Demo 1: Basic click tracking workflow."""
    print("\n" + "="*60)
    print("DEMO 1: Basic Click Tracking Workflow")
    print("="*60)
    
    user_id = "user_demo_001"
    session_id = "session_001"
    
    # Step 1: Log a search impression
    print(f"\n1. Logging search impression for user {user_id}...")
    impression_data = {
        "query": "blue running shoes",
        "variant": "search_v1",
        "results_count": 42,
        "response_time_ms": 45.2
    }
    
    response = requests.post(
        f"{BASE_URL}/analytics/log-impression",
        json=impression_data,
        headers={"X-User-ID": user_id}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    
    # Step 2: Log a click on result
    print(f"\n2. Logging click event (user clicked result at rank 2)...")
    click_data = {
        "product_id": "prod_nike_001",
        "rank": 2,
        "search_query": "blue running shoes",
        "variant": "search_v1",
        "response_time_ms": 45.2,
        "source": "SEARCH_RESULTS"
    }
    
    response = requests.post(
        f"{BASE_URL}/analytics/log-click",
        json=click_data,
        headers={"X-User-ID": user_id}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    
    # Step 3: Get CTR for this user
    print(f"\n3. Retrieving CTR metrics for {user_id}...")
    response = requests.get(
        f"{BASE_URL}/analytics/ctr",
        params={"user_id": user_id}
    )
    print(f"   Status: {response.status_code}")
    ctr_data = response.json()
    print(f"   CTR: {ctr_data.get('ctr', 0):.2%}")
    print(f"   Clicks: {ctr_data.get('clicks', 0)}, Impressions: {ctr_data.get('impressions', 0)}")


def demo_2_variant_comparison():
    """Demo 2: Compare variants across multiple searches."""
    print("\n" + "="*60)
    print("DEMO 2: Variant Comparison with Multiple Searches")
    print("="*60)
    
    # Simulate searches with both variants
    queries = ["blue shoes", "winter jackets", "running shorts"]
    
    for i, query in enumerate(queries):
        variant = "search_v1" if i % 2 == 0 else "search_v2"
        user_id = f"user_compare_{i}"
        
        print(f"\n{i+1}. Logging search with {variant}: '{query}'")
        
        # Log impression
        impression_data = {
            "query": query,
            "variant": variant,
            "results_count": random.randint(10, 100),
            "response_time_ms": random.uniform(30, 100)
        }
        
        response = requests.post(
            f"{BASE_URL}/analytics/log-impression",
            json=impression_data,
            headers={"X-User-ID": user_id}
        )
        
        # Log click (50% of impressions)
        if random.random() > 0.5:
            click_data = {
                "product_id": f"prod_{i}",
                "rank": random.randint(0, 5),
                "search_query": query,
                "variant": variant,
                "response_time_ms": impression_data["response_time_ms"],
                "source": "SEARCH_RESULTS"
            }
            
            response = requests.post(
                f"{BASE_URL}/analytics/log-click",
                json=click_data,
                headers={"X-User-ID": user_id}
            )
            print(f"   └─ Click logged at rank {click_data['rank']}")
        else:
            print(f"   └─ No click recorded")
    
    # Compare variants
    print(f"\n4. Comparing variant performance...")
    response = requests.get(f"{BASE_URL}/analytics/variants-comparison?days=7")
    comparison = response.json()
    
    if "error" not in comparison:
        print(f"   Status: {response.status_code}")
        print(f"   Period: {comparison.get('period_days', 7)} days")
        print(f"   Variants data: {json.dumps(comparison, indent=2)}")
    else:
        print(f"   Note: {comparison.get('error', 'No data yet for comparison')}")


def demo_3_rank_analysis():
    """Demo 3: Analyze which ranks get clicked."""
    print("\n" + "="*60)
    print("DEMO 3: Rank Position Analysis")
    print("="*60)
    
    user_id = "user_rank_analysis"
    
    # Log several impressions and clicks at different ranks
    print(f"\n1. Logging multiple clicks at different ranks for {user_id}...")
    
    results = [
        ("high_rank_click_0", 0),
        ("mid_rank_click_2", 2),
        ("low_rank_click_5", 5),
        ("high_rank_click_0_2", 0),
        ("mid_rank_click_3", 3)
    ]
    
    for i, (product_id, rank) in enumerate(results):
        # Log impression first
        impression_data = {
            "query": "product search",
            "variant": "search_v1",
            "results_count": 20,
            "response_time_ms": 50.0 + i
        }
        
        requests.post(
            f"{BASE_URL}/analytics/log-impression",
            json=impression_data,
            headers={"X-User-ID": user_id}
        )
        
        # Log click
        click_data = {
            "product_id": product_id,
            "rank": rank,
            "search_query": "product search",
            "variant": "search_v1",
            "response_time_ms": 50.0 + i,
            "source": "SEARCH_RESULTS"
        }
        
        response = requests.post(
            f"{BASE_URL}/analytics/log-click",
            json=click_data,
            headers={"X-User-ID": user_id}
        )
        print(f"   ├─ Rank {rank}: {product_id}")
    
    # Get rank metrics
    print(f"\n2. Analyzing rank metrics...")
    response = requests.get(
        f"{BASE_URL}/analytics/rank-metrics",
        params={"user_id": user_id}
    )
    
    if response.status_code == 200:
        metrics = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Average rank clicked: {metrics.get('avg_rank', 0):.1f}")
        print(f"   Total clicks: {metrics.get('total_clicks', 0)}")
        print(f"   Rank distribution:")
        for rank, count in sorted(metrics.get('clicks_by_rank', {}).items()):
            print(f"      └─ Rank {rank}: {count} clicks")


def demo_4_response_time_analysis():
    """Demo 4: Analyze response times across searches."""
    print("\n" + "="*60)
    print("DEMO 4: Response Time Analysis")
    print("="*60)
    
    user_id = "user_response_times"
    
    # Log searches with varying response times
    print(f"\n1. Logging searches with different response times...")
    
    response_times = [
        ("v1_fast", "search_v1", 20.5),
        ("v1_slow", "search_v1", 150.3),
        ("v2_fast", "search_v2", 30.1),
        ("v2_medium", "search_v2", 75.8),
        ("v1_medium", "search_v1", 60.0)
    ]
    
    for product_id, variant, response_time in response_times:
        impression_data = {
            "query": "test query",
            "variant": variant,
            "results_count": 30,
            "response_time_ms": response_time
        }
        
        response = requests.post(
            f"{BASE_URL}/analytics/log-impression",
            json=impression_data,
            headers={"X-User-ID": user_id}
        )
        print(f"   ├─ {variant}: {response_time}ms")
    
    # Get response time metrics
    print(f"\n2. Response time statistics...")
    response = requests.get(
        f"{BASE_URL}/analytics/response-time",
        params={"user_id": user_id}
    )
    
    if response.status_code == 200:
        metrics = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Average: {metrics.get('avg_response_time_ms', 0):.1f}ms")
        print(f"   Min: {metrics.get('min_response_time_ms', 0):.1f}ms")
        print(f"   Max: {metrics.get('max_response_time_ms', 0):.1f}ms")
        print(f"   95th percentile: {metrics.get('p95_response_time_ms', 0):.1f}ms")
        print(f"   Samples: {metrics.get('count', 0)}")


def demo_5_user_summary():
    """Demo 5: Get comprehensive user summary."""
    print("\n" + "="*60)
    print("DEMO 5: User Analytics Summary")
    print("="*60)
    
    user_id = "user_comprehensive"
    
    # Log multiple events
    print(f"\n1. Logging diverse user interactions...")
    
    for i in range(3):
        variant = "search_v1" if i % 2 == 0 else "search_v2"
        
        # Impression
        impression_data = {
            "query": f"query_{i}",
            "variant": variant,
            "results_count": random.randint(5, 50),
            "response_time_ms": random.uniform(25, 150)
        }
        
        requests.post(
            f"{BASE_URL}/analytics/log-impression",
            json=impression_data,
            headers={"X-User-ID": user_id}
        )
        
        # Click
        if random.random() > 0.3:
            click_data = {
                "product_id": f"prod_comp_{i}",
                "rank": random.randint(0, 10),
                "search_query": f"query_{i}",
                "variant": variant,
                "response_time_ms": impression_data["response_time_ms"],
                "source": "SEARCH_RESULTS"
            }
            
            requests.post(
                f"{BASE_URL}/analytics/log-click",
                json=click_data,
                headers={"X-User-ID": user_id}
            )
    
    # Get user summary
    print(f"\n2. User summary for {user_id}...")
    response = requests.get(
        f"{BASE_URL}/analytics/user/{user_id}?days=7"
    )
    
    if response.status_code == 200:
        summary = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Total clicks: {summary.get('total_clicks', 0)}")
        print(f"   Total impressions: {summary.get('total_impressions', 0)}")
        print(f"   CTR: {summary.get('ctr', 0):.2%}")
        print(f"   Avg rank clicked: {summary.get('avg_rank_clicked', 0):.1f}")
        print(f"   Avg response time: {summary.get('avg_response_time_ms', 0):.1f}ms")
        print(f"   Variants used: {summary.get('variants_used', [])}")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("CLICK TRACKING & ANALYTICS DEMO")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"API Endpoint: {BASE_URL}")
    
    try:
        # Test connectivity
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code != 200:
            print("\n⚠️  Warning: API may not be running at expected endpoint")
            print("   Please ensure the FastAPI server is running at", BASE_URL)
            return
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API at", BASE_URL)
        print("   Please start the FastAPI server first:")
        print("   python -m uvicorn main:app --reload")
        return
    
    # Run demos
    demo_1_basic_tracking()
    demo_2_variant_comparison()
    demo_3_rank_analysis()
    demo_4_response_time_analysis()
    demo_5_user_summary()
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. View API documentation: http://localhost:8000/docs")
    print("2. Check analytics dashboard at: http://localhost:8000/analytics/ctr")
    print("3. Explore variant comparison: http://localhost:8000/analytics/variants-comparison")


if __name__ == "__main__":
    main()
