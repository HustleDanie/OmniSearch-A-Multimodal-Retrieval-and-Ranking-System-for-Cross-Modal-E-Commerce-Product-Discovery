"""
Load testing script using Locust for OmniSearch search endpoints.

Simulates concurrent search users with graphical interface and statistics.

Install Locust:
    pip install locust
    
Run:
    locust -f scripts/load_test_locust.py --host=http://localhost:8000 --users=100 --spawn-rate=10
    
Then open http://localhost:8089 in browser
"""

from locust import HttpUser, task, between
import statistics
import time
from typing import List, Dict


class SearchQueries:
    """Collection of realistic search queries"""

    QUERIES = [
        "blue running shoes",
        "red winter jacket",
        "black backpack",
        "summer dress",
        "athletic shirt",
        "denim jeans",
        "cotton socks",
        "leather belt",
        "wool sweater",
        "hiking boots",
        "casual sneakers",
        "formal dress shoes",
        "rain jacket",
        "cargo pants",
        "graphic tee",
        "polo shirt",
        "winter gloves",
        "summer hat",
        "tactical vest",
        "sports shorts",
    ]

    @classmethod
    def get_random(cls) -> str:
        """Get a random query"""
        import random
        return random.choice(cls.QUERIES)


class SearchUser(HttpUser):
    """Simulates a search user"""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Called when a user starts"""
        self.query_count = 0
        self.latencies: List[float] = []

    @task(1)
    def search_text(self):
        """Simulate a text search request"""
        query = SearchQueries.get_random()

        payload = {
            "query": query,
            "top_k": 10,
            "category": None,
            "color": None,
            "debug": False,
        }

        start = time.perf_counter()

        response = self.client.post(
            "/search/text",
            json=payload,
            catch_response=True,
        )

        elapsed = (time.perf_counter() - start) * 1000

        if response.status_code == 200:
            response.success()
            self.latencies.append(elapsed)
            self.query_count += 1
        else:
            response.failure(f"Unexpected status code: {response.status_code}")

    @task(1)
    def search_diverse(self):
        """
        Task with different search patterns
        """
        import random

        query = SearchQueries.get_random()
        top_k = random.choice([5, 10, 20, 50])

        payload = {
            "query": query,
            "top_k": top_k,
            "category": None,
            "color": None,
            "debug": False,
        }

        start = time.perf_counter()

        response = self.client.post(
            "/search/text",
            json=payload,
            catch_response=True,
        )

        elapsed = (time.perf_counter() - start) * 1000

        if response.status_code == 200:
            response.success()
            self.latencies.append(elapsed)
            self.query_count += 1
        else:
            response.failure(f"Unexpected status code: {response.status_code}")

    def on_stop(self):
        """Called when a user stops"""
        if self.latencies:
            print(
                f"\nUser {id(self)} Summary - "
                f"Queries: {self.query_count}, "
                f"Avg Latency: {statistics.mean(self.latencies):.2f}ms, "
                f"P95: {sorted(self.latencies)[int(len(self.latencies)*0.95)]:.2f}ms"
            )
