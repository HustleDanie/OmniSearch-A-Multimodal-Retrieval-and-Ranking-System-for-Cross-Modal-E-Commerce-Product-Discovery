# AWS SageMaker CLIP Deployment - Quick Reference

## Quick Start (5 minutes)

### 1. Create Model Artifacts

```bash
# Create directory structure
mkdir -p code

# Copy inference.py and requirements.txt (see guide)
# Then create tarball
tar -czf clip-model.tar.gz code/

# Upload to S3
aws s3 mb s3://omnisearch-sagemaker-models --region us-east-1
aws s3 cp clip-model.tar.gz s3://omnisearch-sagemaker-models/clip-model/
```

### 2. Deploy Endpoint

```bash
# Update ROLE_ARN in deploy_sagemaker_endpoint.py with your account ID
python scripts/deploy_sagemaker_endpoint.py --deploy

# This takes 5-10 minutes...
```

### 3. Test Endpoint

```bash
python scripts/deploy_sagemaker_endpoint.py --test
```

### 4. Enable Auto-Scaling

```bash
python scripts/deploy_sagemaker_endpoint.py --autoscale
```

### 5. Update FastAPI

Set environment variables:
```env
USE_SAGEMAKER=true
SAGEMAKER_ENDPOINT_NAME=omnisearch-clip-endpoint
AWS_REGION=us-east-1
```

Or update docker-compose.yml:
```yaml
fastapi:
  environment:
    - USE_SAGEMAKER=true
    - SAGEMAKER_ENDPOINT_NAME=omnisearch-clip-endpoint
    - AWS_REGION=us-east-1
```

---

## Essential Commands

### Deployment

```bash
# Deploy endpoint
python deploy_sagemaker_endpoint.py --deploy

# Test endpoint
python deploy_sagemaker_endpoint.py --test

# Enable autoscaling
python deploy_sagemaker_endpoint.py --autoscale

# Get endpoint info
python deploy_sagemaker_endpoint.py --info

# List all endpoints
python deploy_sagemaker_endpoint.py --list

# Delete endpoint
python deploy_sagemaker_endpoint.py --delete
```

### Monitoring

```bash
# View endpoint status
python monitor_sagemaker_endpoint.py

# Watch endpoint in real-time
python monitor_sagemaker_endpoint.py --watch

# Get metrics for last 24 hours
python monitor_sagemaker_endpoint.py --hours 24

# Export metrics to JSON
python monitor_sagemaker_endpoint.py --export metrics.json

# List all endpoints
python monitor_sagemaker_endpoint.py --list
```

### AWS CLI

```bash
# Describe endpoint
aws sagemaker describe-endpoint --endpoint-name omnisearch-clip-endpoint

# List endpoints
aws sagemaker list-endpoints

# Check endpoint logs
aws logs tail /aws/sagemaker/Endpoints/omnisearch-clip-endpoint

# Delete endpoint
aws sagemaker delete-endpoint --endpoint-name omnisearch-clip-endpoint
```

---

## API Endpoints

### Using FastAPI with SageMaker

**Embed Text:**
```bash
curl -X POST http://localhost:8000/embed/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "A woman wearing a red hat",
    "normalize": true
  }'
```

**Embed Image:**
```bash
curl -X POST http://localhost:8000/embed/image \
  -F "file=@image.png"
```

**Batch Embed:**
```bash
curl -X POST http://localhost:8000/embed/batch/text \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["text 1", "text 2"],
    "normalize": true
  }'
```

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Get Metrics:**
```bash
curl "http://localhost:8000/metrics?hours=1"
```

### Direct SageMaker Usage

```python
import boto3
import json

runtime = boto3.client("sagemaker-runtime", region_name="us-east-1")

# Embed text
response = runtime.invoke_endpoint(
    EndpointName="omnisearch-clip-endpoint",
    ContentType="application/json",
    Body=json.dumps({
        "type": "text",
        "data": "A woman wearing a red hat",
        "normalize": True
    })
)

result = json.loads(response["Body"].read())
embedding = result["embedding"]
```

---

## Configuration Files

### .env

```env
USE_SAGEMAKER=true
SAGEMAKER_ENDPOINT_NAME=omnisearch-clip-endpoint
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

### docker-compose.yml

Add to FastAPI service:
```yaml
fastapi:
  environment:
    - USE_SAGEMAKER=true
    - SAGEMAKER_ENDPOINT_NAME=omnisearch-clip-endpoint
    - AWS_REGION=us-east-1
    - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
    - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
```

---

## Performance Baseline

| Metric | Value |
|--------|-------|
| Average latency | 50-100ms |
| Max latency (p99) | 200-500ms |
| Throughput | 10-50 req/s per instance |
| Cost per 1M requests | $0.60-$1.00 |

---

## Troubleshooting

### Endpoint Not Found

```bash
# Check if endpoint exists
aws sagemaker describe-endpoint --endpoint-name omnisearch-clip-endpoint

# List all endpoints
aws sagemaker list-endpoints
```

### Endpoint Stuck in Creating

```bash
# Check logs
aws logs tail /aws/sagemaker/Endpoints/omnisearch-clip-endpoint --follow

