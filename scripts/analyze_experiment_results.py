"""
Experiment Analysis Script

Reads experiment logs, computes CTR for v1 vs v2, and generates visualizations.

Features:
- Load experiment data from JSON audit logs or MongoDB
- Calculate CTR (click-through rate) for each variant
- Generate detailed comparison plots
- Compute statistical metrics
- Export results to file
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Try to import MongoDB support
try:
    from pymongo import MongoClient
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False


@dataclass
class ExperimentMetrics:
    """Metrics for a single variant."""
    variant: str
    clicks: int
    impressions: int
    ctr: float
    avg_response_time: float
    total_users: int
    avg_clicks_per_user: float
    
    def __str__(self):
        return f"""
        Variant: {self.variant}
        ├─ CTR: {self.ctr:.2%}
        ├─ Clicks: {self.clicks}
        ├─ Impressions: {self.impressions}
        ├─ Users: {self.total_users}
        ├─ Avg clicks/user: {self.avg_clicks_per_user:.2f}
        └─ Avg response time: {self.avg_response_time:.1f}ms
        """


class ExperimentAnalyzer:
    """Analyze experiment results from logs."""
    
    def __init__(self):
        """Initialize analyzer."""
        self.events = []
        self.clicks = defaultdict(int)
        self.impressions = defaultdict(int)
        self.response_times = defaultdict(list)
        self.user_events = defaultdict(list)
    
    def load_from_json(self, filepath: str) -> None:
        """Load experiment events from JSON audit log."""
        print(f"Loading from JSON: {filepath}")
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Handle different JSON formats
        if isinstance(data, dict) and 'events' in data:
            events = data['events']
        elif isinstance(data, list):
            events = data
        else:
            raise ValueError("Unexpected JSON format")
        
        for event in events:
            self.events.append(event)
        
        print(f"Loaded {len(self.events)} events")
        self._process_events()
    
    def load_from_mongodb(self, mongodb_uri: str, db_name: str = "omnisearch") -> None:
        """Load experiment events from MongoDB."""
        if not MONGODB_AVAILABLE:
            raise ImportError("pymongo not installed")
        
        print(f"Loading from MongoDB: {mongodb_uri}")
        client = MongoClient(mongodb_uri)
        db = client[db_name]
        
        # Load click events
        click_events = list(db['click_events'].find())
        impressions_list = list(db['impressions'].find())
        
        print(f"Loaded {len(click_events)} clicks and {len(impressions_list)} impressions")
        
        # Convert to common format
        for click in click_events:
            self.events.append({
                'type': 'click',
                'user_id': click.get('user_id'),
                'variant': click.get('variant'),
                'timestamp': click.get('timestamp'),
                'response_time_ms': click.get('response_time_ms', 0)
            })
        
        for impression in impressions_list:
            self.events.append({
                'type': 'impression',
                'user_id': impression.get('user_id'),
                'variant': impression.get('variant'),
                'timestamp': impression.get('timestamp'),
                'response_time_ms': impression.get('response_time_ms', 0)
            })
        
        client.close()
        self._process_events()
    
    def _process_events(self) -> None:
        """Process loaded events."""
        for event in self.events:
            event_type = event.get('type', 'impression')
            variant = event.get('variant', 'unknown')
            user_id = event.get('user_id', 'unknown')
            response_time = event.get('response_time_ms', 0)
            
            self.user_events[user_id].append(event)
            self.response_times[variant].append(response_time)
            
            if event_type == 'click':
                self.clicks[variant] += 1
            elif event_type == 'impression':
                self.impressions[variant] += 1
    
    def compute_metrics(self) -> Dict[str, ExperimentMetrics]:
        """Compute metrics for each variant."""
        metrics = {}
        
        for variant in set(list(self.clicks.keys()) + list(self.impressions.keys())):
            clicks = self.clicks.get(variant, 0)
            impressions = self.impressions.get(variant, 0)
            ctr = clicks / impressions if impressions > 0 else 0
            
            # Response time stats
            times = self.response_times.get(variant, [])
            avg_response_time = np.mean(times) if times else 0
            
            # User stats
            users_by_variant = set()
            for user_id, events in self.user_events.items():
                if any(e.get('variant') == variant for e in events):
                    users_by_variant.add(user_id)
            
            total_users = len(users_by_variant)
            avg_clicks_per_user = clicks / total_users if total_users > 0 else 0
            
            metrics[variant] = ExperimentMetrics(
                variant=variant,
                clicks=clicks,
                impressions=impressions,
                ctr=ctr,
                avg_response_time=avg_response_time,
                total_users=total_users,
                avg_clicks_per_user=avg_clicks_per_user
            )
        
        return metrics
    
    def print_summary(self, metrics: Dict[str, ExperimentMetrics]) -> None:
        """Print summary of metrics."""
        print("\n" + "="*60)
        print("EXPERIMENT RESULTS SUMMARY")
        print("="*60)
        
        for variant, metric in sorted(metrics.items()):
            print(metric)
        
        # Compare variants
        if len(metrics) == 2:
            variants = sorted(metrics.keys())
            v1_ctr = metrics[variants[0]].ctr
            v2_ctr = metrics[variants[1]].ctr
            improvement = (v2_ctr - v1_ctr) / v1_ctr * 100 if v1_ctr > 0 else 0
            
            print("\n" + "="*60)
            print("COMPARISON")
            print("="*60)
            print(f"Variant: {variants[0]} vs {variants[1]}")
            print(f"CTR Improvement: {improvement:+.1f}%")
            print(f"Winner: {variants[1] if improvement > 0 else variants[0]} "
                  f"(by {abs(improvement):.1f}%)")
            print("="*60 + "\n")


class ExperimentVisualizer:
    """Create visualizations for experiment results."""
    
    def __init__(self, metrics: Dict[str, ExperimentMetrics], output_dir: str = "output"):
        """Initialize visualizer."""
        self.metrics = metrics
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.variants = sorted(metrics.keys())
        
        # Define colors
        self.colors = {
            'search_v1': '#3498db',  # Blue
            'search_v2': '#e74c3c',  # Red
        }
        # Fallback colors
        colors_list = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
        for i, variant in enumerate(self.variants):
            if variant not in self.colors:
                self.colors[variant] = colors_list[i % len(colors_list)]
    
    def plot_ctr_comparison(self) -> None:
        """Create CTR comparison plot."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        variants = self.variants
        ctrs = [self.metrics[v].ctr * 100 for v in variants]
        colors = [self.colors[v] for v in variants]
        
        bars = ax.bar(variants, ctrs, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Add value labels on bars
        for bar, ctr in zip(bars, ctrs):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{ctr:.2f}%',
                   ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax.set_ylabel('Click-Through Rate (%)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Variant', fontsize=12, fontweight='bold')
        ax.set_title('CTR Comparison: Search V1 vs V2', fontsize=14, fontweight='bold')
        ax.set_ylim(0, max(ctrs) * 1.15)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        filepath = self.output_dir / 'ctr_comparison.png'
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"Saved: {filepath}")
        plt.close()
    
    def plot_clicks_impressions(self) -> None:
        """Create clicks vs impressions plot."""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        variants = self.variants
        x = np.arange(len(variants))
        width = 0.35
        
        clicks = [self.metrics[v].clicks for v in variants]
        impressions = [self.metrics[v].impressions for v in variants]
        
        bars1 = ax.bar(x - width/2, impressions, width, label='Impressions',
                      color='#3498db', alpha=0.8, edgecolor='black')
        bars2 = ax.bar(x + width/2, clicks, width, label='Clicks',
                      color='#e74c3c', alpha=0.8, edgecolor='black')
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}',
                       ha='center', va='bottom', fontsize=10)
        
        ax.set_ylabel('Count', fontsize=12, fontweight='bold')
        ax.set_xlabel('Variant', fontsize=12, fontweight='bold')
        ax.set_title('Impressions vs Clicks by Variant', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(variants)
        ax.legend(fontsize=11)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        filepath = self.output_dir / 'clicks_impressions.png'
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"Saved: {filepath}")
        plt.close()
    
    def plot_response_times(self) -> None:
        """Create response time comparison plot."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        variants = self.variants
        response_times = [self.metrics[v].avg_response_time for v in variants]
        colors = [self.colors[v] for v in variants]
        
        bars = ax.bar(variants, response_times, color=colors, alpha=0.8,
                     edgecolor='black', linewidth=1.5)
        
        # Add value labels
        for bar, rt in zip(bars, response_times):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{rt:.1f}ms',
                   ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax.set_ylabel('Average Response Time (ms)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Variant', fontsize=12, fontweight='bold')
        ax.set_title('Response Time Comparison', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        filepath = self.output_dir / 'response_times.png'
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"Saved: {filepath}")
        plt.close()
    
    def plot_user_engagement(self) -> None:
        """Create user engagement metrics plot."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        variants = self.variants
        users = [self.metrics[v].total_users for v in variants]
        avg_clicks = [self.metrics[v].avg_clicks_per_user for v in variants]
        colors = [self.colors[v] for v in variants]
        
        # Total users
        bars1 = ax1.bar(variants, users, color=colors, alpha=0.8,
                       edgecolor='black', linewidth=1.5)
        for bar, user_count in zip(bars1, users):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax1.set_ylabel('Total Users', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Variant', fontsize=12, fontweight='bold')
        ax1.set_title('Total Users per Variant', fontsize=13, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Avg clicks per user
        bars2 = ax2.bar(variants, avg_clicks, color=colors, alpha=0.8,
                       edgecolor='black', linewidth=1.5)
        for bar, clicks in zip(bars2, avg_clicks):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{clicks:.2f}',
                    ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax2.set_ylabel('Avg Clicks per User', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Variant', fontsize=12, fontweight='bold')
        ax2.set_title('User Engagement', fontsize=13, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        filepath = self.output_dir / 'user_engagement.png'
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"Saved: {filepath}")
        plt.close()
    
    def plot_dashboard(self) -> None:
        """Create comprehensive dashboard plot."""
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        variants = self.variants
        colors = [self.colors[v] for v in variants]
        
        # 1. CTR Comparison
        ax1 = fig.add_subplot(gs[0, 0])
        ctrs = [self.metrics[v].ctr * 100 for v in variants]
        bars = ax1.bar(variants, ctrs, color=colors, alpha=0.8, edgecolor='black')
        for bar, ctr in zip(bars, ctrs):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{ctr:.2f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax1.set_ylabel('CTR (%)', fontweight='bold')
        ax1.set_title('Click-Through Rate', fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)
        
        # 2. Clicks vs Impressions
        ax2 = fig.add_subplot(gs[0, 1])
        x = np.arange(len(variants))
        width = 0.35
        clicks = [self.metrics[v].clicks for v in variants]
        impressions = [self.metrics[v].impressions for v in variants]
        ax2.bar(x - width/2, impressions, width, label='Impressions', alpha=0.8)
        ax2.bar(x + width/2, clicks, width, label='Clicks', alpha=0.8)
        ax2.set_ylabel('Count', fontweight='bold')
        ax2.set_title('Impressions vs Clicks', fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(variants)
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)
        
        # 3. Response Times
        ax3 = fig.add_subplot(gs[1, 0])
        response_times = [self.metrics[v].avg_response_time for v in variants]
        bars = ax3.bar(variants, response_times, color=colors, alpha=0.8, edgecolor='black')
        for bar, rt in zip(bars, response_times):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{rt:.1f}ms', ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax3.set_ylabel('Response Time (ms)', fontweight='bold')
        ax3.set_title('Average Response Time', fontweight='bold')
        ax3.grid(axis='y', alpha=0.3)
        
        # 4. User Counts
        ax4 = fig.add_subplot(gs[1, 1])
        users = [self.metrics[v].total_users for v in variants]
        bars = ax4.bar(variants, users, color=colors, alpha=0.8, edgecolor='black')
        for bar, user_count in zip(bars, users):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax4.set_ylabel('Total Users', fontweight='bold')
        ax4.set_title('User Distribution', fontweight='bold')
        ax4.grid(axis='y', alpha=0.3)
        
        # 5. Avg Clicks per User
        ax5 = fig.add_subplot(gs[2, 0])
        avg_clicks = [self.metrics[v].avg_clicks_per_user for v in variants]
        bars = ax5.bar(variants, avg_clicks, color=colors, alpha=0.8, edgecolor='black')
        for bar, clicks in zip(bars, avg_clicks):
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height,
                    f'{clicks:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax5.set_ylabel('Avg Clicks per User', fontweight='bold')
        ax5.set_title('User Engagement', fontweight='bold')
        ax5.grid(axis='y', alpha=0.3)
        
        # 6. Summary Statistics
        ax6 = fig.add_subplot(gs[2, 1])
        ax6.axis('off')
        
        summary_text = "EXPERIMENT SUMMARY\n" + "="*40 + "\n\n"
        if len(variants) == 2:
            v1_ctr = self.metrics[variants[0]].ctr
            v2_ctr = self.metrics[variants[1]].ctr
            improvement = (v2_ctr - v1_ctr) / v1_ctr * 100 if v1_ctr > 0 else 0
            winner = variants[1] if improvement > 0 else variants[0]
            
            summary_text += f"Variant Comparison:\n"
            summary_text += f"{variants[0]} CTR: {v1_ctr:.2%}\n"
            summary_text += f"{variants[1]} CTR: {v2_ctr:.2%}\n"
            summary_text += f"\nImprovement: {improvement:+.1f}%\n"
            summary_text += f"Winner: {winner}\n"
        
        ax6.text(0.1, 0.5, summary_text, fontsize=11, family='monospace',
                verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        fig.suptitle('A/B Test Results Dashboard', fontsize=16, fontweight='bold')
        
        filepath = self.output_dir / 'dashboard.png'
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"Saved: {filepath}")
        plt.close()
    
    def generate_all_plots(self) -> None:
        """Generate all visualization plots."""
        print("\nGenerating visualizations...")
        self.plot_ctr_comparison()
        self.plot_clicks_impressions()
        self.plot_response_times()
        self.plot_user_engagement()
        self.plot_dashboard()
        print(f"All plots saved to: {self.output_dir}")


def export_results(metrics: Dict[str, ExperimentMetrics], output_file: str) -> None:
    """Export results to JSON file."""
    results = {
        'timestamp': datetime.now().isoformat(),
        'variants': {}
    }
    
    for variant, metric in metrics.items():
        results['variants'][variant] = {
            'ctr': f"{metric.ctr:.4f}",
            'ctr_percent': f"{metric.ctr*100:.2f}%",
            'clicks': metric.clicks,
            'impressions': metric.impressions,
            'total_users': metric.total_users,
            'avg_clicks_per_user': f"{metric.avg_clicks_per_user:.2f}",
            'avg_response_time_ms': f"{metric.avg_response_time:.1f}"
        }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults exported to: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Analyze A/B test experiment results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze from JSON audit log
  python analyze_experiment_results.py --json logs/experiments.json --output-dir results
  
  # Analyze from MongoDB
  python analyze_experiment_results.py --mongodb mongodb://localhost:27017 --output-dir results
  
  # Generate dashboard and export results
  python analyze_experiment_results.py --json logs/experiments.json --output-dir results --export results.json
        """
    )
    
    parser.add_argument('--json', type=str, help='Path to JSON audit log file')
    parser.add_argument('--mongodb', type=str, help='MongoDB URI (requires pymongo)')
    parser.add_argument('--db-name', type=str, default='omnisearch', help='MongoDB database name')
    parser.add_argument('--output-dir', type=str, default='output', help='Output directory for plots')
    parser.add_argument('--export', type=str, help='Export results to JSON file')
    parser.add_argument('--no-plots', action='store_true', help='Skip generating plots')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.json and not args.mongodb:
        parser.error('Must specify either --json or --mongodb')
    
    # Load data
    analyzer = ExperimentAnalyzer()
    
    if args.json:
        analyzer.load_from_json(args.json)
    elif args.mongodb:
        if not MONGODB_AVAILABLE:
            print("ERROR: pymongo not installed. Install with: pip install pymongo")
            return
        analyzer.load_from_mongodb(args.mongodb, args.db_name)
    
    # Compute metrics
    metrics = analyzer.compute_metrics()
    
    # Print summary
    analyzer.print_summary(metrics)
    
    # Generate visualizations
    if not args.no_plots:
        visualizer = ExperimentVisualizer(metrics, args.output_dir)
        visualizer.generate_all_plots()
    
    # Export results
    if args.export:
        export_results(metrics, args.export)


if __name__ == '__main__':
    main()
