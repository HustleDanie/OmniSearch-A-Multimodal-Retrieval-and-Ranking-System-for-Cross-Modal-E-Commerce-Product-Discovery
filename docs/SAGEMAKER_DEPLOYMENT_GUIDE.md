# AWS SageMaker CLIP Endpoint Deployment Guide

## Overview

This guide walks you through deploying the CLIP embedding model to AWS SageMaker and updating your embedding service to use the managed endpoint instead of local GPU resources.

**Benefits of SageMaker Endpoint:**
- **Scalability**: Auto-scaling based on traffic
- **Reliability**: Managed service with SLA
- **Cost-efficiency**: Pay only for usage
- **Easy updates**: Deploy new models without downtime
- **Multi-model hosting**: Host multiple CLIP variants simultaneously
- **Built-in monitoring**: CloudWatch metrics and alarms
- **A/B testing**: Route traffic between model versions

**Architecture:**
```
Local FastAPI → SageMaker Endpoint (managed CLIP model)
                ↓
         Auto-scaling instances
         (ML instances with GPU)
```

---

## Prerequisites

### AWS Account Setup

1. **AWS Account with permissions:**
   - `sagemaker:*` (SageMaker full access)
   - `s3:*` (S3 for model artifacts)
   - `iam:CreateRole` (IAM role creation)
   - `ecr:*` (ECR for Docker images)

2. **AWS CLI installed and configured:**
   ```bash
   pip install awscli
   aws configure
   ```

3. **Local development environment:**
   ```bash
   pip install boto3 sagemaker
   ```

### S3 Bucket

Create bucket for model artifacts:

```bash
aws s3 mb s3://omnisearch-sagemaker-models --region us-east-1
```

### IAM Role

Create SageMaker execution role:

```bash
# Save this as trust-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "sagemaker.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}

# Create role
aws iam create-role \
  --role-name omnisearch-sagemaker-role \
  --assume-role-policy-document file://trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name omnisearch-sagemaker-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess

aws iam attach-role-policy \
  --role-name omnisearch-sagemaker-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

---

## Step 1: Prepare Model Artifacts

### 1.1 Create Inference Script

Create `code/inference.py` to handle SageMaker inference requests:

```python
import json
import torch
import clip
import numpy as np
from typing import Dict, Any
import base64
from io import BytesIO
from PIL import Image

# Global model variables
model = None
preprocess = None
device = None

def model_fn(model_dir):
    """
    Load model for inference.
    Called once at endpoint startup.
    """
    global model, preprocess, device
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Loading CLIP model on {device}...")
    
    # Load CLIP model
    model, preprocess = clip.load("ViT-B/32", device=device)
    model.eval()
    
    print("✓ Model loaded successfully")
    return model

def input_fn(request_body, content_type='application/json'):
    """
    Parse input from SageMaker runtime.
    """
    if content_type == 'application/json':
        input_data = json.loads(request_body)
        return input_data
    else:
        raise ValueError(f"Unsupported content type: {content_type}")

def predict_fn(input_data: Dict[str, Any], model):
    """
    Run prediction on input data.
    
    Input format:
    {
        "type": "text" or "image",
        "data": "text string" or "base64 encoded image",
        "normalize": true
    }
    """
    global device, preprocess
    
    input_type = input_data.get("type", "text")
    data = input_data.get("data")
    normalize = input_data.get("normalize", True)
    
    with torch.no_grad():
        if input_type == "text":
            # Embed text
            text_tokens = clip.tokenize([data]).to(device)
            embedding = model.encode_text(text_tokens)
            
        elif input_type == "image":
            # Decode base64 image
            image_data = base64.b64decode(data)
            image = Image.open(BytesIO(image_data)).convert("RGB")
            image_tensor = preprocess(image).unsqueeze(0).to(device)
            embedding = model.encode_image(image_tensor)
        
        else:
            raise ValueError(f"Unknown type: {input_type}")
        
        # Normalize if requested
        if normalize:
            embedding = embedding / embedding.norm(dim=-1, keepdim=True)
        
        # Convert to numpy and remove batch dimension
        embedding = embedding.cpu().numpy()[0].tolist()
    
    return embedding

def output_fn(prediction, accept='application/json'):
    """
    Format prediction output.
    """
    if accept == 'application/json':
        return json.dumps({
            "embedding": prediction,
            "dimension": len(prediction)
        }), accept
    else:
        raise ValueError(f"Unsupported accept type: {accept}")
