"""
CLIP Embedding Service using OpenAI CLIP (ViT-B/32).
Provides text and image embedding functionality with GPU support.
"""
import torch
import clip
import numpy as np
from PIL import Image
from typing import Optional
import os


class CLIPEmbeddingService:
    """Service for generating CLIP embeddings from text and images."""
    
    def __init__(self, model_name: str = "ViT-B/32", device: Optional[str] = None):
        """
        Initialize CLIP model at startup.
        
        Args:
            model_name: CLIP model variant to use (default: ViT-B/32)
            device: Device to use ('cuda' or 'cpu'). Auto-detects if None.
        """
        # Determine device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        print(f"Loading CLIP model '{model_name}' on {self.device}...")
        
        # Load CLIP model and preprocessing
        self.model, self.preprocess = clip.load(model_name, device=self.device)
        self.model.eval()  # Set to evaluation mode
        
        print(f"✓ CLIP model loaded successfully on {self.device}")
        
        if self.device == "cuda":
            print(f"  GPU: {torch.cuda.get_device_name(0)}")
            print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate normalized embedding vector from text.
        
        Args:
            text: Input text string to embed
            
        Returns:
            Normalized numpy array of shape (embedding_dim,)
        """
        # Tokenize text
        text_tokens = clip.tokenize([text]).to(self.device)
        
        # Generate embedding
        with torch.no_grad():
            text_features = self.model.encode_text(text_tokens)
            
            # Normalize
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        # Convert to numpy and remove batch dimension
        embedding = text_features.cpu().numpy()[0]
        
        return embedding
    
    def embed_image(self, image_path: str) -> np.ndarray:
        """
        Generate normalized embedding vector from image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Normalized numpy array of shape (embedding_dim,)
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image cannot be loaded
        """
        # Check if file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert("RGB")
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)
            
            # Generate embedding
            with torch.no_grad():
                image_features = self.model.encode_image(image_input)
                
                # Normalize
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            # Convert to numpy and remove batch dimension
            embedding = image_features.cpu().numpy()[0]
            
            return embedding
            
        except Exception as e:
            raise ValueError(f"Failed to load or process image '{image_path}': {e}")
    
    def embed_images_batch(self, image_paths: list[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate normalized embeddings for multiple images efficiently.
        
        Args:
            image_paths: List of paths to image files
            batch_size: Number of images to process at once
            
        Returns:
            Normalized numpy array of shape (num_images, embedding_dim)
        """
        all_embeddings = []
        
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            batch_images = []
            
            for path in batch_paths:
                if not os.path.exists(path):
                    raise FileNotFoundError(f"Image not found: {path}")
                
                image = Image.open(path).convert("RGB")
                batch_images.append(self.preprocess(image))
            
            # Stack into batch tensor
            batch_tensor = torch.stack(batch_images).to(self.device)
            
            # Generate embeddings
            with torch.no_grad():
                image_features = self.model.encode_image(batch_tensor)
                
                # Normalize
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            all_embeddings.append(image_features.cpu().numpy())
        
        # Concatenate all batches
        return np.vstack(all_embeddings)
    
    def embed_texts_batch(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate normalized embeddings for multiple texts efficiently.
        
        Args:
            texts: List of text strings to embed
            batch_size: Number of texts to process at once
            
        Returns:
            Normalized numpy array of shape (num_texts, embedding_dim)
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Tokenize batch
            text_tokens = clip.tokenize(batch_texts).to(self.device)
            
            # Generate embeddings
            with torch.no_grad():
                text_features = self.model.encode_text(text_tokens)
                
                # Normalize
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            all_embeddings.append(text_features.cpu().numpy())
        
        # Concatenate all batches
        return np.vstack(all_embeddings)
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        return float(np.dot(embedding1, embedding2))
    
    def get_embedding_dim(self) -> int:
        """
        Get the dimensionality of the embeddings.
        
        Returns:
            Embedding dimension size
        """
        return self.model.visual.output_dim


# Singleton instance for reuse across application
_clip_service: Optional[CLIPEmbeddingService] = None


def get_clip_service(model_name: str = "ViT-B/32") -> CLIPEmbeddingService:
    """
    Get or create singleton CLIP service instance.
    
    Args:
        model_name: CLIP model variant to use
        
    Returns:
        CLIPEmbeddingService instance
    """
    global _clip_service
    
    if _clip_service is None:
        _clip_service = CLIPEmbeddingService(model_name=model_name)
    
    return _clip_service
