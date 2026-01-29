"""
Deploy CLIP model to AWS SageMaker endpoint.

Usage:
    python scripts/deploy_sagemaker_endpoint.py --deploy
    python scripts/deploy_sagemaker_endpoint.py --test
    python scripts/deploy_sagemaker_endpoint.py --autoscale
    python scripts/deploy_sagemaker_endpoint.py --delete
"""
import sagemaker
from sagemaker.pytorch.model import PyTorchModel
from sagemaker.model_monitor import DataCaptureConfig
import boto3
import json
import argparse
import logging
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
REGION = "us-east-1"
MODEL_NAME_PREFIX = "clip-embedding-model"
ENDPOINT_NAME = "omnisearch-clip-endpoint"
S3_BUCKET = "omnisearch-sagemaker-models"
ROLE_ARN = "arn:aws:iam::YOUR_ACCOUNT_ID:role/omnisearch-sagemaker-role"
INSTANCE_TYPE = "ml.g4dn.xlarge"  # GPU instance with 1x NVIDIA T4
INITIAL_INSTANCE_COUNT = 1

# Update ROLE_ARN before deploying!


def get_account_id():
    """Get AWS account ID."""
    sts = boto3.client("sts", region_name=REGION)
    return sts.get_caller_identity()["Account"]


def update_role_arn():
    """Update ROLE_ARN with current account ID."""
    global ROLE_ARN
    account_id = get_account_id()
    ROLE_ARN = f"arn:aws:iam::{account_id}:role/omnisearch-sagemaker-role"
    logger.info(f"Using role: {ROLE_ARN}")


def deploy_endpoint():
    """Deploy CLIP model to SageMaker endpoint."""
    
    update_role_arn()
    
    # Initialize SageMaker session
    sess = sagemaker.Session()
    
    logger.info("=" * 70)
    logger.info("🚀 CLIP Model Deployment to SageMaker")
    logger.info("=" * 70)
    logger.info(f"Region: {REGION}")
    logger.info(f"Bucket: {S3_BUCKET}")
    logger.info(f"Role: {ROLE_ARN}")
    logger.info(f"Instance type: {INSTANCE_TYPE}")
    logger.info(f"Initial instances: {INITIAL_INSTANCE_COUNT}")
    
    # Create PyTorch model
    logger.info("\n📦 Creating model...")
    
    model_name = f"{MODEL_NAME_PREFIX}-{int(time.time())}"
    
    pytorch_model = PyTorchModel(
        entry_point="inference.py",
        role=ROLE_ARN,
        model_data=f"s3://{S3_BUCKET}/clip-model/clip-model.tar.gz",
        framework_version="2.0",
        py_version="py310",
        sagemaker_session=sess,
        image_uri=None,  # Use SageMaker's pre-built image
        name=model_name,
    )
    
    # Enable data capture for monitoring
    logger.info("📊 Configuring data capture...")
    
    data_capture_config = DataCaptureConfig(
        enable_capture=True,
        sampling_percentage=10,
        destination_s3_uri=f"s3://{S3_BUCKET}/data-capture",
        capture_options=["Input", "Output"]
    )
    
    # Deploy endpoint
    logger.info("\n🚀 Deploying endpoint...")
    logger.info(f"This may take 5-10 minutes...")
    
    try:
        predictor = pytorch_model.deploy(
            initial_instance_count=INITIAL_INSTANCE_COUNT,
            instance_type=INSTANCE_TYPE,
            endpoint_name=ENDPOINT_NAME,
            data_capture_config=data_capture_config,
            wait=True
        )
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ Deployment Successful!")
        logger.info("=" * 70)
        logger.info(f"Endpoint name: {ENDPOINT_NAME}")
        logger.info(f"Model name: {model_name}")
        logger.info(f"Endpoint ARN: {predictor.endpoint}")
        logger.info(f"Instance type: {INSTANCE_TYPE}")
        logger.info(f"Initial instances: {INITIAL_INSTANCE_COUNT}")
        logger.info("\n📝 Next steps:")
        logger.info("  1. Test endpoint: python deploy_sagemaker_endpoint.py --test")
        logger.info("  2. Enable autoscaling: python deploy_sagemaker_endpoint.py --autoscale")
        logger.info("  3. Update FastAPI: Set USE_SAGEMAKER=true")
        
        return predictor
        
    except Exception as e:
        logger.error(f"\n❌ Deployment failed: {str(e)}")
        raise


