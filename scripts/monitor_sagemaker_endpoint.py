"""
Monitor SageMaker endpoint performance and metrics.

Usage:
    python scripts/monitor_sagemaker_endpoint.py --endpoint omnisearch-clip-endpoint
    python scripts/monitor_sagemaker_endpoint.py --watch  # Real-time monitoring
"""
import boto3
import json
import argparse
import logging
from datetime import datetime, timedelta
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REGION = "us-east-1"


def get_endpoint_status(endpoint_name: str):
    """Get endpoint status."""
    
    sm = boto3.client("sagemaker", region_name=REGION)
    
    response = sm.describe_endpoint(EndpointName=endpoint_name)
    
    variant = response["ProductionVariants"][0]
    
    status = {
        "endpoint_name": response["EndpointName"],
        "status": response["EndpointStatus"],
        "instance_type": variant["InstanceType"],
        "current_instances": variant["CurrentInstanceCount"],
        "desired_instances": variant["DesiredInstanceCount"],
        "created": response["CreationTime"].isoformat(),
        "modified": response["LastModifiedTime"].isoformat(),
    }
    
    return status


def get_cloudwatch_metrics(endpoint_name: str, hours: int = 1):
    """Get CloudWatch metrics for endpoint."""
    
    cloudwatch = boto3.client("cloudwatch", region_name=REGION)
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    end_time = datetime.utcnow()
    
    metrics = {}
    
    # Get invocation count
    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/SageMaker",
        MetricName="ModelInvocations",
        Dimensions=[
            {"Name": "EndpointName", "Value": endpoint_name},
            {"Name": "VariantName", "Value": "AllTraffic"}
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=300,
        Statistics=["Sum", "SampleCount"]
    )
    
    if response["Datapoints"]:
        total_invocations = sum([d["Sum"] for d in response["Datapoints"]])
        metrics["total_invocations"] = int(total_invocations)
        metrics["data_points"] = len(response["Datapoints"])
    else:
        metrics["total_invocations"] = 0
        metrics["data_points"] = 0
    
    # Get model latency
    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/SageMaker",
        MetricName="ModelLatency",
        Dimensions=[
            {"Name": "EndpointName", "Value": endpoint_name},
            {"Name": "VariantName", "Value": "AllTraffic"}
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=300,
        Statistics=["Average", "Maximum", "Minimum"]
    )
    
    if response["Datapoints"]:
        latencies = [d["Average"] for d in response["Datapoints"]]
        metrics["avg_latency_ms"] = round(sum(latencies) / len(latencies), 2)
        metrics["max_latency_ms"] = round(max([d["Maximum"] for d in response["Datapoints"]]), 2)
        metrics["min_latency_ms"] = round(min([d["Minimum"] for d in response["Datapoints"]]), 2)
    
    # Get model invocation errors (if any)
    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/SageMaker",
        MetricName="ModelInvocationErrors",
        Dimensions=[
            {"Name": "EndpointName", "Value": endpoint_name},
            {"Name": "VariantName", "Value": "AllTraffic"}
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=300,
        Statistics=["Sum"]
    )
    
    if response["Datapoints"]:
        total_errors = sum([d["Sum"] for d in response["Datapoints"]])
        metrics["total_errors"] = int(total_errors)
    else:
        metrics["total_errors"] = 0
    
    metrics["time_period_hours"] = hours
    metrics["start_time"] = start_time.isoformat()
    metrics["end_time"] = end_time.isoformat()
    
    return metrics


def print_status(endpoint_name: str):
    """Print endpoint status."""
    
    logger.info("=" * 70)
    logger.info(f"🔍 Endpoint Status: {endpoint_name}")
    logger.info("=" * 70)
    
    try:
        status = get_endpoint_status(endpoint_name)
        
        logger.info(f"\nEndpoint: {status['endpoint_name']}")
        logger.info(f"Status: {status['status']}")
        logger.info(f"\nInstance Configuration:")
        logger.info(f"  Type: {status['instance_type']}")
        logger.info(f"  Current instances: {status['current_instances']}")
        logger.info(f"  Desired instances: {status['desired_instances']}")
        logger.info(f"\nDates:")
        logger.info(f"  Created: {status['created']}")
        logger.info(f"  Modified: {status['modified']}")
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")


