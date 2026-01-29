"""
A/B Testing Demo Script

Shows how to use the A/B testing module with realistic scenarios.
"""

import requests
import json
import time
from typing import List, Dict, Any
import random


API_URL = "http://localhost:8000"


def demo_1_basic_assignment():
    """Demo 1: Basic user assignment."""
    print("\n" + "=" * 70)
    print("DEMO 1: Basic User Assignment")
    print("=" * 70)
    
    for i in range(5):
        user_id = f"user_{i}"
        response = requests.post(f"{API_URL}/ab/assign?user_id={user_id}")
        data = response.json()
        print(f"  {user_id}: assigned to {data['variant']}")


def demo_2_search_and_click():
    """Demo 2: Log search and click events."""
    print("\n" + "=" * 70)
    print("DEMO 2: Search and Click Events")
    print("=" * 70)
    
    headers = {"X-User-ID": "user_demo2", "X-Session-ID": "session_abc"}
    
    # Log a search
    print("  Logging search...")
    search_response = requests.post(
        f"{API_URL}/ab/log-search",
        headers=headers,
        json={
            "query": "casual blue shirts",
            "results_count": 24,
            "search_time_ms": 145.5
        }
    )
    search_data = search_response.json()
    print(f"    - Variant: {search_data['variant']}")
    print(f"    - Query: casual blue shirts")
    print(f"    - Results: 24")
    
    time.sleep(0.5)  # Simulate user browsing
    
    # Log a click
    print("  Logging click...")
    click_response = requests.post(
        f"{API_URL}/ab/log-click",
        headers=headers,
        json={
            "product_id": "prod_456",
            "product_title": "Blue Casual Shirt",
            "position": 0,
            "query": "casual blue shirts"
        }
    )
    click_data = click_response.json()
    print(f"    - Clicked: Blue Casual Shirt (product_456)")
    print(f"    - Position: 0")


def demo_3_multi_user_simulation():
    """Demo 3: Simulate multiple users with searches and clicks."""
    print("\n" + "=" * 70)
    print("DEMO 3: Multi-User Simulation (20 users)")
    print("=" * 70)
    
    queries = [
        "casual shirts",
        "blue jeans",
        "running shoes",
        "summer dresses",
        "winter jackets"
    ]
    
    products = [
        ("prod_101", "Classic Blue Shirt", "shirts"),
        ("prod_102", "Dark Blue Jeans", "jeans"),
        ("prod_201", "Running Shoes Pro", "shoes"),
        ("prod_202", "Summer Floral Dress", "dresses"),
        ("prod_301", "Winter Parka", "jackets"),
    ]
    
    for user_num in range(20):
        user_id = f"sim_user_{user_num}"
        session_id = f"session_{user_num}"
        headers = {"X-User-ID": user_id, "X-Session-ID": session_id}
        
        # Random search
        query = random.choice(queries)
        requests.post(
            f"{API_URL}/ab/log-search",
            headers=headers,
            json={
                "query": query,
                "results_count": random.randint(5, 30),
                "search_time_ms": random.uniform(50, 200)
            }
        )
        
        # 60% chance to click
        if random.random() < 0.6:
            product_id, title, category = random.choice(products)
            requests.post(
                f"{API_URL}/ab/log-click",
                headers=headers,
                json={
                    "product_id": product_id,
                    "product_title": title,
                    "position": random.randint(0, 4),
                    "query": query
                }
            )
        
        print(f"  User {user_num:2d}: {query:20s} - ", end="")
        assignment = requests.get(
            f"{API_URL}/ab/assignment?user_id={user_id}"
        ).json()
        print(f"variant: {assignment['variant']}")