def test_endpoint(endpoint_name: str = ENDPOINT_NAME):
    """Test endpoint with sample requests."""
    
    runtime = boto3.client("sagemaker-runtime", region_name=REGION)
    
    logger.info("=" * 70)
    logger.info("🧪 Testing SageMaker Endpoint")
    logger.info("=" * 70)
    
    # Test text embedding
    test_texts = [
        "A woman wearing a red hat",
        "A dog running in the park",
        "A sunset over the ocean"
    ]
    
    logger.info(f"\n📝 Testing with {len(test_texts)} text samples...\n")
    
    for i, text in enumerate(test_texts, 1):
        try:
            logger.info(f"Test {i}: '{text}'")
            
            response = runtime.invoke_endpoint(
                EndpointName=endpoint_name,
                ContentType="application/json",
                Body=json.dumps({
                    "type": "text",
                    "data": text,
                    "normalize": True
                })
            )
            
            result = json.loads(response["Body"].read())
            embedding = result["embedding"]
            dimension = result["dimension"]
            
            logger.info(f"  ✅ Success!")
            logger.info(f"  Dimension: {dimension}")
            logger.info(f"  First 5 values: {[f'{v:.4f}' for v in embedding[:5]]}")
            logger.info("")
            
        except Exception as e:
            logger.error(f"  ❌ Error: {str(e)}\n")
    
    logger.info("=" * 70)
    logger.info("✅ Tests Complete!")
    logger.info("=" * 70)


def configure_autoscaling(endpoint_name: str = ENDPOINT_NAME):
    """Configure auto-scaling for the endpoint."""
    
    logger.info("=" * 70)
    logger.info("📈 Configuring Auto-Scaling")
    logger.info("=" * 70)
    
    autoscaling = boto3.client("application-autoscaling", region_name=REGION)
    
    resource_id = f"endpoint/{endpoint_name}/variant/AllTraffic"
    
    logger.info(f"Resource: {resource_id}")
    
    try:
        # Register scalable target
        logger.info("\n1️⃣ Registering scalable target...")
        
        autoscaling.register_scalable_target(
            ServiceNamespace="sagemaker",
            ResourceId=resource_id,
            ScalableDimension="sagemaker:variant:DesiredInstanceCount",
            MinCapacity=1,
            MaxCapacity=4
        )
        
        logger.info("   ✅ Scalable target registered")
        
        # Create scaling policy
        logger.info("\n2️⃣ Creating scaling policy...")
        
        autoscaling.put_scaling_policy(
            PolicyName=f"{endpoint_name}-scaling-policy",
            ServiceNamespace="sagemaker",
            ResourceId=resource_id,
            ScalableDimension="sagemaker:variant:DesiredInstanceCount",
            PolicyType="TargetTrackingScaling",
            TargetTrackingScalingPolicyConfiguration={
                "TargetValue": 70.0,
                "PredefinedMetricSpecification": {
                    "PredefinedMetricType": "SageMakerVariantInvocationsPerInstance"
                },
                "ScaleOutCooldown": 300,
                "ScaleInCooldown": 600
            }
        )
        
        logger.info("   ✅ Scaling policy created")
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ Auto-Scaling Configured!")
        logger.info("=" * 70)
        logger.info(f"Target: 70% CPU utilization")
        logger.info(f"Min instances: 1")
        logger.info(f"Max instances: 4")
        logger.info(f"Scale-out cooldown: 5 minutes")
        logger.info(f"Scale-in cooldown: 10 minutes")
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        raise