def print_metrics(endpoint_name: str, hours: int = 1):
    """Print endpoint metrics."""
    
    logger.info("=" * 70)
    logger.info(f"📊 Metrics (last {hours} hour(s)): {endpoint_name}")
    logger.info("=" * 70)
    
    try:
        metrics = get_cloudwatch_metrics(endpoint_name, hours)
        
        logger.info(f"\nTime period: {metrics['start_time']} to {metrics['end_time']}")
        logger.info(f"\nInvocations:")
        logger.info(f"  Total: {metrics['total_invocations']}")
        logger.info(f"  Errors: {metrics['total_errors']}")
        
        if metrics['total_invocations'] > 0:
            error_rate = (metrics['total_errors'] / metrics['total_invocations']) * 100
            logger.info(f"  Error rate: {error_rate:.2f}%")
        
        logger.info(f"\nLatency:")
        if 'avg_latency_ms' in metrics:
            logger.info(f"  Average: {metrics['avg_latency_ms']}ms")
            logger.info(f"  Min: {metrics['min_latency_ms']}ms")
            logger.info(f"  Max: {metrics['max_latency_ms']}ms")
        else:
            logger.info(f"  No data available")
        
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")


def watch_endpoint(endpoint_name: str, interval: int = 60):
    """Watch endpoint metrics in real-time."""
    
    logger.info(f"👀 Watching endpoint: {endpoint_name}")
    logger.info(f"Update interval: {interval} seconds")
    logger.info("Press Ctrl+C to stop\n")
    
    try:
        while True:
            print("\033[2J\033[H")  # Clear screen
            
            logger.info(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print_status(endpoint_name)
            print_metrics(endpoint_name, hours=1)
            
            logger.info(f"Next update in {interval} seconds... (Press Ctrl+C to stop)")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logger.info("\n\n✋ Monitoring stopped")


def list_endpoints():
    """List all SageMaker endpoints."""
    
    sm = boto3.client("sagemaker", region_name=REGION)
    
    logger.info("=" * 70)
    logger.info("📋 SageMaker Endpoints")
    logger.info("=" * 70)
    
    response = sm.list_endpoints()
    
    if not response["Endpoints"]:
        logger.info("No endpoints found")
        return
    
    logger.info(f"\n{len(response['Endpoints'])} endpoint(s) found:\n")
    
    for i, endpoint in enumerate(response["Endpoints"], 1):
        logger.info(f"{i}. {endpoint['EndpointName']}")
        logger.info(f"   Status: {endpoint['EndpointStatus']}")
        logger.info(f"   Modified: {endpoint['LastModifiedTime']}")
        logger.info("")


def export_metrics(endpoint_name: str, hours: int = 24, output_file: str = "metrics.json"):
    """Export metrics to JSON file."""
    
    logger.info(f"📤 Exporting metrics to {output_file}...")
    
    try:
        status = get_endpoint_status(endpoint_name)
        metrics = get_cloudwatch_metrics(endpoint_name, hours)
        
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "metrics": metrics
        }
        
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"✅ Metrics exported successfully to {output_file}")
        logger.info(f"Size: {len(json.dumps(data))} bytes")
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")


def main():
    """Main CLI interface."""
    
    parser = argparse.ArgumentParser(
        description="Monitor AWS SageMaker CLIP endpoint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python monitor_sagemaker_endpoint.py --endpoint omnisearch-clip-endpoint
  python monitor_sagemaker_endpoint.py --watch
  python monitor_sagemaker_endpoint.py --export metrics.json --hours 24
  python monitor_sagemaker_endpoint.py --list
        """
    )
    
    parser.add_argument(
        "--endpoint",
        type=str,
        default="omnisearch-clip-endpoint",
        help="Endpoint name"
    )
    
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch endpoint in real-time"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Watch interval in seconds (default: 60)"
    )
    
    parser.add_argument(
        "--hours",
        type=int,
        default=1,
        help="Hours to look back (default: 1)"
    )
    
    parser.add_argument(
        "--export",
        type=str,
        help="Export metrics to JSON file"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all endpoints"
    )
    
    args = parser.parse_args()
    
    try:
        if args.watch:
            watch_endpoint(args.endpoint, args.interval)
        elif args.list:
            list_endpoints()
        elif args.export:
            export_metrics(args.endpoint, args.hours, args.export)
        else:
            print_status(args.endpoint)
            print_metrics(args.endpoint, args.hours)
            
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Operation cancelled")
    except Exception as e:
        logger.error(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
