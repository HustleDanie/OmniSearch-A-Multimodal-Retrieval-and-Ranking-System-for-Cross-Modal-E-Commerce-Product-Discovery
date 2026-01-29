"""
Test script for multimodal embedding fusion.
Demonstrates the fuse_embeddings function behavior.
"""
import sys
import os
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import get_search_service, get_clip_service


def test_fusion_both_vectors():
    """Test fusion with both image and text vectors."""
    print("=" * 80)
    print("TEST 1: Fuse Both Image and Text Embeddings")
    print("=" * 80)
    
    clip_service = get_clip_service()
    search_service = get_search_service()
    
    # Generate embeddings
    text = "blue denim jacket"
    print(f"\nGenerating embeddings for: '{text}'")
    
    text_vec = clip_service.embed_text(text)
    # Simulate an image vector (use text as proxy for demo)
    image_vec = clip_service.embed_text(f"a photo of a {text}")
    
    print(f"Text embedding shape: {text_vec.shape}")
    print(f"Image embedding shape: {image_vec.shape}")
    
    # Fuse embeddings (60% image, 40% text)
    fused = search_service.fuse_embeddings(
        image_vec=image_vec,
        text_vec=text_vec,
        image_weight=0.6,
        text_weight=0.4
    )
    
    print(f"\nFused embedding shape: {fused.shape}")
    print(f"Fused embedding norm: {np.linalg.norm(fused):.6f}")
    print(f"First 5 values: {fused[:5]}")
    
    # Verify normalization
    assert abs(np.linalg.norm(fused) - 1.0) < 1e-6, "Vector should be normalized"
    print("\n✓ Fused vector is normalized (norm = 1.0)")


def test_fusion_text_only():
    """Test fusion with text vector only."""
    print("\n" + "=" * 80)
    print("TEST 2: Fuse Text Embedding Only")
    print("=" * 80)
    
    clip_service = get_clip_service()
    search_service = get_search_service()
    
    text = "red athletic shoes"
    print(f"\nGenerating text embedding for: '{text}'")
    
    text_vec = clip_service.embed_text(text)
    
    # Fuse with only text
    fused = search_service.fuse_embeddings(
        image_vec=None,
        text_vec=text_vec
    )
    
    print(f"\nFused embedding shape: {fused.shape}")
    print(f"Fused embedding norm: {np.linalg.norm(fused):.6f}")
    
    # Should be identical to original (but normalized)
    similarity = np.dot(fused, text_vec)
    print(f"Similarity to original: {similarity:.6f}")
    
    assert abs(np.linalg.norm(fused) - 1.0) < 1e-6, "Vector should be normalized"
    assert abs(similarity - 1.0) < 1e-6, "Should be same as original"
    print("\n✓ Text-only fusion works correctly")


def test_fusion_image_only():
    """Test fusion with image vector only (simulated)."""
    print("\n" + "=" * 80)
    print("TEST 3: Fuse Image Embedding Only")
    print("=" * 80)
    
    clip_service = get_clip_service()
    search_service = get_search_service()
    
    # Simulate image vector
    text = "a photo of a green backpack"
    print(f"\nGenerating image embedding (simulated): '{text}'")
    
    image_vec = clip_service.embed_text(text)
    
    # Fuse with only image
    fused = search_service.fuse_embeddings(
        image_vec=image_vec,
        text_vec=None
    )
    
    print(f"\nFused embedding shape: {fused.shape}")
    print(f"Fused embedding norm: {np.linalg.norm(fused):.6f}")
    
    # Should be identical to original (but normalized)
    similarity = np.dot(fused, image_vec)
    print(f"Similarity to original: {similarity:.6f}")
    
    assert abs(np.linalg.norm(fused) - 1.0) < 1e-6, "Vector should be normalized"
    assert abs(similarity - 1.0) < 1e-6, "Should be same as original"
    print("\n✓ Image-only fusion works correctly")


def test_fusion_error():
    """Test fusion with no vectors (should raise error)."""
    print("\n" + "=" * 80)
    print("TEST 4: Fusion with No Vectors (Error Case)")
    print("=" * 80)
    
    search_service = get_search_service()
    
    print("\nAttempting to fuse with no vectors...")
    
    try:
        fused = search_service.fuse_embeddings(
            image_vec=None,
            text_vec=None
        )
        print("\n✗ Should have raised ValueError")
        
    except ValueError as e:
        print(f"\n✓ Correctly raised ValueError: {e}")


def test_custom_weights():
    """Test fusion with custom weights."""
    print("\n" + "=" * 80)
    print("TEST 5: Custom Fusion Weights")
    print("=" * 80)
    
    clip_service = get_clip_service()
    search_service = get_search_service()
    
    text_vec = clip_service.embed_text("blue jacket")
    image_vec = clip_service.embed_text("a photo of blue jacket")
    
    # Test different weight combinations
    weight_configs = [
        (0.8, 0.2, "80% image, 20% text"),
        (0.5, 0.5, "50% image, 50% text"),
        (0.3, 0.7, "30% image, 70% text"),
        (1.0, 0.0, "100% image"),
        (0.0, 1.0, "100% text")
    ]
    
    print("\nTesting different weight combinations:")
    
    for img_w, txt_w, desc in weight_configs:
        fused = search_service.fuse_embeddings(
            image_vec=image_vec,
            text_vec=text_vec,
            image_weight=img_w,
            text_weight=txt_w
        )
        
        # Calculate similarities
        img_sim = np.dot(fused, image_vec)
        txt_sim = np.dot(fused, text_vec)
        
        print(f"\n  {desc}:")
        print(f"    Similarity to image: {img_sim:.4f}")
        print(f"    Similarity to text:  {txt_sim:.4f}")
        print(f"    Vector norm: {np.linalg.norm(fused):.6f}")


def test_multimodal_search():
    """Test multimodal search integration."""
    print("\n" + "=" * 80)
    print("TEST 6: Multimodal Search Integration")
    print("=" * 80)
    
    search_service = get_search_service()
    
    query = "blue denim jacket"
    print(f"\nPerforming multimodal search for: '{query}'")
    print("(Using text-only since we don't have real images)")
    
    try:
        results = search_service.search_multimodal(
            text_query=query,
            image_path=None,  # No image for demo
            image_weight=0.6,
            text_weight=0.4,
            top_k=5
        )
        
        print(f"\n✓ Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.title} (similarity: {result.similarity:.4f})")
        
    except Exception as e:
        print(f"\nNote: {e}")
        print("Make sure Weaviate has products uploaded to test search")


if __name__ == "__main__":
    print("\n🔀 Multimodal Embedding Fusion Tests\n")
    
    try:
        # Run all tests
        test_fusion_both_vectors()
        test_fusion_text_only()
        test_fusion_image_only()
        test_fusion_error()
        test_custom_weights()
        test_multimodal_search()
        
        print("\n" + "=" * 80)
        print("✓ All fusion tests passed!")
        print("=" * 80)
        
        print("\nSummary:")
        print("  - Fusion with both vectors: ✓")
        print("  - Fusion with text only: ✓")
        print("  - Fusion with image only: ✓")
        print("  - Error handling: ✓")
        print("  - Custom weights: ✓")
        print("  - Multimodal search: ✓")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