```

### 1.2 Create Requirements File

Create `code/requirements.txt`:

```
torch==2.0.0
torchvision==0.15.0
clip @ git+https://github.com/openai/CLIP.git
Pillow==10.0.0
numpy==1.24.0
```

### 1.3 Package Model Artifacts

```bash
# Create directory structure
mkdir -p code

# Create files (see Step 1.1 and 1.2)
# ... place inference.py and requirements.txt in code/ directory

# Create tarball
tar -czf clip-model.tar.gz code/

# Upload to S3
aws s3 cp clip-model.tar.gz s3://omnisearch-sagemaker-models/clip-model/
```

---

## Step 2: Deploy to SageMaker

### 2.1 Create Docker Image (Optional but Recommended)

For better control, create a custom Docker image:

```dockerfile
FROM 246618743249.dkr.ecr.us-east-1.amazonaws.com/sagemaker-pytorch:2.0-cpu-py310

# Install CLIP
RUN pip install git+https://github.com/openai/CLIP.git

# Copy inference code
COPY code /opt/ml/code

ENV SAGEMAKER_PROGRAM inference.py

EXPOSE 8080
```

Build and push:

```bash
# Build image
docker build -t omnisearch-clip:latest .

# Tag for ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

docker tag omnisearch-clip:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/omnisearch-clip:latest

docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/omnisearch-clip:latest
```

### 2.2 Deploy Using SageMaker Python SDK

Create `scripts/deploy_sagemaker_endpoint.py`:

```python
"""
Deploy CLIP model to AWS SageMaker endpoint.
Run this script to create or update the endpoint.
"""
import sagemaker
from sagemaker.pytorch.model import PyTorchModel
from sagemaker.model_monitor import DataCaptureConfig
import boto3
from datetime import datetime

# Configuration
REGION = "us-east-1"
MODEL_NAME = "clip-embedding-model"
ENDPOINT_NAME = "omnisearch-clip-endpoint"
S3_BUCKET = "omnisearch-sagemaker-models"
ROLE_ARN = "arn:aws:iam::YOUR_ACCOUNT_ID:role/omnisearch-sagemaker-role"
INSTANCE_TYPE = "ml.g4dn.xlarge"  # GPU instance with 1x NVIDIA T4
INITIAL_INSTANCE_COUNT = 1

def deploy_endpoint():
    """Deploy CLIP model to SageMaker endpoint."""
    
    # Initialize SageMaker session
    sess = sagemaker.Session()
    
    print(f"Region: {REGION}")
    print(f"Bucket: {S3_BUCKET}")
    print(f"Role ARN: {ROLE_ARN}")
    
    # Create PyTorch model
    pytorch_model = PyTorchModel(
        entry_point="inference.py",
        role=ROLE_ARN,
        model_data=f"s3://{S3_BUCKET}/clip-model/clip-model.tar.gz",
        framework_version="2.0",
        py_version="py310",
        sagemaker_session=sess,
        image_uri=None,  # Use SageMaker's pre-built image
        name=MODEL_NAME,
    )
    
    # Enable data capture for monitoring
    data_capture_config = DataCaptureConfig(
        enable_capture=True,
        sampling_percentage=10,
        destination_s3_uri=f"s3://{S3_BUCKET}/data-capture",
        capture_options=["Input", "Output"]
    )
    
    # Deploy endpoint
    print("\n🚀 Deploying CLIP model to SageMaker...")
    predictor = pytorch_model.deploy(
        initial_instance_count=INITIAL_INSTANCE_COUNT,
        instance_type=INSTANCE_TYPE,
        endpoint_name=ENDPOINT_NAME,
        data_capture_config=data_capture_config,
    )
    
    print(f"✅ Endpoint deployed successfully!")
    print(f"Endpoint name: {ENDPOINT_NAME}")
    print(f"Endpoint ARN: {predictor.endpoint}")
    print(f"Instance type: {INSTANCE_TYPE}")
    print(f"Initial instances: {INITIAL_INSTANCE_COUNT}")
    
    return predictor