def demo_4_view_metrics():
    """Demo 4: View aggregate metrics."""
    print("\n" + "=" * 70)
    print("DEMO 4: Aggregate Metrics")
    print("=" * 70)
    
    response = requests.get(f"{API_URL}/ab/metrics")
    metrics = response.json()
    
    print(f"\n  Overall Statistics:")
    print(f"    Total Events: {metrics['total_events']}")
    print(f"    Total Users: {metrics['total_assignments']}")
    print(f"    Search Events: {metrics['search_events']}")
    print(f"    Click Events: {metrics['click_events']}")
    
    print(f"\n  Performance Metrics:")
    print(f"    Avg Search Time: {metrics['avg_search_time_ms']:.1f}ms")
    print(f"    Avg Results per Search: {metrics['avg_results']:.1f}")
    
    v1 = metrics['search_v1']
    v2 = metrics['search_v2']
    
    print(f"\n  Variant Comparison:")
    print(f"    {'Metric':<20} {'V1':<15} {'V2':<15}")
    print(f"    {'-' * 50}")
    print(f"    {'Searches':<20} {v1['count']:<15} {v2['count']:<15}")
    print(f"    {'Clicks':<20} {v1['clicks']:<15} {v2['clicks']:<15}")
    print(f"    {'CTR':<20} {v1['ctr']:.2%} {' ' * 9} {v2['ctr']:.2%}")
    
    # Determine winner
    if v1['ctr'] > v2['ctr']:
        difference = (v1['ctr'] - v2['ctr']) / v2['ctr'] * 100
        print(f"\n  ✓ V1 outperforms V2 by {difference:.1f}%")
    elif v2['ctr'] > v1['ctr']:
        difference = (v2['ctr'] - v1['ctr']) / v1['ctr'] * 100
        print(f"\n  ✓ V2 outperforms V1 by {difference:.1f}%")
    else:
        print(f"\n  = Both variants have equal CTR")


def demo_5_filter_events():
    """Demo 5: Filter and query events."""
    print("\n" + "=" * 70)
    print("DEMO 5: Query Events with Filters")
    print("=" * 70)
    
    # Get events for one user
    print("  All events for sim_user_0:")
    response = requests.get(
        f"{API_URL}/ab/events?user_id=sim_user_0&limit=10"
    )
    events = response.json()
    
    for i, event in enumerate(events['events'], 1):
        if event['event_type'] == 'search':
            print(f"    {i}. SEARCH: '{event['query']}' - {event.get('results_count', 0)} results")
        else:
            print(f"    {i}. CLICK: {event.get('product_title', 'Unknown')} (pos {event.get('position', -1)})")
    
    # Get search_v1 only
    print("\n  Search events for search_v1 variant:")
    response = requests.get(
        f"{API_URL}/ab/events?variant=search_v1&event_type=search&limit=5"
    )
    events = response.json()
    
    count = 0
    for event in events['events'][:3]:
        print(f"    - '{event['query']}' by {event['user_id']}")
        count += 1
    
    if events['count'] > 3:
        print(f"    ... and {events['count'] - 3} more")


def demo_6_reset_and_start_over():
    """Demo 6: Reset data to start fresh."""
    print("\n" + "=" * 70)
    print("DEMO 6: Reset and Start Fresh")
    print("=" * 70)
    
    # Show current state
    response = requests.get(f"{API_URL}/ab/metrics")
    before = response.json()
    print(f"  Before reset: {before['total_events']} events")
    
    # Reset
    response = requests.delete(f"{API_URL}/ab/reset")
    result = response.json()
    print(f"  Reset: {result['message']}")
    
    # Show after state
    response = requests.get(f"{API_URL}/ab/metrics")
    after = response.json()
    print(f"  After reset: {after['total_events']} events")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "A/B TESTING MODULE - DEMONSTRATION".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        # Check API is running
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code != 200:
            print("\n❌ API is not responding correctly")
            print(f"   Status: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to API at", API_URL)
        print("\nStart the server with:")
        print("  uvicorn main:app --reload")
        return
    
    # Run demos
    demo_1_basic_assignment()
    demo_2_search_and_click()
    demo_3_multi_user_simulation()
    demo_4_view_metrics()
    demo_5_filter_events()
    demo_6_reset_and_start_over()
    
    print("\n" + "=" * 70)
    print("✓ All demos completed successfully!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Check metrics at: http://localhost:8000/ab/metrics")
    print("  2. View API docs at: http://localhost:8000/docs")
    print("  3. Read more at: docs/AB_TESTING.md")
    print()


if __name__ == "__main__":
    main()
