#!/usr/bin/env python3
"""
Generate and populate a comprehensive sample product database.
This demonstrates the full capabilities of OmniSearch with diverse products.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import WeaviateConnection
from services import get_clip_service
from typing import List, Dict, Any

# Comprehensive sample products database
COMPREHENSIVE_PRODUCTS = [
    # APPAREL - Men
    {"title": "Black Cotton T-Shirt", "description": "Classic black cotton t-shirt for casual wear, comfortable fit", "color": "black", "category": "apparel"},
    {"title": "White Polo Shirt", "description": "Elegant white polo shirt with collar, perfect for business casual", "color": "white", "category": "apparel"},
    {"title": "Blue Denim Jacket", "description": "Stylish blue denim jacket with pockets, timeless design", "color": "blue", "category": "apparel"},
    {"title": "Navy Chinos", "description": "Professional navy chinos trousers for work or casual outings", "color": "navy", "category": "apparel"},
    {"title": "Red Hoodie Sweatshirt", "description": "Warm red hoodie with drawstring and kangaroo pocket", "color": "red", "category": "apparel"},
    {"title": "Gray Wool Sweater", "description": "Comfortable gray wool sweater, perfect for cool weather", "color": "gray", "category": "apparel"},
    {"title": "Black Leather Jacket", "description": "Premium black leather motorcycle jacket with zippers", "color": "black", "category": "apparel"},
    {"title": "Green Military Shirt", "description": "Durable green military-style shirt with cargo pockets", "color": "green", "category": "apparel"},
    
    # APPAREL - Women
    {"title": "Black Dress", "description": "Elegant black cocktail dress perfect for evening events", "color": "black", "category": "apparel"},
    {"title": "Red Summer Dress", "description": "Bright red summer dress with floral patterns and flowing design", "color": "red", "category": "apparel"},
    {"title": "Blue Blouse", "description": "Professional blue blouse with button-up front, perfect for office", "color": "blue", "category": "apparel"},
    {"title": "White Cardigan", "description": "Soft white cardigan sweater for layering, comfortable fit", "color": "white", "category": "apparel"},
    {"title": "Green Skirt", "description": "Stylish green midi skirt with pleated design", "color": "green", "category": "apparel"},
    {"title": "Pink Jacket", "description": "Modern pink blazer jacket for professional settings", "color": "pink", "category": "apparel"},
    {"title": "Purple Yoga Pants", "description": "Comfortable purple yoga pants with high waist, ideal for fitness", "color": "purple", "category": "apparel"},
    
    # FOOTWEAR
    {"title": "Black Running Shoes", "description": "High-performance black running shoes with cushioned sole", "color": "black", "category": "footwear"},
    {"title": "White Sneakers", "description": "Classic white canvas sneakers, versatile everyday shoes", "color": "white", "category": "footwear"},
    {"title": "Red Casual Sneakers", "description": "Trendy red sneakers with comfortable lining", "color": "red", "category": "footwear"},
    {"title": "Blue Leather Boots", "description": "Stylish blue leather boots for casual or formal wear", "color": "blue", "category": "footwear"},
    {"title": "Brown Hiking Boots", "description": "Rugged brown hiking boots with excellent grip and support", "color": "brown", "category": "footwear"},
    {"title": "Black Flip Flops", "description": "Comfortable black flip flops for beach and casual wear", "color": "black", "category": "footwear"},
    {"title": "Gray Sports Sandals", "description": "Durable gray sports sandals perfect for outdoor activities", "color": "gray", "category": "footwear"},
    {"title": "Gold Heels", "description": "Elegant gold high heels for special occasions", "color": "gold", "category": "footwear"},
    
    # ACCESSORIES
    {"title": "Black Leather Belt", "description": "Premium black leather belt with silver buckle", "color": "black", "category": "accessories"},
    {"title": "Blue Denim Backpack", "description": "Spacious blue denim backpack with multiple compartments", "color": "blue", "category": "accessories"},
    {"title": "Red Shoulder Bag", "description": "Stylish red shoulder bag with adjustable strap", "color": "red", "category": "accessories"},
    {"title": "Black Crossbody Bag", "description": "Practical black crossbody bag for everyday use", "color": "black", "category": "accessories"},
    {"title": "Brown Leather Handbag", "description": "Classic brown leather handbag with spacious interior", "color": "brown", "category": "accessories"},
    {"title": "Green Tote Bag", "description": "Eco-friendly green tote bag for shopping and travel", "color": "green", "category": "accessories"},
    {"title": "White Scarf", "description": "Elegant white silk scarf for any occasion", "color": "white", "category": "accessories"},
    {"title": "Black Sun Hat", "description": "Stylish black sun hat with wide brim for UV protection", "color": "black", "category": "accessories"},
    {"title": "Red Baseball Cap", "description": "Classic red baseball cap with adjustable back", "color": "red", "category": "accessories"},
    
    # ELECTRONICS
    {"title": "Black Smartphone", "description": "Latest black smartphone with large display and fast processor", "color": "black", "category": "electronics"},
    {"title": "Silver Laptop", "description": "Sleek silver laptop with powerful specs for work", "color": "silver", "category": "electronics"},
    {"title": "Blue Wireless Earbuds", "description": "Premium blue wireless earbuds with noise cancellation", "color": "blue", "category": "electronics"},
    {"title": "Black Smartwatch", "description": "Modern black smartwatch with fitness tracking features", "color": "black", "category": "electronics"},
    {"title": "White Tablet", "description": "Portable white tablet perfect for media consumption", "color": "white", "category": "electronics"},
    {"title": "Black Gaming Headset", "description": "Professional black gaming headset with surround sound", "color": "black", "category": "electronics"},
    {"title": "Gray Portable Speaker", "description": "Compact gray portable speaker with excellent sound quality", "color": "gray", "category": "electronics"},
    {"title": "Red USB Hub", "description": "Multi-port red USB hub for connectivity", "color": "red", "category": "electronics"},
    
    # HOME & FURNITURE
    {"title": "Black Coffee Table", "description": "Modern black coffee table with minimalist design", "color": "black", "category": "furniture"},
    {"title": "White Bookshelf", "description": "Spacious white bookshelf for organizing books and decor", "color": "white", "category": "furniture"},
    {"title": "Brown Wooden Chair", "description": "Comfortable brown wooden chair for reading", "color": "brown", "category": "furniture"},
    {"title": "Gray Office Desk", "description": "Professional gray office desk with drawers", "color": "gray", "category": "furniture"},
    {"title": "Blue Sofa", "description": "Comfortable blue sofa perfect for family gatherings", "color": "blue", "category": "furniture"},
    {"title": "Black TV Stand", "description": "Sleek black TV stand with storage compartments", "color": "black", "category": "furniture"},
    {"title": "White Bed Frame", "description": "Clean white bed frame for contemporary bedrooms", "color": "white", "category": "furniture"},
    
    # SPORTS & OUTDOOR
    {"title": "Black Bicycle", "description": "Lightweight black bicycle for commuting and recreation", "color": "black", "category": "sports"},
    {"title": "Blue Soccer Ball", "description": "Official blue soccer ball for matches and practice", "color": "blue", "category": "sports"},
    {"title": "Red Basketball", "description": "Professional red basketball with excellent grip", "color": "red", "category": "sports"},
    {"title": "Black Tennis Racket", "description": "High-performance black tennis racket for serious players", "color": "black", "category": "sports"},
    {"title": "Green Yoga Mat", "description": "Eco-friendly green yoga mat with non-slip surface", "color": "green", "category": "sports"},
    {"title": "Black Dumbbells", "description": "Set of black dumbbells for home fitness training", "color": "black", "category": "sports"},
    {"title": "Blue Skateboard", "description": "Trendy blue skateboard for tricks and cruising", "color": "blue", "category": "sports"},
    
    # BEAUTY & PERSONAL CARE
    {"title": "Black Hair Dryer", "description": "Professional black hair dryer with ionic technology", "color": "black", "category": "beauty"},
    {"title": "White Toothbrush", "description": "Electric white toothbrush with smart features", "color": "white", "category": "beauty"},
    {"title": "Red Lipstick", "description": "Classic red lipstick with long-lasting formula", "color": "red", "category": "beauty"},
    {"title": "Blue Face Mask Pack", "description": "Soothing blue face masks for skincare routine", "color": "blue", "category": "beauty"},
    {"title": "Pink Makeup Brush Set", "description": "Complete pink makeup brush set for professional application", "color": "pink", "category": "beauty"},
    
    # TOYS & GAMES
    {"title": "Black Jeep Toy", "description": "Detailed die-cast black jeep model toy for collectors", "color": "black", "category": "toys"},
    {"title": "Red Race Car", "description": "Fast red race car toy with realistic wheels", "color": "red", "category": "toys"},
    {"title": "Green Piano Keyboard", "description": "Educational green piano keyboard with 61 keys", "color": "green", "category": "toys"},
    {"title": "Blue Building Blocks Set", "description": "Creative blue building blocks set for children", "color": "blue", "category": "toys"},
    {"title": "Black Chess Set", "description": "Classic black and white chess set for strategy gaming", "color": "black", "category": "toys"},
    {"title": "White Puzzle", "description": "Challenging white puzzle with 1000 pieces", "color": "white", "category": "toys"},
    
    # KITCHEN & DINING
    {"title": "Black Coffee Maker", "description": "Modern black coffee maker for brewing perfect coffee", "color": "black", "category": "kitchen"},
    {"title": "Silver Blender", "description": "Powerful silver blender for smoothies and cooking", "color": "silver", "category": "kitchen"},
    {"title": "Red Toaster", "description": "Retro red toaster with multiple settings", "color": "red", "category": "kitchen"},
    {"title": "White Microwave", "description": "Compact white microwave for quick cooking", "color": "white", "category": "kitchen"},
    {"title": "Black Frying Pan", "description": "Non-stick black frying pan for healthy cooking", "color": "black", "category": "kitchen"},
    {"title": "Blue Dinnerware Set", "description": "Beautiful blue dinnerware set for 4 people", "color": "blue", "category": "kitchen"},
    
    # BOOKS & MEDIA
    {"title": "Black Notebook", "description": "Premium black notebook for journaling and notes", "color": "black", "category": "books"},
    {"title": "Red Book Collection", "description": "Set of classic red books for literature enthusiasts", "color": "red", "category": "books"},
    {"title": "Blue Pen Set", "description": "Professional blue pen set for writing", "color": "blue", "category": "books"},
    {"title": "White Desk Lamp", "description": "Bright white desk lamp for focused reading", "color": "white", "category": "books"},
    
    # PETS & ANIMALS
    {"title": "Black Dog Collar", "description": "Durable black dog collar with adjustable size", "color": "black", "category": "pets"},
    {"title": "Red Pet Bed", "description": "Comfortable red pet bed for dogs and cats", "color": "red", "category": "pets"},
    {"title": "Blue Leash", "description": "Strong blue leash for safe pet walking", "color": "blue", "category": "pets"},
    {"title": "Green Pet Toy", "description": "Interactive green pet toy for playtime", "color": "green", "category": "pets"},
    
    # VEHICLES & TRANSPORT
    {"title": "Black Car Model", "description": "Realistic black car model for collectors", "color": "black", "category": "vehicles"},
    {"title": "Red Motorcycle Toy", "description": "Detailed red motorcycle toy with moving parts", "color": "red", "category": "vehicles"},
    {"title": "Blue Airplane Model", "description": "Authentic blue airplane model for enthusiasts", "color": "blue", "category": "vehicles"},
    {"title": "Green Bus Toy", "description": "Classic green bus toy for children", "color": "green", "category": "vehicles"},
    
    # JEWELRY & WATCHES
    {"title": "Black Leather Watch", "description": "Elegant black leather watch with minimalist design", "color": "black", "category": "jewelry"},
    {"title": "Gold Bracelet", "description": "Stylish gold bracelet with fine links", "color": "gold", "category": "jewelry"},
    {"title": "Silver Necklace", "description": "Delicate silver necklace with pendant", "color": "silver", "category": "jewelry"},
    {"title": "Red Gemstone Ring", "description": "Beautiful red gemstone ring for special occasions", "color": "red", "category": "jewelry"},
    {"title": "Blue Stainless Watch", "description": "Modern blue stainless steel watch with date display", "color": "blue", "category": "jewelry"},
    
    # DECORATIONS & HOME DECOR
    {"title": "Black Picture Frame", "description": "Sleek black picture frame for wall art", "color": "black", "category": "decor"},
    {"title": "Red Wall Clock", "description": "Stylish red wall clock for modern interiors", "color": "red", "category": "decor"},
    {"title": "White Vase", "description": "Elegant white vase for fresh flowers", "color": "white", "category": "decor"},
    {"title": "Blue Throw Pillow", "description": "Comfortable blue throw pillow for couches", "color": "blue", "category": "decor"},
    {"title": "Green Plant Pot", "description": "Eco-friendly green plant pot for indoor plants", "color": "green", "category": "decor"},
    {"title": "Gold Candle Holder", "description": "Decorative gold candle holder for ambiance", "color": "gold", "category": "decor"},
]

def populate_database():
    """Generate and populate the Weaviate database with sample products."""
    clip_service = get_clip_service()
    
    with WeaviateConnection() as client:
        # Clear existing data
        print("Clearing existing products...")
        try:
            client.delete_collection()
            print("✓ Deleted old collection")
        except Exception as e:
            print(f"Note: {e}")
        
        # Create schema
        print("Creating schema...")
        client.create_product_schema()
        
        # Add products
        print(f"\nAdding {len(COMPREHENSIVE_PRODUCTS)} products to database...")
        print("=" * 60)
        
        successful = 0
        failed = 0
        
        for i, product_template in enumerate(COMPREHENSIVE_PRODUCTS, 1):
            try:
                # Generate embedding from title and description
                text_to_embed = f"{product_template['title']}. {product_template['description']}"
                embedding = clip_service.embed_text(text_to_embed)
                
                # Insert product
                uuid = client.insert_product_with_vector(
                    properties={
                        "product_id": f"product_{i:03d}",
                        "title": product_template["title"],
                        "description": product_template["description"],
                        "color": product_template["color"],
                        "category": product_template["category"],
                        "image_path": f"/images/{product_template['color']}-{product_template['category']}-{i}.jpg"
                    },
                    vector=embedding
                )
                
                successful += 1
                
                # Print progress every 10 products
                if i % 10 == 0:
                    status = f"[{i}/{len(COMPREHENSIVE_PRODUCTS)}]"
                    print(f"{status} Added: {product_template['title']}")
                    
            except Exception as e:
                failed += 1
                print(f"✗ Failed to add '{product_template['title']}': {str(e)[:50]}")
        
        # Verify
        print("=" * 60)
        info = client.get_collection_info()
        total = info.get("total_objects", 0)
        
        print(f"\n✅ COMPLETE!")
        print(f"Successfully added: {successful} products")
        print(f"Failed: {failed} products")
        print(f"Total in database: {total} products")
        
        print(f"\n📦 Product Categories:")
        categories = {}
        for product in COMPREHENSIVE_PRODUCTS:
            cat = product["category"]
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in sorted(categories.items()):
            print(f"   • {cat.capitalize()}: {count} products")
        
        print(f"\n🎨 Available Colors:")
        colors = set(p["color"] for p in COMPREHENSIVE_PRODUCTS)
        print(f"   {', '.join(sorted(colors))}")
        
        print(f"\n🔍 Try searching for:")
        print(f"   • 'black jeep' - find toy vehicles")
        print(f"   • 'green piano' - find musical instruments")
        print(f"   • 'red dress' - find women's apparel")
        print(f"   • 'blue electronics' - find tech products")
        print(f"   • 'comfortable shoes' - find footwear")
        print(f"   • 'office furniture' - find desks and chairs")
        print(f"\n✨ Your multimodal search engine is ready!")

if __name__ == "__main__":
    populate_database()