def test_endpoint(endpoint_name: str):
    """Test endpoint with sample request."""
    
    runtime = boto3.client("sagemaker-runtime", region_name=REGION)
    
    # Test text embedding
    test_text = "A woman wearing a red hat"
    
    print(f"\n🧪 Testing endpoint with text: '{test_text}'")
    
    response = runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType="application/json",
        Body=json.dumps({
            "type": "text",
            "data": test_text,
            "normalize": True
        })
    )
    
    result = json.loads(response["Body"].read())
    embedding = result["embedding"]
    dimension = len(embedding)
    
    print(f"✅ Embedding generated successfully!")
    print(f"Embedding dimension: {dimension}")
    print(f"Sample values: {embedding[:5]}...")
    
    return embedding

def configure_autoscaling(endpoint_name: str):
    """Configure auto-scaling for the endpoint."""
    
    autoscaling = boto3.client("application-autoscaling")
    
    # Register scalable target
    autoscaling.register_scalable_target(
        ServiceNamespace="sagemaker",
        ResourceId=f"endpoint/{endpoint_name}/variant/AllTraffic",
        ScalableDimension="sagemaker:variant:DesiredInstanceCount",
        MinCapacity=1,
        MaxCapacity=4
    )
    
    # Create scaling policy
    autoscaling.put_scaling_policy(
        PolicyName=f"{endpoint_name}-scaling-policy",
        ServiceNamespace="sagemaker",
        ResourceId=f"endpoint/{endpoint_name}/variant/AllTraffic",
        ScalableDimension="sagemaker:variant:DesiredInstanceCount",
        PolicyType="TargetTrackingScaling",
        TargetTrackingScalingPolicyConfiguration={
            "TargetValue": 70.0,  # Target 70% CPU utilization
            "PredefinedMetricSpecification": {
                "PredefinedMetricType": "SageMakerVariantInvocationsPerInstance"
            },
            "ScaleOutCooldown": 300,
            "ScaleInCooldown": 600
        }
    )
    
    print(f"✅ Auto-scaling configured for {endpoint_name}")
    print(f"   Target: 70% CPU utilization")
    print(f"   Min instances: 1")
    print(f"   Max instances: 4")

if __name__ == "__main__":
    import json
    
    # Deploy endpoint
    predictor = deploy_endpoint()
    
    # Test endpoint
    # test_endpoint(ENDPOINT_NAME)
    
    # Configure auto-scaling
    # configure_autoscaling(ENDPOINT_NAME)
