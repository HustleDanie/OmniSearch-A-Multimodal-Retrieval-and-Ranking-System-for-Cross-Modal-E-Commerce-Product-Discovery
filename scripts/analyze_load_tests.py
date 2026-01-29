"""
Utility for analyzing and comparing load test results.

Analyzes JSON exports from AsyncIO load tests and generates reports.
"""

import json
import statistics
from pathlib import Path
from typing import List, Dict
import argparse
from datetime import datetime
import glob


class LoadTestAnalyzer:
    """Analyze load test results"""

    def __init__(self):
        self.results: Dict = {}

    def load_result(self, filepath: str, label: str = None) -> None:
        """Load a single load test result"""
        if label is None:
            label = Path(filepath).stem

        with open(filepath) as f:
            data = json.load(f)
            self.results[label] = data

        print(f"✓ Loaded: {label}")

    def load_results_glob(self, pattern: str) -> None:
        """Load multiple results matching glob pattern"""
        files = glob.glob(pattern)
        for filepath in sorted(files):
            self.load_result(filepath)

    def print_result(self, label: str) -> None:
        """Print detailed result for a single test"""
        if label not in self.results:
            print(f"✗ Result not found: {label}")
            return

        data = self.results[label]
        metrics = data["metrics"]
        config = data["configuration"]
        duration = data["duration_seconds"]

        print(f"\n{'='*80}")
        print(f"TEST: {label}")
        print(f"{'='*80}")

        print(f"\nConfiguration:")
        print(f"  Base URL: {config['base_url']}")
        print(f"  Users: {config['num_users']}")
        print(f"  Requests/User: {config['requests_per_user']}")
        print(f"  Duration: {duration:.2f}s")

        print(f"\nLatency Metrics (ms):")
        print(f"  Min:     {metrics['min_ms']:>10.2f}")
        print(f"  Max:     {metrics['max_ms']:>10.2f}")
        print(f"  Avg:     {metrics['avg_ms']:>10.2f}")
        print(f"  Median:  {metrics['median_ms']:>10.2f}")
        print(f"  StDev:   {metrics['stdev_ms']:>10.2f}")
        print(f"  P50:     {metrics['p50_ms']:>10.2f}")
        print(f"  P95:     {metrics['p95_ms']:>10.2f}")
        print(f"  P99:     {metrics['p99_ms']:>10.2f}")

        print(f"\nRequest Metrics:")
        print(f"  Total:       {metrics['total_requests']:>10}")
        print(f"  Successful:  {metrics['successful_requests']:>10}")
        print(f"  Failed:      {metrics['failed_requests']:>10}")
        print(f"  Error Rate:  {metrics['error_rate']:>10.2f}%")

        rps = metrics["total_requests"] / duration if duration > 0 else 0
        print(f"\nThroughput:")
        print(f"  Requests/sec: {rps:>10.2f}")

        print(f"\n{'='*80}")

    def compare_results(self, labels: List[str] = None) -> None:
        """Compare multiple results"""
        if labels is None:
            labels = list(self.results.keys())

        if len(labels) < 2:
            print("✗ Need at least 2 results to compare")
            return

        print(f"\n{'='*120}")
        print("COMPARISON")
        print(f"{'='*120}\n")

        # Header
        print(f"{'Test':<20} {'Users':<10} {'Avg (ms)':<12} {'P95 (ms)':<12} "
              f"{'P99 (ms)':<12} {'Error %':<10} {'RPS':<10}")
        print(f"{'-'*120}")

        baseline_avg = None

        for label in labels:
            if label not in self.results:
                continue

            data = self.results[label]
            metrics = data["metrics"]
            config = data["configuration"]
            duration = data["duration_seconds"]

            avg = metrics["avg_ms"]
            p95 = metrics["p95_ms"]
            p99 = metrics["p99_ms"]
            error = metrics["error_rate"]
            rps = metrics["total_requests"] / duration if duration > 0 else 0
            users = config["num_users"]

            print(f"{label:<20} {users:<10} {avg:<12.2f} {p95:<12.2f} "
                  f"{p99:<12.2f} {error:<10.2f} {rps:<10.2f}")

            if baseline_avg is None:
                baseline_avg = avg

        print(f"\n{'-'*120}\n")

        # Calculate regressions
        print("Latency Regression (vs first test):")
        baseline_avg = None
        baseline_label = None

        for label in labels:
            if label not in self.results:
                continue

            data = self.results[label]
            metrics = data["metrics"]
            avg = metrics["avg_ms"]

            if baseline_avg is None:
                baseline_avg = avg
                baseline_label = label
                print(f"  {label:<20} (baseline)")
            else:
                regression = ((avg - baseline_avg) / baseline_avg) * 100
                symbol = "📈" if regression > 0 else "📉"
                print(f"  {label:<20} {regression:+.1f}% {symbol}")

        print(f"\n{'='*120}\n")

    def performance_report(self, labels: List[str] = None) -> None:
        """Generate comprehensive performance report"""
        if labels is None:
            labels = list(self.results.keys())

        print(f"\n{'='*80}")
        print("PERFORMANCE REPORT")
        print(f"{'='*80}\n")

        for label in labels:
            if label not in self.results:
                continue

            data = self.results[label]
            metrics = data["metrics"]
            config = data["configuration"]
            duration = data["duration_seconds"]

            # Performance assessment
            avg = metrics["avg_ms"]
            p95 = metrics["p95_ms"]
            error = metrics["error_rate"]

            print(f"{label}:")
            print(f"  Configuration: {config['num_users']} users × {config['requests_per_user']} requests")

            # Latency assessment
            if avg < 50:
                latency_status = "✓ Excellent"
            elif avg < 100:
                latency_status = "✓ Good"
            elif avg < 200:
                latency_status = "⚠ Acceptable"
            else:
                latency_status = "✗ Poor"

            print(f"  Avg Latency: {avg:.2f}ms - {latency_status}")

            # P95 assessment
            if p95 < 100:
                p95_status = "✓ Excellent"
            elif p95 < 200:
                p95_status = "✓ Good"
            elif p95 < 500:
                p95_status = "⚠ Acceptable"
            else:
                p95_status = "✗ Poor"

            print(f"  P95 Latency: {p95:.2f}ms - {p95_status}")

            # Error rate assessment
            if error < 0.1:
                error_status = "✓ Excellent"
            elif error < 1:
                error_status = "✓ Good"
            elif error < 5:
                error_status = "⚠ Monitor"
            else:
                error_status = "✗ Critical"

            print(f"  Error Rate: {error:.2f}% - {error_status}")

            # Throughput
            rps = metrics["total_requests"] / duration if duration > 0 else 0
            print(f"  Throughput: {rps:.2f} requests/sec")

            # Recommendations
            print(f"  Recommendations:")
            if avg > 100:
                print(f"    - Consider optimizing search algorithm")
            if p95 > 200:
                print(f"    - P95 latency is high, add caching or indexes")
            if error > 1:
                print(f"    - Error rate elevated, check API logs")
            if error < 0.1 and avg < 50:
                print(f"    - Performance is excellent!")

            print()

    def export_comparison_csv(self, filepath: str, labels: List[str] = None) -> None:
        """Export comparison as CSV"""
        if labels is None:
            labels = list(self.results.keys())

        import csv

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "Test",
                "Users",
                "Requests/User",
                "Total Requests",
                "Successful",
                "Failed",
                "Error Rate %",
                "Min (ms)",
                "Max (ms)",
                "Avg (ms)",
                "Median (ms)",
                "StDev (ms)",
                "P50 (ms)",
                "P95 (ms)",
                "P99 (ms)",
                "RPS",
                "Duration (s)",
            ])

            for label in labels:
                if label not in self.results:
                    continue

                data = self.results[label]
                metrics = data["metrics"]
                config = data["configuration"]
                duration = data["duration_seconds"]
                rps = metrics["total_requests"] / duration if duration > 0 else 0

                writer.writerow([
                    label,
                    config["num_users"],
                    config["requests_per_user"],
                    metrics["total_requests"],
                    metrics["successful_requests"],
                    metrics["failed_requests"],
                    metrics["error_rate"],
                    metrics["min_ms"],
                    metrics["max_ms"],
                    metrics["avg_ms"],
                    metrics["median_ms"],
                    metrics["stdev_ms"],
                    metrics["p50_ms"],
                    metrics["p95_ms"],
                    metrics["p99_ms"],
                    rps,
                    duration,
                ])

        print(f"✓ Exported comparison to: {filepath}")

    def export_comparison_html(self, filepath: str, labels: List[str] = None) -> None:
        """Export comparison as HTML report"""
        if labels is None:
            labels = list(self.results.keys())

        html = """
        <html>
        <head>
            <title>Load Test Comparison</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: right; }
                th { background-color: #4CAF50; color: white; }
                tr:nth-child(even) { background-color: #f2f2f2; }
                .good { color: green; font-weight: bold; }
                .warning { color: orange; font-weight: bold; }
                .error { color: red; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>Load Test Comparison Report</h1>
            <p>Generated: """ + datetime.now().isoformat() + """</p>
            
            <h2>Summary</h2>
            <table>
                <tr>
                    <th>Test</th>
                    <th>Users</th>
                    <th>Avg Latency (ms)</th>
                    <th>P95 Latency (ms)</th>
                    <th>P99 Latency (ms)</th>
                    <th>Error Rate (%)</th>
                    <th>RPS</th>
                </tr>
        """

        for label in labels:
            if label not in self.results:
                continue

            data = self.results[label]
            metrics = data["metrics"]
            config = data["configuration"]
            duration = data["duration_seconds"]
            rps = metrics["total_requests"] / duration if duration > 0 else 0

            # Color coding
            avg_class = "good" if metrics["avg_ms"] < 50 else "warning" if metrics["avg_ms"] < 100 else "error"
            p95_class = "good" if metrics["p95_ms"] < 100 else "warning" if metrics["p95_ms"] < 200 else "error"
            error_class = "good" if metrics["error_rate"] < 0.1 else "warning" if metrics["error_rate"] < 1 else "error"

            html += f"""
                <tr>
                    <td>{label}</td>
                    <td>{config['num_users']}</td>
                    <td class="{avg_class}">{metrics['avg_ms']:.2f}</td>
                    <td class="{p95_class}">{metrics['p95_ms']:.2f}</td>
                    <td>{metrics['p99_ms']:.2f}</td>
                    <td class="{error_class}">{metrics['error_rate']:.2f}</td>
                    <td>{rps:.2f}</td>
                </tr>
            """

        html += """
            </table>
        </body>
        </html>
        """

        with open(filepath, "w") as f:
            f.write(html)

        print(f"✓ Exported HTML report to: {filepath}")