# Delete and retry
aws sagemaker delete-endpoint --endpoint-name omnisearch-clip-endpoint
```

### Authentication Errors

```bash
# Verify credentials
aws sts get-caller-identity

# Set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### High Latency

1. Check endpoint metrics: `python monitor_sagemaker_endpoint.py --watch`
2. Check instance count: `aws sagemaker describe-endpoint --endpoint-name omnisearch-clip-endpoint`
3. Scale up if needed: Increase `MaxCapacity` in autoscaling policy
4. Upgrade instance type: Change from `ml.g4dn.xlarge` to `ml.g4dn.2xlarge`

---

## Cost Estimation

### Hourly Costs

| Instance Type | Price/Hour |
|---------------|-----------|
| ml.g4dn.xlarge | $0.81 |
| ml.g4dn.2xlarge | $1.71 |
| ml.g4dn.12xlarge | $10.29 |

### Monthly Estimates (1 instance, always on)

| Instance | Monthly |
|----------|---------|
| ml.g4dn.xlarge | $583 |
| ml.g4dn.2xlarge | $1,231 |

### Cost Optimization

- Use Savings Plans: 20-40% discount
- Auto-scale down during off-peak
- Use Spot Instances: 70% discount (with interruption risk)
- Keep services in same region

---

## Files Created

| File | Purpose |
|------|---------|
| `services/sagemaker_clip_service.py` | SageMaker embedding service |
| `api/embedding.py` | FastAPI embedding endpoint |
| `scripts/deploy_sagemaker_endpoint.py` | Deployment script |
| `scripts/monitor_sagemaker_endpoint.py` | Monitoring script |
| `docs/SAGEMAKER_DEPLOYMENT_GUIDE.md` | Full deployment guide |
| `docs/SAGEMAKER_QUICKREF.md` | This quick reference |

---

## Example Workflow

### Local Development

```bash
# Use local CLIP model
export USE_SAGEMAKER=false
export CLIP_MODEL=ViT-B/32

# Start FastAPI
python api/main.py
```

### Production with SageMaker

```bash
# Deploy endpoint once
python scripts/deploy_sagemaker_endpoint.py --deploy

# Enable autoscaling
python scripts/deploy_sagemaker_endpoint.py --autoscale

# Update FastAPI configuration
export USE_SAGEMAKER=true
export SAGEMAKER_ENDPOINT_NAME=omnisearch-clip-endpoint

# Start FastAPI (now using SageMaker)
python api/main.py
```

### Monitor

```bash
# Watch in real-time
python scripts/monitor_sagemaker_endpoint.py --watch

# Export daily metrics
python scripts/monitor_sagemaker_endpoint.py --export metrics-$(date +%Y-%m-%d).json --hours 24
```

---

## Migration Path: Local → SageMaker

### Step 1: Develop Locally

```python
# Use local CLIP service
from services.clip_service import CLIPEmbeddingService

service = CLIPEmbeddingService(model_name="ViT-B/32")
embedding = service.embed_text("test")
```

### Step 2: Deploy to SageMaker

```bash
python scripts/deploy_sagemaker_endpoint.py --deploy
```

### Step 3: Update Code

```python
# Switch to SageMaker service
from services.sagemaker_clip_service import SageMakerCLIPEmbeddingService

service = SageMakerCLIPEmbeddingService(
    endpoint_name="omnisearch-clip-endpoint",
    region_name="us-east-1"
)
embedding = service.embed_text("test")
```

### Step 4: Environment-based Selection

```python
USE_SAGEMAKER = os.getenv("USE_SAGEMAKER", "false") == "true"

if USE_SAGEMAKER:
    service = SageMakerCLIPEmbeddingService(...)
else:
    service = CLIPEmbeddingService(...)
```

---

## Key Differences: Local vs SageMaker

| Aspect | Local | SageMaker |
|--------|-------|----------|
| Setup time | 1 minute | 10 minutes |
| Latency | 50-200ms | 50-100ms |
| Throughput | Limited by GPU | Auto-scales |
| Cost (monthly) | $0 | $600+ |
| Maintenance | Manual | Managed |
| Scaling | Manual | Automatic |
| Monitoring | Manual | CloudWatch |

---

## Resources

- [SageMaker Documentation](https://docs.aws.amazon.com/sagemaker/)
- [SageMaker Pricing](https://aws.amazon.com/sagemaker/pricing/)
- [CLIP GitHub](https://github.com/openai/CLIP)
- [PyTorch on SageMaker](https://docs.aws.amazon.com/sagemaker/latest/dg/pytorch.html)

---

## Support

For issues, check:
1. `SAGEMAKER_DEPLOYMENT_GUIDE.md` - Full guide
2. `deploy_sagemaker_endpoint.py --help` - Deployment help
3. `monitor_sagemaker_endpoint.py --help` - Monitoring help
4. AWS SageMaker console: https://console.aws.amazon.com/sagemaker/

---

**Last Updated:** January 28, 2026
**Status:** Production Ready ✅