```

Run deployment:

```bash
python scripts/deploy_sagemaker_endpoint.py
```

---

## Step 3: Update Embedding Service

### 3.1 Create SageMaker Embedding Service

Create `services/sagemaker_clip_service.py`:

```python
"""
CLIP Embedding Service using AWS SageMaker endpoint.
Provides text and image embedding functionality with remote inference.
"""
import boto3
import numpy as np
import json
import base64
from typing import Optional
from io import BytesIO
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class SageMakerCLIPEmbeddingService:
    """
    Service for generating CLIP embeddings using AWS SageMaker endpoint.
    
    Replaces local GPU inference with managed SageMaker endpoint.
    """
    
    def __init__(
        self,
        endpoint_name: str,
        region_name: str = "us-east-1",
        normalize: bool = True
    ):
        """
        Initialize SageMaker CLIP embedding service.
        
        Args:
            endpoint_name: Name of SageMaker endpoint
            region_name: AWS region
            normalize: Whether to normalize embeddings (default: True)
        """
        self.endpoint_name = endpoint_name
        self.region_name = region_name
        self.normalize = normalize
        
        # Initialize SageMaker runtime client
        self.runtime = boto3.client(
            "sagemaker-runtime",
            region_name=region_name
        )
        
        # Initialize SageMaker client for endpoint info
        self.sm_client = boto3.client(
            "sagemaker",
            region_name=region_name
        )
        
        # Verify endpoint exists
        self._verify_endpoint()
        
        logger.info(f"✓ SageMaker CLIP service initialized")
        logger.info(f"  Endpoint: {endpoint_name}")
        logger.info(f"  Region: {region_name}")
    
    def _verify_endpoint(self):
        """Verify endpoint exists and is in service."""
        try:
            response = self.sm_client.describe_endpoint(
                EndpointName=self.endpoint_name
            )
            
            status = response["EndpointStatus"]
            if status != "InService":
                raise RuntimeError(
                    f"Endpoint {self.endpoint_name} is not in service. "
                    f"Status: {status}"
                )
            
            logger.info(f"Endpoint status: {status}")
            
        except self.sm_client.exceptions.ValidationException:
            raise ValueError(
                f"Endpoint '{self.endpoint_name}' does not exist. "
                f"Deploy endpoint using deploy_sagemaker_endpoint.py"
            )
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate normalized embedding vector from text.
        
        Args:
            text: Input text string to embed
            
        Returns:
            Normalized numpy array of shape (embedding_dim,)
        """
        payload = {
            "type": "text",
            "data": text,
            "normalize": self.normalize
        }
        
        response = self.runtime.invoke_endpoint(
            EndpointName=self.endpoint_name,
            ContentType="application/json",
            Body=json.dumps(payload)
        )
        
        result = json.loads(response["Body"].read())
        embedding = np.array(result["embedding"])
        
        return embedding
    
    def embed_image(self, image_path: str) -> np.ndarray:
        """
        Generate normalized embedding vector from image.
        
        Args:
            image_path: Path to image file or S3 URI
            
        Returns:
            Normalized numpy array of shape (embedding_dim,)
        """
        # Load image
        if image_path.startswith("s3://"):
            image_data = self._load_image_from_s3(image_path)
        else:
            with open(image_path, "rb") as f:
                image_data = f.read()
        
        # Encode as base64
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        
        payload = {
            "type": "image",
            "data": image_base64,
            "normalize": self.normalize
        }
        
        response = self.runtime.invoke_endpoint(
            EndpointName=self.endpoint_name,
            ContentType="application/json",
            Body=json.dumps(payload)
        )
        
        result = json.loads(response["Body"].read())
        embedding = np.array(result["embedding"])
        
        return embedding
    
    def _load_image_from_s3(self, s3_uri: str) -> bytes:
        """Load image from S3 URI (s3://bucket/key)."""
        s3_client = boto3.client("s3", region_name=self.region_name)
        
        # Parse S3 URI
        parts = s3_uri.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]
        
        # Download image
        response = s3_client.get_object(Bucket=bucket, Key=key)
        image_data = response["Body"].read()
        
        return image_data
    
    def embed_batch(self, texts: list, batch_size: int = 10) -> np.ndarray:
        """
        Embed multiple texts efficiently.
        
        Args:
            texts: List of text strings
            batch_size: Process in batches (not currently batched on endpoint)
            
        Returns:
            Numpy array of shape (len(texts), embedding_dim)
        """
        embeddings = []
        
        for text in texts:
            embedding = self.embed_text(text)
            embeddings.append(embedding)
        
        return np.array(embeddings)
    
    def get_endpoint_metrics(self):
        """Get endpoint metrics and status."""
        response = self.sm_client.describe_endpoint(
            EndpointName=self.endpoint_name
        )
        
        metrics = {
            "endpoint_name": response["EndpointName"],
            "endpoint_status": response["EndpointStatus"],
            "instance_type": response["ProductionVariants"][0]["InstanceType"],
            "current_instance_count": response["ProductionVariants"][0]["CurrentInstanceCount"],
            "creation_time": response["CreationTime"].isoformat(),
            "last_modified_time": response["LastModifiedTime"].isoformat(),
        }
        
        return metrics

```

### 3.2 Update FastAPI to Use SageMaker

Update `api/embedding.py` to support both local and SageMaker:

```python
"""
Embedding API endpoint with support for local and SageMaker inference.
"""
from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

# Initialize embedding service based on environment
USE_SAGEMAKER = os.getenv("USE_SAGEMAKER", "false").lower() == "true"

if USE_SAGEMAKER:
    from services.sagemaker_clip_service import SageMakerCLIPEmbeddingService
    
    ENDPOINT_NAME = os.getenv("SAGEMAKER_ENDPOINT_NAME", "omnisearch-clip-endpoint")
    REGION = os.getenv("AWS_REGION", "us-east-1")
    
    embedding_service = SageMakerCLIPEmbeddingService(
        endpoint_name=ENDPOINT_NAME,
        region_name=REGION
    )
    logger.info(f"Using SageMaker endpoint: {ENDPOINT_NAME}")
else:
    from services.clip_service import CLIPEmbeddingService
    
    MODEL_NAME = os.getenv("CLIP_MODEL", "ViT-B/32")
    embedding_service = CLIPEmbeddingService(model_name=MODEL_NAME)
    logger.info(f"Using local CLIP model: {MODEL_NAME}")

