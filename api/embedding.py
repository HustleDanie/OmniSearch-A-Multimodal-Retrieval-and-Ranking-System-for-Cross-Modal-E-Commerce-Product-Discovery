"""
Embedding API endpoint with support for local and SageMaker inference.

Endpoints:
    POST /embed/text - Embed text
    POST /embed/image - Embed image
    GET /health - Health check
    GET /metrics - Endpoint metrics (SageMaker only)

Configuration:
    USE_SAGEMAKER - Use SageMaker endpoint (default: false)
    SAGEMAKER_ENDPOINT_NAME - SageMaker endpoint name
    AWS_REGION - AWS region (default: us-east-1)
    CLIP_MODEL - Local CLIP model variant (default: ViT-B/32)
"""
from fastapi import FastAPI, HTTPException, File, UploadFile, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import os
import logging
import tempfile

logger = logging.getLogger(__name__)

# Initialize embedding service based on environment
USE_SAGEMAKER = os.getenv("USE_SAGEMAKER", "false").lower() == "true"

if USE_SAGEMAKER:
    try:
        from services.sagemaker_clip_service import SageMakerCLIPEmbeddingService
        
        ENDPOINT_NAME = os.getenv("SAGEMAKER_ENDPOINT_NAME", "omnisearch-clip-endpoint")
        REGION = os.getenv("AWS_REGION", "us-east-1")
        
        embedding_service = SageMakerCLIPEmbeddingService(
            endpoint_name=ENDPOINT_NAME,
            region_name=REGION,
            normalize=True
        )
        logger.info(f"✓ Using SageMaker endpoint: {ENDPOINT_NAME}")
        SERVICE_TYPE = "sagemaker"
        
    except Exception as e:
        logger.error(f"Failed to initialize SageMaker service: {str(e)}")
        logger.info("Falling back to local CLIP service")
        from services.clip_service import CLIPEmbeddingService
        
        MODEL_NAME = os.getenv("CLIP_MODEL", "ViT-B/32")
        embedding_service = CLIPEmbeddingService(model_name=MODEL_NAME)
        logger.info(f"✓ Using local CLIP model: {MODEL_NAME}")
        SERVICE_TYPE = "local"
else:
    try:
        from services.clip_service import CLIPEmbeddingService
        
        MODEL_NAME = os.getenv("CLIP_MODEL", "ViT-B/32")
        embedding_service = CLIPEmbeddingService(model_name=MODEL_NAME)
        logger.info(f"✓ Using local CLIP model: {MODEL_NAME}")
        SERVICE_TYPE = "local"
        
    except Exception as e:
        logger.error(f"Failed to initialize CLIP service: {str(e)}")
        embedding_service = None
        SERVICE_TYPE = None


# ==================== Request/Response Models ====================

class TextEmbeddingRequest(BaseModel):
    """Text embedding request."""
    text: str = Field(..., min_length=1, description="Text to embed")
    normalize: bool = Field(True, description="Normalize embedding vector")


class ImageEmbeddingRequest(BaseModel):
    """Image embedding request."""
    s3_uri: Optional[str] = Field(None, description="S3 URI of image (s3://bucket/key)")


class EmbeddingResponse(BaseModel):
    """Embedding response."""
    embedding: List[float] = Field(..., description="Embedding vector")
    dimension: int = Field(..., description="Embedding dimension")
    service: str = Field(..., description="Service used (local or sagemaker)")


class BatchTextEmbeddingRequest(BaseModel):
    """Batch text embedding request."""
    texts: List[str] = Field(..., min_items=1, description="Texts to embed")
    normalize: bool = Field(True, description="Normalize embedding vectors")


class BatchEmbeddingResponse(BaseModel):
    """Batch embedding response."""
    embeddings: List[List[float]] = Field(..., description="List of embedding vectors")
    count: int = Field(..., description="Number of embeddings")
    dimension: int = Field(..., description="Embedding dimension")
    service: str = Field(..., description="Service used")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    service_type: str = Field(..., description="Service type (local or sagemaker)")
    device: Optional[str] = Field(None, description="Device (local only)")
    endpoint_status: Optional[str] = Field(None, description="Endpoint status (SageMaker only)")


class MetricsResponse(BaseModel):
    """Metrics response."""
    endpoint_name: Optional[str] = Field(None, description="Endpoint name")
    endpoint_status: Optional[str] = Field(None, description="Endpoint status")
    instance_type: Optional[str] = Field(None, description="Instance type")
    current_instances: Optional[int] = Field(None, description="Current instance count")
    total_invocations: Optional[int] = Field(None, description="Total invocations (last hour)")
    avg_latency_ms: Optional[float] = Field(None, description="Average latency")


# ==================== API Endpoints ====================

router = FastAPI(
    title="Embedding Service API",
    description="CLIP embedding service with local or SageMaker inference",
    version="1.0.0"
)