def main():
    parser = argparse.ArgumentParser(description="Analyze load test results")

    parser.add_argument("files", nargs="*", help="Result JSON files to analyze")
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare multiple results",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate performance report",
    )
    parser.add_argument(
        "--export-csv",
        help="Export comparison as CSV",
    )
    parser.add_argument(
        "--export-html",
        help="Export comparison as HTML",
    )
    parser.add_argument(
        "--glob",
        help="Load results matching glob pattern",
    )

    args = parser.parse_args()

    analyzer = LoadTestAnalyzer()

    # Load results
    if args.glob:
        analyzer.load_results_glob(args.glob)
    else:
        for filepath in args.files:
            analyzer.load_result(filepath)

    if not analyzer.results:
        print("✗ No results loaded")
        return

    # Print individual results if no aggregate requested
    if not (args.compare or args.report or args.export_csv or args.export_html):
        for label in analyzer.results.keys():
            analyzer.print_result(label)
        args.compare = True

    # Generate outputs
    if args.compare:
        analyzer.compare_results()

    if args.report:
        analyzer.performance_report()

    if args.export_csv:
        analyzer.export_comparison_csv(args.export_csv)

    if args.export_html:
        analyzer.export_comparison_html(args.export_html)


if __name__ == "__main__":
    main()