router = FastAPI()

class TextEmbeddingRequest(BaseModel):
    text: str

class TextEmbeddingResponse(BaseModel):
    embedding: list
    dimension: int

@router.post("/embed/text", response_model=TextEmbeddingResponse)
async def embed_text(request: TextEmbeddingRequest):
    """Generate embedding for text."""
    try:
        embedding = embedding_service.embed_text(request.text)
        return TextEmbeddingResponse(
            embedding=embedding.tolist(),
            dimension=len(embedding)
        )
    except Exception as e:
        logger.error(f"Embedding error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/embed/image", response_model=TextEmbeddingResponse)
async def embed_image(file: UploadFile = File(...)):
    """Generate embedding for image."""
    try:
        # Save temporary file
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())
        
        embedding = embedding_service.embed_image(temp_path)
        
        # Clean up
        os.remove(temp_path)
        
        return TextEmbeddingResponse(
            embedding=embedding.tolist(),
            dimension=len(embedding)
        )
    except Exception as e:
        logger.error(f"Image embedding error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health():
    """Health check endpoint."""
    try:
        if USE_SAGEMAKER:
            metrics = embedding_service.get_endpoint_metrics()
            return {
                "status": "healthy",
                "service": "sagemaker",
                "endpoint": metrics["endpoint_name"],
                "endpoint_status": metrics["endpoint_status"]
            }
        else:
            return {
                "status": "healthy",
                "service": "local",
                "device": embedding_service.device
            }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
```

---

## Step 4: Configuration

### 4.1 Update .env Files

For local development (no SageMaker):

```env
USE_SAGEMAKER=false
CLIP_MODEL=ViT-B/32
```

For SageMaker deployment:

```env
USE_SAGEMAKER=true
SAGEMAKER_ENDPOINT_NAME=omnisearch-clip-endpoint
AWS_REGION=us-east-1
```

### 4.2 Update Docker Environment

Update `docker-compose.yml` for SageMaker:

```yaml
fastapi:
  environment:
    - USE_SAGEMAKER=false  # Set to true for production
    - SAGEMAKER_ENDPOINT_NAME=omnisearch-clip-endpoint
    - AWS_REGION=us-east-1
    - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
    - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
```

Or update `.env.docker`:

```env
USE_SAGEMAKER=true
SAGEMAKER_ENDPOINT_NAME=omnisearch-clip-endpoint
AWS_REGION=us-east-1
```

---

## Step 5: Monitoring & Management

### 5.1 Monitor Endpoint Performance

Create `scripts/monitor_sagemaker_endpoint.py`:

```python
"""
Monitor SageMaker endpoint performance and metrics.
"""
import boto3
import time
from datetime import datetime, timedelta

def get_cloudwatch_metrics(endpoint_name: str, hours: int = 1):
    """Get CloudWatch metrics for endpoint."""
    
    cloudwatch = boto3.client("cloudwatch", region_name="us-east-1")
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    end_time = datetime.utcnow()
    
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
        Statistics=["Sum"]
    )
    
    print(f"\n📊 Endpoint Metrics (last {hours} hour(s)):")
    print(f"Endpoint: {endpoint_name}")
    print(f"Time range: {start_time} to {end_time}")
    
    if response["Datapoints"]:
        total_invocations = sum([d["Sum"] for d in response["Datapoints"]])
        print(f"Total invocations: {int(total_invocations)}")
    
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
        Statistics=["Average", "Maximum"]
    )
    
    if response["Datapoints"]:
        avg_latency = sum([d["Average"] for d in response["Datapoints"]]) / len(response["Datapoints"])
        max_latency = max([d["Maximum"] for d in response["Datapoints"]])
        print(f"Average latency: {avg_latency:.2f}ms")
        print(f"Max latency: {max_latency:.2f}ms")

def list_endpoints():
    """List all SageMaker endpoints."""
    
    sm = boto3.client("sagemaker", region_name="us-east-1")
    
    response = sm.list_endpoints()
    
    print("\n📋 SageMaker Endpoints:")
    for endpoint in response["Endpoints"]:
        print(f"  - {endpoint['EndpointName']}")
        print(f"    Status: {endpoint['EndpointStatus']}")
        print(f"    Creation time: {endpoint['CreationTime']}")

if __name__ == "__main__":
    endpoint_name = "omnisearch-clip-endpoint"
    
    get_cloudwatch_metrics(endpoint_name, hours=1)
    list_endpoints()