@router.post(
    "/embed/text",
    response_model=EmbeddingResponse,
    summary="Embed text",
    tags=["Embeddings"]
)
async def embed_text(request: TextEmbeddingRequest):
    """
    Generate embedding for text.
    
    **Parameters:**
    - **text**: Text string to embed
    - **normalize**: Whether to normalize the embedding (default: True)
    
    **Returns:**
    - **embedding**: Normalized embedding vector
    - **dimension**: Dimension of embedding (512 for ViT-B/32)
    - **service**: Service used (local or sagemaker)
    """
    if embedding_service is None:
        raise HTTPException(status_code=503, detail="Embedding service not initialized")
    
    try:
        embedding = embedding_service.embed_text(request.text)
        
        return EmbeddingResponse(
            embedding=embedding.tolist(),
            dimension=len(embedding),
            service=SERVICE_TYPE
        )
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Embedding error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/embed/image",
    response_model=EmbeddingResponse,
    summary="Embed image",
    tags=["Embeddings"]
)
async def embed_image(file: UploadFile = File(...)):
    """
    Generate embedding for image.
    
    **Parameters:**
    - **file**: Image file (PNG, JPG, GIF, etc.)
    
    **Returns:**
    - **embedding**: Normalized embedding vector
    - **dimension**: Dimension of embedding (512 for ViT-B/32)
    - **service**: Service used (local or sagemaker)
    """
    if embedding_service is None:
        raise HTTPException(status_code=503, detail="Embedding service not initialized")
    
    try:
        # Save temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            content = await file.read()
            tmp.write(content)
            temp_path = tmp.name
        
        try:
            embedding = embedding_service.embed_image(temp_path)
            
            return EmbeddingResponse(
                embedding=embedding.tolist(),
                dimension=len(embedding),
                service=SERVICE_TYPE
            )
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except FileNotFoundError as e:
        logger.error(f"File error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        logger.error(f"Image error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Image embedding error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/embed/batch/text",
    response_model=BatchEmbeddingResponse,
    summary="Embed multiple texts",
    tags=["Embeddings"]
)
async def embed_batch_text(request: BatchTextEmbeddingRequest):
    """
    Generate embeddings for multiple texts.
    
    **Parameters:**
    - **texts**: List of text strings to embed
    - **normalize**: Whether to normalize embeddings (default: True)
    
    **Returns:**
    - **embeddings**: List of embedding vectors
    - **count**: Number of embeddings generated
    - **dimension**: Dimension of each embedding
    - **service**: Service used
    """
    if embedding_service is None:
        raise HTTPException(status_code=503, detail="Embedding service not initialized")
    
    try:
        embeddings = embedding_service.embed_batch(request.texts)
        
        return BatchEmbeddingResponse(
            embeddings=embeddings.tolist(),
            count=len(embeddings),
            dimension=embeddings.shape[1],
            service=SERVICE_TYPE
        )
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Batch embedding error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["System"]
)
async def health():
    """
    Check embedding service health.
    
    **Returns:**
    - **status**: Service status (healthy/unhealthy)
    - **service_type**: Type of service (local or sagemaker)
    - **device**: Device name (local only)
    - **endpoint_status**: Endpoint status (SageMaker only)
    """
    if embedding_service is None:
        raise HTTPException(status_code=503, detail="Embedding service not initialized")
    
    try:
        if SERVICE_TYPE == "sagemaker":
            metrics = embedding_service.get_endpoint_metrics()
            return HealthResponse(
                status="healthy",
                service_type="sagemaker",
                endpoint_status=metrics["endpoint_status"]
            )
        else:
            return HealthResponse(
                status="healthy",
                service_type="local",
                device=embedding_service.device
            )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Get metrics",
    tags=["System"]
)
async def metrics(hours: int = Query(1, ge=1, le=24)):
    """
    Get endpoint metrics and statistics.
    
    **Parameters:**
    - **hours**: Number of hours to look back (1-24, default: 1)
    
    **Returns:**
    - **endpoint_name**: Endpoint name
    - **endpoint_status**: Current endpoint status
    - **instance_type**: ML instance type
    - **current_instances**: Number of running instances
    - **total_invocations**: Total invocations in period
    - **avg_latency_ms**: Average latency in milliseconds
    
    **Note:** Only available for SageMaker endpoints
    """
    if SERVICE_TYPE != "sagemaker":
        raise HTTPException(
            status_code=400,
            detail="Metrics only available for SageMaker endpoints"
        )
    
    try:
        endpoint_metrics = embedding_service.get_endpoint_metrics()
        invocation_stats = embedding_service.get_endpoint_invoke_stats(hours=hours)
        
        return MetricsResponse(
            endpoint_name=endpoint_metrics["endpoint_name"],
            endpoint_status=endpoint_metrics["endpoint_status"],
            instance_type=endpoint_metrics["instance_type"],
            current_instances=endpoint_metrics["current_instance_count"],
            total_invocations=invocation_stats.get("total_invocations"),
            avg_latency_ms=invocation_stats.get("avg_latency_ms")
        )
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", tags=["System"])
async def root():
    """API documentation."""
    return {
        "service": "Embedding Service",
        "version": "1.0.0",
        "service_type": SERVICE_TYPE,
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


# ==================== App creation ====================

app = router

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("FASTAPI_PORT", 8000))
    host = os.getenv("FASTAPI_HOST", "0.0.0.0")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
