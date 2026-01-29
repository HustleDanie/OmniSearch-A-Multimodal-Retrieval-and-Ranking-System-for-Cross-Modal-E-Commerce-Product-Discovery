"""
Example usage of CLIP Embedding Service.
"""
import numpy as np
from services import CLIPEmbeddingService, get_clip_service


def example_basic_usage():
    """Basic usage example."""
    print("=== Basic CLIP Service Usage ===\n")
    
    # Initialize service (loads model once)
    clip_service = CLIPEmbeddingService()
    
    # Get embedding dimension
    dim = clip_service.get_embedding_dim()
    print(f"Embedding dimension: {dim}\n")
    
    # Embed text
    text = "a red sports car"
    text_embedding = clip_service.embed_text(text)
    print(f"Text: '{text}'")
    print(f"Embedding shape: {text_embedding.shape}")
    print(f"Embedding norm: {np.linalg.norm(text_embedding):.4f}")
    print(f"First 5 values: {text_embedding[:5]}\n")
    
    # Embed another text
    text2 = "a blue bicycle"
    text_embedding2 = clip_service.embed_text(text2)
    
    # Compute similarity
    similarity = clip_service.compute_similarity(text_embedding, text_embedding2)
    print(f"Similarity between '{text}' and '{text2}': {similarity:.4f}\n")


def example_image_embedding():
    """Image embedding example (requires actual images)."""
    print("=== Image Embedding Example ===\n")
    
    clip_service = get_clip_service()
    
    # Example: embed image (would need actual image file)
    try:
        image_path = "path/to/your/image.jpg"
        image_embedding = clip_service.embed_image(image_path)
        print(f"Image embedding shape: {image_embedding.shape}")
        print(f"Image embedding norm: {np.linalg.norm(image_embedding):.4f}")
    except FileNotFoundError:
        print("Note: Provide actual image path to test image embedding")
        print("Example usage:")
        print("  image_embedding = clip_service.embed_image('product.jpg')")
        print("  print(f'Shape: {image_embedding.shape}')")


def example_batch_processing():
    """Batch processing example."""
    print("\n=== Batch Processing Example ===\n")
    
    clip_service = get_clip_service()
    
    # Batch text embeddings
    texts = [
        "a red sports car",
        "a blue bicycle",
        "a green backpack",
        "black leather shoes",
        "white cotton t-shirt"
    ]
    
    batch_embeddings = clip_service.embed_texts_batch(texts)
    print(f"Embedded {len(texts)} texts")
    print(f"Batch shape: {batch_embeddings.shape}")
    
    # Compute similarity matrix
    print("\nSimilarity matrix:")
    for i, text1 in enumerate(texts):
        similarities = []
        for j in range(len(texts)):
            sim = clip_service.compute_similarity(batch_embeddings[i], batch_embeddings[j])
            similarities.append(f"{sim:.3f}")
        print(f"{text1:25s} -> {' '.join(similarities)}")


def example_text_image_similarity():
    """Example of computing text-to-image similarity."""
    print("\n=== Text-to-Image Similarity ===\n")
    
    clip_service = get_clip_service()
    
    # Embed multiple query texts
    queries = [
        "a photo of a car",
        "a photo of a bicycle",
        "a photo of clothing"
    ]
    
    query_embeddings = clip_service.embed_texts_batch(queries)
    
    print(f"Embedded {len(queries)} query texts")
    print("These embeddings can be used to search for similar images")
    print("by computing cosine similarity with image embeddings\n")
    
    # Example workflow:
    print("Typical workflow:")
    print("1. Embed all product images once -> store in vector DB")
    print("2. For search query, embed the query text")
    print("3. Compute similarity with all image embeddings")
    print("4. Return top-K most similar products")


if __name__ == "__main__":
    # Run examples
    example_basic_usage()
    example_image_embedding()
    example_batch_processing()
    example_text_image_similarity()
    
    print("\n✓ All examples completed!")