```

### 5.2 Update Endpoint Model

Deploy new model version without downtime:

```python
"""
Update endpoint to new model version.
"""
import boto3

def update_endpoint(endpoint_name: str, new_model_s3_path: str):
    """Create new model and update endpoint."""
    
    sm = boto3.client("sagemaker", region_name="us-east-1")
    
    # Create new model
    model_name = f"clip-{int(time.time())}"
    
    sm.create_model(
        ModelName=model_name,
        PrimaryContainer={
            "Image": "<ECR_URI>/omnisearch-clip:latest",
            "ModelDataUrl": new_model_s3_path,
        },
        ExecutionRoleArn="arn:aws:iam::YOUR_ACCOUNT_ID:role/omnisearch-sagemaker-role"
    )
    
    # Create endpoint configuration
    config_name = f"clip-config-{int(time.time())}"
    
    sm.create_endpoint_config(
        EndpointConfigName=config_name,
        ProductionVariants=[
            {
                "VariantName": "Primary",
                "ModelName": model_name,
                "InstanceType": "ml.g4dn.xlarge",
                "InitialInstanceCount": 1
            }
        ]
    )
    
    # Update endpoint
    sm.update_endpoint(
        EndpointName=endpoint_name,
        EndpointConfigName=config_name
    )
    
    print(f"✅ Endpoint {endpoint_name} updated to model {model_name}")
    print(f"   New model is now serving traffic")
```

---

## Troubleshooting

### Issue: "Endpoint not found"

**Solution:**
```bash
# Check endpoint exists
aws sagemaker describe-endpoint --endpoint-name omnisearch-clip-endpoint

# List all endpoints
aws sagemaker list-endpoints
```

### Issue: Endpoint stuck in "Creating" status

**Solution:**
```bash
# Check endpoint logs
aws logs tail /aws/sagemaker/Endpoints/omnisearch-clip-endpoint --follow

# Delete and redeploy if necessary
aws sagemaker delete-endpoint --endpoint-name omnisearch-clip-endpoint
```

### Issue: High latency or timeouts

**Solution:**
- Increase model invoke timeout in FastAPI
- Enable endpoint auto-scaling
- Check CloudWatch metrics for capacity issues
- Upgrade to larger instance type (ml.g4dn.2xlarge)

### Issue: AWS credential errors

**Solution:**
```bash
# Verify credentials
aws sts get-caller-identity

# Set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

---

## Cost Estimation

### SageMaker On-Demand Pricing (US-East-1)

| Instance Type | Price/Hour | Daily | Monthly |
|---------------|-----------|-------|---------|
| ml.g4dn.xlarge | $0.81 | $19.44 | $583 |
| ml.g4dn.2xlarge | $1.71 | $41.04 | $1,231 |
| ml.g4dn.12xlarge | $10.29 | $246.96 | $7,409 |

### Cost Optimization

1. **Use Savings Plans:** 20-40% discount with 1-3 year commitment
2. **Auto-scaling:** Scale down to 1 instance during off-peak
3. **Spot Instances:** 70% discount but with interruption risk
4. **Data transfer:** Keep embedding service in same region

### Example: 1M requests/month

```
Requests: 1,000,000
Average latency: 500ms
Concurrent users: 5
Required capacity: 1 x ml.g4dn.xlarge
Monthly cost: ~$600
Cost per 1000 requests: $0.60
```

---

## Next Steps

1. **Deploy SageMaker endpoint** - Run `deploy_sagemaker_endpoint.py`
2. **Update FastAPI** - Set `USE_SAGEMAKER=true`
3. **Update Docker Compose** - Add AWS credentials
4. **Monitor endpoint** - Run `monitor_sagemaker_endpoint.py`
5. **Load test** - Use existing load testing tools
6. **Configure auto-scaling** - Adjust for your traffic patterns

---

## Resources

- [AWS SageMaker Documentation](https://docs.aws.amazon.com/sagemaker/)
- [SageMaker Python SDK](https://sagemaker.readthedocs.io/)
- [PyTorch on SageMaker](https://docs.aws.amazon.com/sagemaker/latest/dg/pytorch.html)
- [CLIP Repository](https://github.com/openai/CLIP)
- [SageMaker Pricing](https://aws.amazon.com/sagemaker/pricing/)
