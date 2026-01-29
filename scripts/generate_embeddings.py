"""
Generate embeddings for all products in MongoDB.
This script pulls products, generates CLIP embeddings, and prepares them for vector DB upload.
"""
import sys
import os
from typing import List, Dict, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import MongoDBConnection, WeaviateConnection
from services import get_clip_service
import numpy as np


class ProductEmbeddingGenerator:
    """Generate and manage product embeddings."""
    
    def __init__(self):
        """Initialize the embedding generator with CLIP service."""
        self.clip_service = get_clip_service()
        self.embeddings_data: List[Dict[str, Any]] = []
    
    def generate_text_embedding(self, title: str, description: str) -> np.ndarray:
        """
        Generate text embedding from product title and description.
        
        Args:
            title: Product title
            description: Product description
            
        Returns:
            Normalized embedding vector
        """
        # Combine title and description with proper formatting
        combined_text = f"{title}. {description}"
        return self.clip_service.embed_text(combined_text)
    
    def generate_image_embedding(self, image_path: str) -> np.ndarray:
        """
        Generate image embedding from product image.
        
        Args:
            image_path: Path to product image
            
        Returns:
            Normalized embedding vector
        """
        return self.clip_service.embed_image(image_path)
    
    def process_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single product to generate embeddings.
        
        Args:
            product: Product dictionary from MongoDB
            
        Returns:
            Dictionary with product info and embeddings
        """
        product_id = product.get("product_id")
        title = product.get("title", "")
        description = product.get("description", "")
        image_path = product.get("image_path", "")
        
        print(f"Processing product: {product_id} - {title}")
        
        # Generate text embedding
        text_embedding = self.generate_text_embedding(title, description)
        
        # Generate image embedding (with error handling)
        image_embedding = None
        if image_path and os.path.exists(image_path):
            try:
                image_embedding = self.generate_image_embedding(image_path)
            except Exception as e:
                print(f"  ⚠ Failed to generate image embedding: {e}")
        else:
            print(f"  ⚠ Image not found: {image_path}")
        
        # Create embedding record
        embedding_record = {
            "product_id": product_id,
            "title": title,
            "description": description,
            "category": product.get("category"),
            "color": product.get("color"),
            "image_path": image_path,
            "text_embedding": text_embedding,
            "image_embedding": image_embedding,
            "generated_at": datetime.utcnow().isoformat(),
            "embedding_dim": len(text_embedding)
        }
        
        return embedding_record
    
    def process_products_batch(self, products: List[Dict[str, Any]], 
                               use_batch: bool = True) -> List[Dict[str, Any]]:
        """
        Process multiple products efficiently.
        
        Args:
            products: List of product dictionaries
            use_batch: Whether to use batch processing for embeddings
            
        Returns:
            List of embedding records
        """
        if not products:
            print("No products to process")
            return []
        
        print(f"\nProcessing {len(products)} products...")
        
        if use_batch:
            # Batch process text embeddings
            print("Generating text embeddings (batch)...")
            texts = [f"{p.get('title', '')}. {p.get('description', '')}" 
                    for p in products]
            text_embeddings = self.clip_service.embed_texts_batch(texts)
            
            # Process image embeddings individually (file I/O can't be batched easily)
            print("Generating image embeddings...")
            image_embeddings = []
            for product in products:
                image_path = product.get("image_path", "")
                if image_path and os.path.exists(image_path):
                    try:
                        img_emb = self.generate_image_embedding(image_path)
                        image_embeddings.append(img_emb)
                    except Exception as e:
                        print(f"  ⚠ Failed for {product.get('product_id')}: {e}")
                        image_embeddings.append(None)
                else:
                    image_embeddings.append(None)
            
            # Create embedding records
            embedding_records = []
            for i, product in enumerate(products):
                record = {
                    "product_id": product.get("product_id"),
                    "title": product.get("title", ""),
                    "description": product.get("description", ""),
                    "category": product.get("category"),
                    "color": product.get("color"),
                    "image_path": product.get("image_path", ""),
                    "text_embedding": text_embeddings[i],
                    "image_embedding": image_embeddings[i],
                    "generated_at": datetime.utcnow().isoformat(),
                    "embedding_dim": len(text_embeddings[i])
                }
                embedding_records.append(record)
            
            return embedding_records
        else:
            # Process one by one
            embedding_records = []
            for i, product in enumerate(products, 1):
                print(f"[{i}/{len(products)}] ", end="")
                record = self.process_product(product)
                embedding_records.append(record)
            
            return embedding_records
    
    def generate_embeddings_from_mongodb(self, db_name: str = "omnisearch",
                                        limit: int = None,
                                        use_batch: bool = True) -> List[Dict[str, Any]]:
        """
        Pull products from MongoDB and generate embeddings.
        
        Args:
            db_name: MongoDB database name
            limit: Maximum number of products to process (None for all)
            use_batch: Whether to use batch processing
            
        Returns:
            List of embedding records stored in memory
        """
        print(f"{'='*60}")
        print("Product Embedding Generation")
        print(f"{'='*60}\n")
        
        # Connect to MongoDB and fetch products
        with MongoDBConnection(db_name=db_name) as client:
            products = client.fetch_all_products(limit=limit)
        
        if not products:
            print("No products found in MongoDB")
            return []
        
        # Process products
        self.embeddings_data = self.process_products_batch(products, use_batch=use_batch)
        
        # Summary
        total = len(self.embeddings_data)
        with_images = sum(1 for e in self.embeddings_data if e["image_embedding"] is not None)
        
        print(f"\n{'='*60}")
        print("Summary")
        print(f"{'='*60}")
        print(f"Total products processed: {total}")
        print(f"Text embeddings generated: {total}")
        print(f"Image embeddings generated: {with_images}")
        print(f"Embedding dimension: {self.embeddings_data[0]['embedding_dim'] if total > 0 else 'N/A'}")
        print(f"Data stored in memory: {len(self.embeddings_data)} records")
        print(f"{'='*60}\n")
        
        return self.embeddings_data
    
    def get_embeddings(self) -> List[Dict[str, Any]]:
        """
        Get the generated embeddings from memory.
        
        Returns:
            List of embedding records
        """
        return self.embeddings_data
    
    def save_embeddings_to_numpy(self, output_path: str = "embeddings_data.npz"):
        """
        Save embeddings to a compressed NumPy file for backup.
        
        Args:
            output_path: Path to save the .npz file
        """
        if not self.embeddings_data:
            print("No embeddings to save")
            return
        
        # Prepare arrays
        product_ids = [e["product_id"] for e in self.embeddings_data]
        text_embeddings = np.array([e["text_embedding"] for e in self.embeddings_data])
        
        # Handle image embeddings (some might be None)
        image_embeddings = []
        image_mask = []
        for e in self.embeddings_data:
            if e["image_embedding"] is not None:
                image_embeddings.append(e["image_embedding"])
                image_mask.append(True)
            else:
                # Use zero vector as placeholder
                image_embeddings.append(np.zeros_like(e["text_embedding"]))
                image_mask.append(False)
        
        image_embeddings = np.array(image_embeddings)
        image_mask = np.array(image_mask)
        
        # Save to file
        np.savez_compressed(
            output_path,
            product_ids=product_ids,
            text_embeddings=text_embeddings,
            image_embeddings=image_embeddings,
            image_mask=image_mask
        )
        
        print(f"✓ Embeddings saved to {output_path}")
        print(f"  File size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
    
    def get_embedding_summary(self) -> Dict[str, Any]:
        """
        Get a summary of generated embeddings.
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.embeddings_data:
            return {"count": 0}
        
        total = len(self.embeddings_data)
        with_images = sum(1 for e in self.embeddings_data if e["image_embedding"] is not None)
        
        # Calculate average similarity between text and image embeddings
        similarities = []
        for e in self.embeddings_data:
            if e["image_embedding"] is not None:
                sim = np.dot(e["text_embedding"], e["image_embedding"])
                similarities.append(sim)
        
        return {
            "total_products": total,
            "text_embeddings_count": total,
            "image_embeddings_count": with_images,
            "embedding_dimension": self.embeddings_data[0]["embedding_dim"],
            "avg_text_image_similarity": np.mean(similarities) if similarities else None,
            "categories": list(set(e["category"] for e in self.embeddings_data if e["category"])),
            "colors": list(set(e["color"] for e in self.embeddings_data if e["color"]))
        }
    
    def upload_to_weaviate(self, weaviate_url: str = None, 
         upload_to_weaviate: bool = True, limit: int = None):
    """
    Main execution function.
    
    Args:
        upload_to_weaviate: Whether to upload embeddings to Weaviate after generation
        limit: Maximum number of products to process (None for all)
    """
    # Create generator
    generator = ProductEmbeddingGenerator()
    
    # Generate embeddings from MongoDB
    embeddings = generator.generate_embeddings_from_mongodb(
        db_name="omnisearch",
        limit=limit,
        use_batch=True  # Use efficient batch processing
    )
    
    if not embeddings:
        print("No embeddings generated. Exiting.")
        return generator
    
    # Display summary
    summary = generator.get_embedding_summary()
    print("Embedding Statistics:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Upload to Weaviate
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate embeddings and upload to Weaviate")
    parser.add_argument("--no-upload", action="store_true", 
                       help="Skip uploading to Weaviate")
    parser.add_argument("--limit", type=int, default=None,
                       help="Limit number of products to process (default: all)")
    
    args = parser.parse_args()
    
    generator = main(
        upload_to_weaviate=not args.no_upload,
        limit=args.limit
    )
    
    # The embeddings are in memory and uploaded to Weaviate
    # To access embeddings: embeddings_data = generator.get_embeddings()
    # 
    # Each record contains:
    # - product_id, title, description, category, color, image_path
    # - text_embedding (numpy array)
    # - image_embedding (numpy array or None)
    # - generated_at (timestamp)
    #
    # Usage examples:
    # python generate_embeddings.py                    # Generate and upload all
    # python generate_embeddings.py --limit 10         # Process only 10 products
    # python generate_embeddings.py --no-upload        # Generate without uploadingnerated and stored in memory")
        print("  To upload later: generator.upload_to_weaviate()")
    
    # Optional: Save to file for backup
    # generator.save_embeddings_to_numpy("embeddings_backup.npz
        
        with WeaviateConnection(url=weaviate_url) as weaviate_client:
            # Create schema if it doesn't exist
            embedding_dim = self.embeddings_data[0]["embedding_dim"]
            weaviate_client.create_product_schema(vector_dimension=embedding_dim)
            
            # Process in batches for efficiency
            total_batches = (len(self.embeddings_data) + batch_size - 1) // batch_size
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(self.embeddings_data))
                batch_data = self.embeddings_data[start_idx:end_idx]
                
                print(f"Processing batch {batch_idx + 1}/{total_batches} ({start_idx + 1}-{end_idx}/{len(self.embeddings_data)})")
                
                # Prepare batch data
                batch_products = []
                batch_vectors = []
                
                for embedding_record in batch_data:
                    # Prepare metadata properties
                    properties = {
                        "product_id": embedding_record["product_id"],
                        "title": embedding_record["title"],
                        "description": embedding_record["description"],
                        "color": embedding_record["color"],
                        "category": embedding_record["category"],
                        "image_path": embedding_record["image_path"]
                    }
                    
                    # Select vector: prefer image embedding, fallback to text if allowed
                    vector = embedding_record["image_embedding"]
                    
                    if vector is None:
                        if fallback_to_text:
                            vector = embedding_record["text_embedding"]
                            print(f"  ⚠ Using text embedding for {embedding_record['product_id']} (no image)")
                        else:
                            print(f"  ✗ Skipping {embedding_record['product_id']} (no image embedding)")
                            skipped += 1
                            continue
                    
                    batch_products.append(properties)
                    batch_vectors.append(vector)
                
                # Upload batch
                if batch_products:
                    try:
                        vectors_array = np.array(batch_vectors)
                        uuids = weaviate_client.insert_products_batch(batch_products, vectors_array)
                        uploaded += len(uuids)
                    except Exception as e:
                        print(f"  ✗ Batch upload failed: {e}")
                        failed += len(batch_products)
        
        # Summary
        print(f"\n{'='*60}")
        print("Upload Summary")
        print(f"{'='*60}")
        print(f"Successfully uploaded: {uploaded}")
        print(f"Skipped (no image): {skipped}")
        print(f"Failed: {failed}")
        print(f"{'='*60}\n")
        
        return {
            "uploaded": uploaded,
            "skipped": skipped,
            "failed": failed,
            "total_processed": len(self.embeddings_data)
        }


def main():
    """Main execution function."""
    # Create generator
    generator = ProductEmbeddingGenerator()
    
    # Generate embeddings from MongoDB
    # Set limit=None to process all products, or limit=10 for testing
    embeddings = generator.generate_embeddings_from_mongodb(
        db_name="omnisearch",
        limit=None,  # Process all products
        use_batch=True  # Use efficient batch processing
    )
    
    # Display summary
    summary = generator.get_embedding_summary()
    print("Embedding Statistics:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Optional: Save to file for backup
    # generator.save_embeddings_to_numpy("embeddings_backup.npz")
    
    print("\n✓ Embeddings are now stored in memory and ready for vector DB upload")
    print("  Access via: generator.get_embeddings()")
    
    return generator


if __name__ == "__main__":
    generator = main()
    
    # The embeddings are now in memory and can be accessed:
    # embeddings_data = generator.get_embeddings()
    # 
    # Each record contains:
    # - product_id
    # - title, description, category, color
    # - text_embedding (numpy array)
    # - image_embedding (numpy array or None)
    # - generated_at (timestamp)
