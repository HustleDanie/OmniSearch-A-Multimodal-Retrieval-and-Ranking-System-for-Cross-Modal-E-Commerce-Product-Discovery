"""
Load testing script using asyncio for OmniSearch search endpoints.

Simulates concurrent search users and measures latency metrics.
"""

import asyncio
import aiohttp
import time
import statistics
import json
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse


@dataclass
class LatencyMetrics:
    """Container for latency statistics"""
    min_ms: float
    max_ms: float
    avg_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    median_ms: float
    stdev_ms: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float


class AsyncLoadTester:
    """Async load testing for search endpoints"""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        num_users: int = 100,
        requests_per_user: int = 10,
    ):
        self.base_url = base_url
        self.num_users = num_users
        self.requests_per_user = requests_per_user
        self.latencies: List[float] = []
        self.errors: List[str] = []
        self.start_time: float = 0
        self.end_time: float = 0

    async def make_search_request(
        self,
        session: aiohttp.ClientSession,
        user_id: int,
        search_queries: List[str],
    ) -> Tuple[List[float], List[str]]:
        """
        Make search requests as a simulated user

        Returns:
            Tuple of (latencies, errors)
        """
        user_latencies = []
        user_errors = []

        for i, query in enumerate(search_queries):
            try:
                payload = {
                    "query": query,
                    "top_k": 10,
                    "category": None,
                    "color": None,
                    "debug": False,
                }

                start = time.perf_counter()

                async with session.post(
                    f"{self.base_url}/search/text",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    await response.json()
                    elapsed = (time.perf_counter() - start) * 1000  # Convert to ms

                    user_latencies.append(elapsed)

                    if response.status != 200:
                        user_errors.append(
                            f"User {user_id}: HTTP {response.status} on request {i}"
                        )

            except asyncio.TimeoutError:
                user_errors.append(f"User {user_id}: Timeout on request {i}")
            except Exception as e:
                user_errors.append(f"User {user_id}: {str(e)}")

        return user_latencies, user_errors

    async def simulate_user(
        self,
        user_id: int,
        search_queries: List[str],
    ) -> Tuple[List[float], List[str]]:
        """
        Simulate a single user making requests
        """
        connector = aiohttp.TCPConnector(limit_per_host=5)
        async with aiohttp.ClientSession(connector=connector) as session:
            return await self.make_search_request(session, user_id, search_queries)

    async def run_load_test(self, search_queries: List[str] = None) -> LatencyMetrics:
        """
        Run the load test with concurrent users

        Args:
            search_queries: List of search queries to use. If None, uses defaults.
        """
        if search_queries is None:
            search_queries = [
                "blue running shoes",
                "red winter jacket",
                "black backpack",
                "summer dress",
                "athletic shirt",
                "jeans",
                "casual socks",
                "leather belt",
                "wool sweater",
                "hiking boots",
            ]

        # Ensure we have enough queries
        search_queries = search_queries * ((self.requests_per_user // len(search_queries)) + 1)
        search_queries = search_queries[:self.requests_per_user]

        print(f"\n{'='*80}")
        print(f"LOAD TEST CONFIGURATION")
        print(f"{'='*80}")
        print(f"Base URL: {self.base_url}")
        print(f"Concurrent Users: {self.num_users}")
        print(f"Requests per User: {self.requests_per_user}")
        print(f"Total Requests: {self.num_users * self.requests_per_user}")
        print(f"{'='*80}\n")

        # Start load test
        self.start_time = time.perf_counter()

        print("Launching concurrent users...")

        # Create tasks for all users
        tasks = []
        for user_id in range(self.num_users):
            task = self.simulate_user(user_id, search_queries)
            tasks.append(task)

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        self.end_time = time.perf_counter()

        # Aggregate results
        for result in results:
            if isinstance(result, Exception):
                self.errors.append(str(result))
            else:
                latencies, errors = result
                self.latencies.extend(latencies)
                self.errors.extend(errors)

        # Calculate metrics
        return self._calculate_metrics()

    def _calculate_metrics(self) -> LatencyMetrics:
        """Calculate latency metrics from collected data"""
        total_requests = self.num_users * self.requests_per_user
        successful_requests = len(self.latencies)
        failed_requests = total_requests - successful_requests

        if not self.latencies:
            return LatencyMetrics(
                min_ms=0,
                max_ms=0,
                avg_ms=0,
                p50_ms=0,
                p95_ms=0,
                p99_ms=0,
                median_ms=0,
                stdev_ms=0,
                total_requests=total_requests,
                successful_requests=0,
                failed_requests=failed_requests,
                error_rate=100.0,
            )

        sorted_latencies = sorted(self.latencies)

        p50_idx = int(len(sorted_latencies) * 0.50)
        p95_idx = int(len(sorted_latencies) * 0.95)
        p99_idx = int(len(sorted_latencies) * 0.99)

        return LatencyMetrics(
            min_ms=min(self.latencies),
            max_ms=max(self.latencies),
            avg_ms=statistics.mean(self.latencies),
            p50_ms=sorted_latencies[p50_idx] if p50_idx < len(sorted_latencies) else 0,
            p95_ms=sorted_latencies[p95_idx] if p95_idx < len(sorted_latencies) else 0,
            p99_ms=sorted_latencies[p99_idx] if p99_idx < len(sorted_latencies) else 0,
            median_ms=statistics.median(self.latencies),
            stdev_ms=statistics.stdev(self.latencies) if len(self.latencies) > 1 else 0,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            error_rate=(failed_requests / total_requests * 100) if total_requests > 0 else 0,
        )

    def print_results(self, metrics: LatencyMetrics) -> None:
        """Print formatted results"""
        elapsed_time = self.end_time - self.start_time

        print(f"\n{'='*80}")
        print(f"LOAD TEST RESULTS")
        print(f"{'='*80}")
        print(f"Total Time: {elapsed_time:.2f}s")
        print(f"Requests/Second: {metrics.total_requests / elapsed_time:.2f}")
        print(f"{'='*80}\n")

        print("LATENCY METRICS (ms)")
        print(f"{'='*80}")
        print(f"Min:     {metrics.min_ms:>10.2f} ms")
        print(f"Max:     {metrics.max_ms:>10.2f} ms")
        print(f"Avg:     {metrics.avg_ms:>10.2f} ms")
        print(f"Median:  {metrics.median_ms:>10.2f} ms")
        print(f"StDev:   {metrics.stdev_ms:>10.2f} ms")
        print(f"P50:     {metrics.p50_ms:>10.2f} ms")
        print(f"P95:     {metrics.p95_ms:>10.2f} ms")
        print(f"P99:     {metrics.p99_ms:>10.2f} ms")
        print(f"{'='*80}\n")

        print("REQUEST METRICS")
        print(f"{'='*80}")
        print(f"Total Requests:      {metrics.total_requests:>10}")
        print(f"Successful:          {metrics.successful_requests:>10}")
        print(f"Failed:              {metrics.failed_requests:>10}")
        print(f"Error Rate:          {metrics.error_rate:>10.2f}%")
        print(f"{'='*80}\n")

        if self.errors:
            print("ERRORS (First 10):")
            print(f"{'='*80}")
            for error in self.errors[:10]:
                print(f"  - {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more errors")
            print(f"{'='*80}\n")

    def export_results(self, metrics: LatencyMetrics, filepath: str) -> None:
        """Export results to JSON file"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "base_url": self.base_url,
                "num_users": self.num_users,
                "requests_per_user": self.requests_per_user,
            },
            "metrics": asdict(metrics),
            "duration_seconds": self.end_time - self.start_time,
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        print(f"Results exported to: {filepath}\n")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Load test OmniSearch with concurrent users"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the OmniSearch API (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--users",
        type=int,
        default=100,
        help="Number of concurrent users (default: 100)",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=10,
        help="Requests per user (default: 10)",
    )
    parser.add_argument(
        "--export",
        help="Export results to JSON file",
    )

    args = parser.parse_args()

    # Create and run load tester
    tester = AsyncLoadTester(
        base_url=args.url,
        num_users=args.users,
        requests_per_user=args.requests,
    )

    try:
        metrics = await tester.run_load_test()
        tester.print_results(metrics)

        if args.export:
            tester.export_results(metrics, args.export)

    except KeyboardInterrupt:
        print("\n\nLoad test interrupted by user")
    except Exception as e:
        print(f"\n\nLoad test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