def get_endpoint_info(endpoint_name: str = ENDPOINT_NAME):
    """Get endpoint information and status."""
    
    sm = boto3.client("sagemaker", region_name=REGION)
    cloudwatch = boto3.client("cloudwatch", region_name=REGION)
    
    logger.info("=" * 70)
    logger.info("📊 Endpoint Information")
    logger.info("=" * 70)
    
    try:
        # Get endpoint details
        response = sm.describe_endpoint(EndpointName=endpoint_name)
        
        variant = response["ProductionVariants"][0]
        
        logger.info(f"\nEndpoint: {response['EndpointName']}")
        logger.info(f"Status: {response['EndpointStatus']}")
        logger.info(f"ARN: {response['EndpointArn']}")
        logger.info(f"\nInstance Configuration:")
        logger.info(f"  Type: {variant['InstanceType']}")
        logger.info(f"  Current count: {variant['CurrentInstanceCount']}")
        logger.info(f"  Desired count: {variant['DesiredInstanceCount']}")
        logger.info(f"\nDates:")
        logger.info(f"  Created: {response['CreationTime']}")
        logger.info(f"  Modified: {response['LastModifiedTime']}")
        
        # Get CloudWatch metrics (last hour)
        from datetime import datetime, timedelta
        
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
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
            Statistics=["Sum"]
        )
        
        total_invocations = sum([d["Sum"] for d in response["Datapoints"]]) if response["Datapoints"] else 0
        
        logger.info(f"\nMetrics (last hour):")
        logger.info(f"  Total invocations: {int(total_invocations)}")
        
        logger.info("\n" + "=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")


def delete_endpoint(endpoint_name: str = ENDPOINT_NAME):
    """Delete endpoint and associated resources."""
    
    logger.info("=" * 70)
    logger.info("🗑️  Deleting Endpoint")
    logger.info("=" * 70)
    
    sm = boto3.client("sagemaker", region_name=REGION)
    
    try:
        # First, try to deregister from autoscaling
        try:
            autoscaling = boto3.client("application-autoscaling", region_name=REGION)
            autoscaling.deregister_scalable_target(
                ServiceNamespace="sagemaker",
                ResourceId=f"endpoint/{endpoint_name}/variant/AllTraffic",
                ScalableDimension="sagemaker:variant:DesiredInstanceCount"
            )
            logger.info("✅ Removed from autoscaling")
        except:
            pass
        
        # Delete endpoint
        logger.info(f"\nDeleting endpoint: {endpoint_name}...")
        sm.delete_endpoint(EndpointName=endpoint_name)
        
        # Wait for deletion
        logger.info("Waiting for deletion...")
        waiter = sm.get_waiter("endpoint_deleted")
        waiter.wait(EndpointName=endpoint_name)
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ Endpoint Deleted!")
        logger.info("=" * 70)
        
    except Exception as e:
        if "Could not find endpoint" in str(e):
            logger.info(f"Endpoint '{endpoint_name}' not found")
        else:
            logger.error(f"❌ Error: {str(e)}")


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
    
    for endpoint in response["Endpoints"]:
        logger.info(f"📍 {endpoint['EndpointName']}")
        logger.info(f"   Status: {endpoint['EndpointStatus']}")
        logger.info(f"   Created: {endpoint['CreationTime']}")
        logger.info("")


def main():
    """Main CLI interface."""
    
    parser = argparse.ArgumentParser(
        description="Deploy CLIP model to AWS SageMaker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deploy_sagemaker_endpoint.py --deploy          # Deploy endpoint
  python deploy_sagemaker_endpoint.py --test            # Test endpoint
  python deploy_sagemaker_endpoint.py --autoscale       # Enable autoscaling
  python deploy_sagemaker_endpoint.py --info            # Get endpoint info
  python deploy_sagemaker_endpoint.py --delete          # Delete endpoint
  python deploy_sagemaker_endpoint.py --list            # List all endpoints
        """
    )
    
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Deploy CLIP model to SageMaker endpoint"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test endpoint with sample requests"
    )
    
    parser.add_argument(
        "--autoscale",
        action="store_true",
        help="Configure auto-scaling for endpoint"
    )
    
    parser.add_argument(
        "--info",
        action="store_true",
        help="Get endpoint information and status"
    )
    
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete endpoint"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all SageMaker endpoints"
    )
    
    parser.add_argument(
        "--endpoint",
        type=str,
        default=ENDPOINT_NAME,
        help=f"Endpoint name (default: {ENDPOINT_NAME})"
    )
    
    args = parser.parse_args()
    
    try:
        if args.deploy:
            deploy_endpoint()
        elif args.test:
            test_endpoint(args.endpoint)
        elif args.autoscale:
            configure_autoscaling(args.endpoint)
        elif args.info:
            get_endpoint_info(args.endpoint)
        elif args.delete:
            delete_endpoint(args.endpoint)
        elif args.list:
            list_endpoints()
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Operation cancelled by user")
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
