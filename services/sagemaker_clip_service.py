"""
CLIP Embedding Service using AWS SageMaker endpoint.
Provides text and image embedding functionality with remote inference.
"""
import boto3
import numpy as np
import json
import base64
from typing import Optional, List
from io import BytesIO
from PIL import Image
import logging
import os

logger = logging.getLogger(__name__)


class SageMakerCLIPEmbeddingService:
    """
    Service for generating CLIP embeddings using AWS SageMaker endpoint.
    
    Replaces local GPU inference with managed SageMaker endpoint.
    Handles both text and image embeddings with optional normalization.
    """
    
    def __init__(
        self,
        endpoint_name: str,
        region_name: str = "us-east-1",
        normalize: bool = True,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None
    ):
        """
        Initialize SageMaker CLIP embedding service.
        
        Args:
            endpoint_name: Name of SageMaker endpoint
            region_name: AWS region (default: us-east-1)
            normalize: Whether to normalize embeddings (default: True)
            aws_access_key_id: AWS access key (uses environment if None)
            aws_secret_access_key: AWS secret key (uses environment if None)
            
        Raises:
            ValueError: If endpoint doesn't exist or is not in service
            RuntimeError: If endpoint is not in service
        """
        self.endpoint_name = endpoint_name
        self.region_name = region_name
        self.normalize = normalize
        
        # Initialize SageMaker runtime client (for inference)
        self.runtime = boto3.client(
            "sagemaker-runtime",
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
        # Initialize SageMaker client (for endpoint info)
        self.sm_client = boto3.client(
            "sagemaker",
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
        # Initialize S3 client for image loading
        self.s3_client = boto3.client(
            "s3",
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
        # Verify endpoint exists and is in service
        self._verify_endpoint()
        
        logger.info(f"✓ SageMaker CLIP service initialized")
        logger.info(f"  Endpoint: {endpoint_name}")
        logger.info(f"  Region: {region_name}")
        logger.info(f"  Normalize: {normalize}")
    
    def _verify_endpoint(self):
        """
        Verify endpoint exists and is in service.
        
        Raises:
            ValueError: If endpoint doesn't exist
            RuntimeError: If endpoint is not in service
        """
        try:
            response = self.sm_client.describe_endpoint(
                EndpointName=self.endpoint_name
            )
            
            status = response["EndpointStatus"]
            if status != "InService":
                raise RuntimeError(
                    f"Endpoint '{self.endpoint_name}' is not in service. "
                    f"Status: {status}"
                )
            
            logger.info(f"Endpoint status: {status} ✓")
            
        except self.sm_client.exceptions.ValidationException as e:
            raise ValueError(
                f"Endpoint '{self.endpoint_name}' does not exist. "
                f"Deploy endpoint using deploy_sagemaker_endpoint.py. "
                f"Error: {str(e)}"
            )
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate normalized embedding vector from text.
        
        Args:
            text: Input text string to embed
            
        Returns:
            Normalized numpy array of shape (embedding_dim,)
            
        Raises:
            ValueError: If text is empty
            RuntimeError: If endpoint invocation fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        payload = {
            "type": "text",
            "data": text.strip(),
            "normalize": self.normalize
        }
        
        try:
            response = self.runtime.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType="application/json",
                Accept="application/json",
                Body=json.dumps(payload)
            )
            
            result = json.loads(response["Body"].read())
            embedding = np.array(result["embedding"], dtype=np.float32)
            
            logger.debug(f"Text embedding generated: {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating text embedding: {str(e)}")
            raise RuntimeError(f"Failed to generate text embedding: {str(e)}")
    
    def embed_image(self, image_path: str) -> np.ndarray:
        """
        Generate normalized embedding vector from image.
        
        Supports both local files and S3 URIs.
        
        Args:
            image_path: Path to image file (local) or S3 URI (s3://bucket/key)
            
        Returns:
            Normalized numpy array of shape (embedding_dim,)
            
        Raises:
            FileNotFoundError: If local image file doesn't exist
            ValueError: If image cannot be loaded
            RuntimeError: If endpoint invocation fails
        """
        # Load image data
        if image_path.startswith("s3://"):
            image_data = self._load_image_from_s3(image_path)
        else:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            with open(image_path, "rb") as f:
                image_data = f.read()
        
        # Validate image can be loaded
        try:
            Image.open(BytesIO(image_data)).convert("RGB")
        except Exception as e:
            raise ValueError(f"Cannot load image: {str(e)}")
        
        # Encode as base64
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        
        payload = {
            "type": "image",
            "data": image_base64,
            "normalize": self.normalize
        }
        
        try:
            response = self.runtime.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType="application/json",
                Accept="application/json",
                Body=json.dumps(payload)
            )
            
            result = json.loads(response["Body"].read())
            embedding = np.array(result["embedding"], dtype=np.float32)
            
            logger.debug(f"Image embedding generated: {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating image embedding: {str(e)}")
            raise RuntimeError(f"Failed to generate image embedding: {str(e)}")
    
    def _load_image_from_s3(self, s3_uri: str) -> bytes:
        """
        Load image from S3 URI.
        
        Args:
            s3_uri: S3 URI in format s3://bucket/key
            
        Returns:
            Image data as bytes
            
        Raises:
            ValueError: If S3 URI is invalid
            RuntimeError: If S3 download fails
        """
        try:
            # Parse S3 URI
            if not s3_uri.startswith("s3://"):
                raise ValueError(f"Invalid S3 URI: {s3_uri}")
            
            parts = s3_uri.replace("s3://", "").split("/", 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid S3 URI format: {s3_uri}")
            
            bucket, key = parts
            
            # Download image
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            image_data = response["Body"].read()
            
            logger.debug(f"Image loaded from S3: {bucket}/{key}")
            return image_data
            
        except Exception as e:
            raise RuntimeError(f"Failed to load image from S3: {str(e)}")
    
    def embed_batch(self, texts: List[str], batch_size: int = 10) -> np.ndarray:
        """
        Embed multiple texts efficiently.
        
        Processes texts sequentially (SageMaker doesn't support batch mode).
        For high throughput, consider endpoint batching configuration.
        
        Args:
            texts: List of text strings
            batch_size: Batch size (informational, not used for SageMaker)
            
        Returns:
            Numpy array of shape (len(texts), embedding_dim)
            
        Raises:
            ValueError: If texts list is empty
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        embeddings = []
        
        for i, text in enumerate(texts):
            try:
                embedding = self.embed_text(text)
                embeddings.append(embedding)
                
                if (i + 1) % 10 == 0:
                    logger.debug(f"Processed {i + 1}/{len(texts)} texts")
                    
            except Exception as e:
                logger.error(f"Error embedding text {i}: {str(e)}")
                raise
        
        logger.info(f"✓ Batch embedding complete: {len(texts)} texts")
        return np.array(embeddings)
    
    def get_endpoint_metrics(self) -> dict:
        """
        Get endpoint metrics and status.
        
        Returns:
            Dictionary with endpoint information:
            - endpoint_name: Endpoint name
            - endpoint_status: Current status (InService, Creating, etc.)
            - instance_type: ML instance type
            - current_instance_count: Number of running instances
            - creation_time: When endpoint was created
            - last_modified_time: Last modification time
            
        Raises:
            RuntimeError: If unable to retrieve metrics
        """
        try:
            response = self.sm_client.describe_endpoint(
                EndpointName=self.endpoint_name
            )
            
            variant = response["ProductionVariants"][0]
            
            metrics = {
                "endpoint_name": response["EndpointName"],
                "endpoint_status": response["EndpointStatus"],
                "instance_type": variant["InstanceType"],
                "current_instance_count": variant["CurrentInstanceCount"],
                "desired_instance_count": variant["DesiredInstanceCount"],
                "creation_time": response["CreationTime"].isoformat(),
                "last_modified_time": response["LastModifiedTime"].isoformat(),
            }
            
            logger.debug(f"Endpoint metrics retrieved: {metrics}")
            return metrics
            
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve endpoint metrics: {str(e)}")
    
    def get_endpoint_invoke_stats(self, hours: int = 1) -> dict:
        """
        Get endpoint invocation statistics from CloudWatch.
        
        Args:
            hours: Number of hours to look back (default: 1)
            
        Returns:
            Dictionary with invocation statistics
            
        Raises:
            RuntimeError: If unable to retrieve metrics
        """
        try:
            from datetime import datetime, timedelta
            
            cloudwatch = boto3.client("cloudwatch", region_name=self.region_name)
            
            start_time = datetime.utcnow() - timedelta(hours=hours)
            end_time = datetime.utcnow()
            
            # Get model invocations
            response = cloudwatch.get_metric_statistics(
                Namespace="AWS/SageMaker",
                MetricName="ModelInvocations",
                Dimensions=[
                    {"Name": "EndpointName", "Value": self.endpoint_name},
                    {"Name": "VariantName", "Value": "AllTraffic"}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=["Sum"]
            )
            
            total_invocations = sum([d["Sum"] for d in response["Datapoints"]]) if response["Datapoints"] else 0
            
            # Get model latency
            response = cloudwatch.get_metric_statistics(
                Namespace="AWS/SageMaker",
                MetricName="ModelLatency",
                Dimensions=[
                    {"Name": "EndpointName", "Value": self.endpoint_name},
                    {"Name": "VariantName", "Value": "AllTraffic"}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=["Average", "Maximum", "Minimum"]
            )
            
            stats = {
                "total_invocations": int(total_invocations),
                "time_period_hours": hours,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            }
            
            if response["Datapoints"]:
                avg_latency = sum([d["Average"] for d in response["Datapoints"]]) / len(response["Datapoints"])
                max_latency = max([d["Maximum"] for d in response["Datapoints"]])
                min_latency = min([d["Minimum"] for d in response["Datapoints"]])
                
                stats.update({
                    "avg_latency_ms": round(avg_latency, 2),
                    "max_latency_ms": round(max_latency, 2),
                    "min_latency_ms": round(min_latency, 2),
                })
            
            logger.debug(f"Endpoint stats: {stats}")
            return stats
            
        except Exception as e:
            logger.warning(f"Unable to retrieve CloudWatch metrics: {str(e)}")
            return {"error": str(e)}
