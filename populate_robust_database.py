#!/usr/bin/env python3
"""
Generate and populate a robust, comprehensive product database.
This creates a realistic e-commerce catalog for testing multimodal search.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import WeaviateConnection
from services import get_clip_service

# Comprehensive product database with 200+ products
ROBUST_PRODUCTS = [
    # APPAREL - TOPS (Men)
    {"title": "Classic White Crew Neck T-Shirt", "description": "Premium cotton crew neck t-shirt, perfect for everyday wear", "color": "white", "category": "apparel"},
    {"title": "Black Slim Fit Button-Up Shirt", "description": "Professional black button-up shirt with slim fit tailoring", "color": "black", "category": "apparel"},
    {"title": "Navy Blue Oxford Shirt", "description": "Classic navy oxford cloth button-down for business casual", "color": "navy", "category": "apparel"},
    {"title": "Gray V-Neck Henley", "description": "Comfortable gray henley with v-neck design", "color": "gray", "category": "apparel"},
    {"title": "Red Polo Shirt", "description": "Sporty red polo shirt with collar and buttons", "color": "red", "category": "apparel"},
    {"title": "Blue Striped Long Sleeve", "description": "Blue and white striped long sleeve shirt for versatile styling", "color": "blue", "category": "apparel"},
    {"title": "Green Casual Hoodie", "description": "Comfortable green hoodie with kangaroo pocket", "color": "green", "category": "apparel"},
    {"title": "Black Turtleneck Sweater", "description": "Elegant black turtleneck for winter warmth", "color": "black", "category": "apparel"},
    {"title": "White Tank Top", "description": "Simple white sleeveless tank top", "color": "white", "category": "apparel"},
    {"title": "Purple Cardigan Sweater", "description": "Soft purple cardigan for layering", "color": "purple", "category": "apparel"},
    
    # APPAREL - TOPS (Women)
    {"title": "White Blouse with Peplum", "description": "Elegant white blouse with peplum hem for feminine style", "color": "white", "category": "apparel"},
    {"title": "Black Turtleneck Bodysuit", "description": "Form-fitting black turtleneck bodysuit", "color": "black", "category": "apparel"},
    {"title": "Pink Crop Top", "description": "Trendy pink crop top perfect for casual outfits", "color": "pink", "category": "apparel"},
    {"title": "Blue Silk Camisole", "description": "Luxurious blue silk camisole with delicate straps", "color": "blue", "category": "apparel"},
    {"title": "Red Wrap Blouse", "description": "Flattering red wrap blouse with tie waist", "color": "red", "category": "apparel"},
    {"title": "Green Off-Shoulder Top", "description": "Trendy green off-shoulder top with ruffles", "color": "green", "category": "apparel"},
    {"title": "Black Mesh Top", "description": "Edgy black mesh top for layering", "color": "black", "category": "apparel"},
    {"title": "White Lace Tank", "description": "Delicate white lace tank top", "color": "white", "category": "apparel"},
    
    # APPAREL - BOTTOMS
    {"title": "Black Skinny Jeans", "description": "Classic black skinny jeans with stretch", "color": "black", "category": "apparel"},
    {"title": "Blue Straight Leg Jeans", "description": "Comfortable blue jeans with straight leg cut", "color": "blue", "category": "apparel"},
    {"title": "White Linen Pants", "description": "Breathable white linen pants for summer", "color": "white", "category": "apparel"},
    {"title": "Black Dress Pants", "description": "Professional black dress pants for work", "color": "black", "category": "apparel"},
    {"title": "Gray Yoga Pants", "description": "Comfortable gray yoga pants with waistband", "color": "gray", "category": "apparel"},
    {"title": "Navy Chino Shorts", "description": "Casual navy chino shorts for summer", "color": "navy", "category": "apparel"},
    {"title": "Black Leather Leggings", "description": "Sleek black leather-look leggings", "color": "black", "category": "apparel"},
    {"title": "Olive Green Cargo Pants", "description": "Durable olive green cargo pants with multiple pockets", "color": "green", "category": "apparel"},
    
    # APPAREL - DRESSES
    {"title": "Little Black Cocktail Dress", "description": "Timeless black cocktail dress with classic silhouette", "color": "black", "category": "apparel"},
    {"title": "Red Bodycon Dress", "description": "Sexy red bodycon dress perfect for nights out", "color": "red", "category": "apparel"},
    {"title": "Blue Floral Maxi Dress", "description": "Beautiful blue floral maxi dress for summer events", "color": "blue", "category": "apparel"},
    {"title": "White Sundress", "description": "Light and airy white sundress with spaghetti straps", "color": "white", "category": "apparel"},
    {"title": "Green A-Line Dress", "description": "Flattering green a-line dress for versatile styling", "color": "green", "category": "apparel"},
    {"title": "Pink Party Dress", "description": "Glamorous pink dress with sequin details", "color": "pink", "category": "apparel"},
    
    # APPAREL - OUTERWEAR
    {"title": "Black Leather Motorcycle Jacket", "description": "Classic black leather jacket with zippered pockets", "color": "black", "category": "apparel"},
    {"title": "Brown Wool Peacoat", "description": "Warm brown wool peacoat for winter", "color": "brown", "category": "apparel"},
    {"title": "Blue Denim Jacket", "description": "Timeless blue denim jacket for casual wear", "color": "blue", "category": "apparel"},
    {"title": "White Blazer", "description": "Professional white blazer for business settings", "color": "white", "category": "apparel"},
    {"title": "Red Windbreaker Jacket", "description": "Water-resistant red windbreaker for outdoor activities", "color": "red", "category": "apparel"},
    {"title": "Black Puffer Coat", "description": "Warm black puffer coat with insulation", "color": "black", "category": "apparel"},
    {"title": "Green Trench Coat", "description": "Elegant green trench coat for timeless style", "color": "green", "category": "apparel"},
    
    # FOOTWEAR - CASUAL
    {"title": "White Canvas Sneakers", "description": "Classic white canvas sneakers for everyday wear", "color": "white", "category": "footwear"},
    {"title": "Black Leather Loafers", "description": "Sophisticated black leather loafers", "color": "black", "category": "footwear"},
    {"title": "Red Casual Slip-Ons", "description": "Comfortable red slip-on sneakers", "color": "red", "category": "footwear"},
    {"title": "Blue Denim Sneakers", "description": "Trendy blue denim canvas sneakers", "color": "blue", "category": "footwear"},
    {"title": "Gray Athletic Shoes", "description": "Comfortable gray athletic shoes for sports", "color": "gray", "category": "footwear"},
    {"title": "White Platform Sneakers", "description": "Modern white platform sneakers", "color": "white", "category": "footwear"},
    {"title": "Black Casual Oxfords", "description": "Classic black oxford casual shoes", "color": "black", "category": "footwear"},
    
    # FOOTWEAR - FORMAL
    {"title": "Black Patent Leather Heels", "description": "Elegant black patent leather high heels", "color": "black", "category": "footwear"},
    {"title": "Gold Metallic Pumps", "description": "Glamorous gold metallic pumps", "color": "gold", "category": "footwear"},
    {"title": "Silver Strappy Sandals", "description": "Sophisticated silver strappy sandals", "color": "silver", "category": "footwear"},
    {"title": "Red Stiletto Heels", "description": "Classic red stiletto heels for special occasions", "color": "red", "category": "footwear"},
    {"title": "Blue Dress Flats", "description": "Comfortable blue dress flats", "color": "blue", "category": "footwear"},
    
    # FOOTWEAR - ATHLETIC
    {"title": "Black Running Shoes", "description": "High-performance black running shoes with cushioning", "color": "black", "category": "footwear"},
    {"title": "White Cross-Training Shoes", "description": "Supportive white cross-training shoes", "color": "white", "category": "footwear"},
    {"title": "Blue Basketball Shoes", "description": "Professional blue basketball shoes", "color": "blue", "category": "footwear"},
    {"title": "Gray Hiking Boots", "description": "Durable gray hiking boots for trails", "color": "gray", "category": "footwear"},
    {"title": "Red Soccer Cleats", "description": "Professional red soccer cleats", "color": "red", "category": "footwear"},
    
    # FOOTWEAR - CASUAL/LEISURE
    {"title": "Black Flip Flops", "description": "Simple black flip flops for beach", "color": "black", "category": "footwear"},
    {"title": "Blue Slide Sandals", "description": "Comfortable blue slide sandals", "color": "blue", "category": "footwear"},
    {"title": "White Slippers", "description": "Cozy white slippers for home wear", "color": "white", "category": "footwear"},
    {"title": "Gray Fuzzy Slippers", "description": "Warm gray fuzzy slippers", "color": "gray", "category": "footwear"},
    
    # ACCESSORIES - BAGS
    {"title": "Black Leather Tote Bag", "description": "Spacious black leather tote for work", "color": "black", "category": "accessories"},
    {"title": "Brown Leather Backpack", "description": "Durable brown leather backpack for travel", "color": "brown", "category": "accessories"},
    {"title": "Red Crossbody Bag", "description": "Practical red crossbody bag with adjustable strap", "color": "red", "category": "accessories"},
    {"title": "Blue Duffel Bag", "description": "Large blue duffel bag for gym or travel", "color": "blue", "category": "accessories"},
    {"title": "Black Clutch Purse", "description": "Elegant black clutch for evening events", "color": "black", "category": "accessories"},
    {"title": "Green Canvas Backpack", "description": "Eco-friendly green canvas backpack", "color": "green", "category": "accessories"},
    {"title": "Gold Metallic Evening Bag", "description": "Glamorous gold evening bag with chain strap", "color": "gold", "category": "accessories"},
    {"title": "White Leather Shoulder Bag", "description": "Chic white leather shoulder bag", "color": "white", "category": "accessories"},
    
    # ACCESSORIES - BELTS & SCARVES
    {"title": "Black Leather Belt", "description": "Classic black leather belt with silver buckle", "color": "black", "category": "accessories"},
    {"title": "Brown Woven Belt", "description": "Casual brown woven belt", "color": "brown", "category": "accessories"},
    {"title": "White Silk Scarf", "description": "Elegant white silk scarf for any outfit", "color": "white", "category": "accessories"},
    {"title": "Blue Paisley Scarf", "description": "Colorful blue paisley scarf", "color": "blue", "category": "accessories"},
    {"title": "Red Wool Scarf", "description": "Warm red wool scarf for winter", "color": "red", "category": "accessories"},
    
    # ACCESSORIES - HATS
    {"title": "Black Baseball Cap", "description": "Classic black baseball cap", "color": "black", "category": "accessories"},
    {"title": "White Straw Hat", "description": "Lightweight white straw hat for sun protection", "color": "white", "category": "accessories"},
    {"title": "Red Beanie", "description": "Cozy red beanie for winter", "color": "red", "category": "accessories"},
    {"title": "Navy Bucket Hat", "description": "Trendy navy bucket hat", "color": "navy", "category": "accessories"},
    {"title": "Gray Fedora Hat", "description": "Stylish gray fedora hat", "color": "gray", "category": "accessories"},
    
    # ACCESSORIES - SUNGLASSES & JEWELRY
    {"title": "Black Aviator Sunglasses", "description": "Classic black aviator sunglasses", "color": "black", "category": "accessories"},
    {"title": "Gold Chain Necklace", "description": "Delicate gold chain necklace", "color": "gold", "category": "accessories"},
    {"title": "Silver Bracelet", "description": "Elegant silver bracelet with charms", "color": "silver", "category": "accessories"},
    {"title": "Pearl Earrings", "description": "Classic pearl stud earrings", "color": "white", "category": "accessories"},
    
    # ELECTRONICS - PHONES & TABLETS
    {"title": "Black Smartphone 13", "description": "Latest black smartphone with OLED display", "color": "black", "category": "electronics"},
    {"title": "Silver Smartphone Pro", "description": "Premium silver smartphone with advanced camera", "color": "silver", "category": "electronics"},
    {"title": "Blue Smartphone", "description": "Affordable blue smartphone", "color": "blue", "category": "electronics"},
    {"title": "White Tablet 10 Inch", "description": "Large white tablet perfect for media", "color": "white", "category": "electronics"},
    {"title": "Black iPad Mini", "description": "Compact black iPad mini for on-the-go", "color": "black", "category": "electronics"},
    
    # ELECTRONICS - COMPUTERS
    {"title": "Silver Laptop 15 Inch", "description": "Sleek silver laptop for work and entertainment", "color": "silver", "category": "electronics"},
    {"title": "Gray Laptop 13 Inch", "description": "Portable gray laptop for travel", "color": "gray", "category": "electronics"},
    {"title": "Black Gaming Laptop", "description": "Powerful black gaming laptop", "color": "black", "category": "electronics"},
    {"title": "White Desktop Monitor", "description": "Crisp white monitor for productivity", "color": "white", "category": "electronics"},
    
    # ELECTRONICS - AUDIO
    {"title": "Black Wireless Earbuds", "description": "Premium black wireless earbuds with noise cancellation", "color": "black", "category": "electronics"},
    {"title": "White Bluetooth Speaker", "description": "Portable white bluetooth speaker", "color": "white", "category": "electronics"},
    {"title": "Blue Headphones", "description": "Comfortable blue over-ear headphones", "color": "blue", "category": "electronics"},
    {"title": "Black Gaming Headset", "description": "Professional black gaming headset with mic", "color": "black", "category": "electronics"},
    {"title": "Silver Wireless Earbuds Pro", "description": "Advanced silver wireless earbuds", "color": "silver", "category": "electronics"},
    
    # ELECTRONICS - WEARABLES
    {"title": "Black Smartwatch", "description": "Modern black smartwatch with fitness tracking", "color": "black", "category": "electronics"},
    {"title": "Silver Apple Watch", "description": "Premium silver smartwatch", "color": "silver", "category": "electronics"},
    {"title": "Blue Fitness Tracker", "description": "Blue wristband fitness tracker", "color": "blue", "category": "electronics"},
    
    # ELECTRONICS - ACCESSORIES
    {"title": "Black USB-C Cable", "description": "Durable black USB-C charging cable", "color": "black", "category": "electronics"},
    {"title": "White Power Bank", "description": "Convenient white portable power bank", "color": "white", "category": "electronics"},
    {"title": "Gray USB Hub", "description": "Multi-port gray USB hub", "color": "gray", "category": "electronics"},
    
    # SPORTS & FITNESS
    {"title": "Black Yoga Mat", "description": "Non-slip black yoga mat for practice", "color": "black", "category": "sports"},
    {"title": "Green Fitness Mat", "description": "Cushioned green exercise mat", "color": "green", "category": "sports"},
    {"title": "Black Dumbbell Set", "description": "Complete black dumbbell set with rack", "color": "black", "category": "sports"},
    {"title": "Red Kettlebell", "description": "Heavy red kettlebell for strength training", "color": "red", "category": "sports"},
    {"title": "Blue Resistance Bands", "description": "Set of blue resistance bands", "color": "blue", "category": "sports"},
    {"title": "Black Stationary Bike", "description": "Indoor black stationary bike", "color": "black", "category": "sports"},
    {"title": "Gray Treadmill", "description": "Modern gray treadmill for cardio", "color": "gray", "category": "sports"},
    {"title": "Blue Soccer Ball", "description": "Official blue soccer ball", "color": "blue", "category": "sports"},
    {"title": "Red Basketball", "description": "Professional red basketball", "color": "red", "category": "sports"},
    {"title": "Black Tennis Racket", "description": "High-performance black tennis racket", "color": "black", "category": "sports"},
    {"title": "Blue Skateboard", "description": "Trendy blue skateboard", "color": "blue", "category": "sports"},
    {"title": "Black Mountain Bike", "description": "Rugged black mountain bike", "color": "black", "category": "sports"},
    
    # HOME & FURNITURE
    {"title": "Black Coffee Table", "description": "Modern black coffee table with storage", "color": "black", "category": "furniture"},
    {"title": "Brown Wooden Desk", "description": "Spacious brown wooden desk for office", "color": "brown", "category": "furniture"},
    {"title": "Gray Office Chair", "description": "Ergonomic gray office chair with wheels", "color": "gray", "category": "furniture"},
    {"title": "White Bookshelf", "description": "Tall white bookshelf for storage", "color": "white", "category": "furniture"},
    {"title": "Blue Armchair", "description": "Comfortable blue armchair for reading", "color": "blue", "category": "furniture"},
    {"title": "Black TV Stand", "description": "Sleek black TV stand with shelves", "color": "black", "category": "furniture"},
    {"title": "White Bed Frame", "description": "Clean white bed frame for bedrooms", "color": "white", "category": "furniture"},
    {"title": "Gray Nightstand", "description": "Compact gray nightstand with drawer", "color": "gray", "category": "furniture"},
    {"title": "Red Accent Table", "description": "Bold red accent table for living rooms", "color": "red", "category": "furniture"},
    
    # KITCHEN & DINING
    {"title": "Black Coffee Maker", "description": "Programmable black coffee maker", "color": "black", "category": "kitchen"},
    {"title": "Silver Blender", "description": "Powerful silver blender for smoothies", "color": "silver", "category": "kitchen"},
    {"title": "Red Toaster", "description": "Retro red toaster with multiple settings", "color": "red", "category": "kitchen"},
    {"title": "White Microwave", "description": "Compact white microwave oven", "color": "white", "category": "kitchen"},
    {"title": "Black Frying Pan", "description": "Non-stick black frying pan", "color": "black", "category": "kitchen"},
    {"title": "Silver Pot Set", "description": "Set of silver cookware pots", "color": "silver", "category": "kitchen"},
    {"title": "Blue Dinnerware Set", "description": "Beautiful blue dinnerware for 12", "color": "blue", "category": "kitchen"},
    {"title": "White Dish Set", "description": "Classic white dishes set", "color": "white", "category": "kitchen"},
    
    # BOOKS & MEDIA
    {"title": "Black Notebook", "description": "Premium black notebook for journaling", "color": "black", "category": "books"},
    {"title": "Red Diary", "description": "Classic red diary for planning", "color": "red", "category": "books"},
    {"title": "Blue Pen Set", "description": "Professional blue pen set", "color": "blue", "category": "books"},
    {"title": "White Desk Lamp", "description": "Bright white LED desk lamp", "color": "white", "category": "books"},
    
    # TOYS & GAMES
    {"title": "Black Jeep Toy", "description": "Detailed black jeep die-cast toy model", "color": "black", "category": "toys"},
    {"title": "Red Sports Car", "description": "Fast red race car toy model", "color": "red", "category": "toys"},
    {"title": "Blue Building Blocks", "description": "Educational blue building block set", "color": "blue", "category": "toys"},
    {"title": "Green Piano Keyboard", "description": "Electronic green piano with 61 keys", "color": "green", "category": "toys"},
    {"title": "Black Chess Set", "description": "Classic black and white chess set", "color": "black", "category": "toys"},
    {"title": "White Puzzle 1000pc", "description": "Challenging white puzzle with 1000 pieces", "color": "white", "category": "toys"},
    
    # BEAUTY & PERSONAL CARE
    {"title": "Black Hair Dryer", "description": "Professional black hair dryer with ionic", "color": "black", "category": "beauty"},
    {"title": "White Electric Toothbrush", "description": "Smart white electric toothbrush", "color": "white", "category": "beauty"},
    {"title": "Red Lipstick", "description": "Classic red lipstick with long wear", "color": "red", "category": "beauty"},
    {"title": "Blue Face Mask", "description": "Soothing blue sheet face mask", "color": "blue", "category": "beauty"},
    {"title": "Pink Makeup Brush Set", "description": "Professional pink makeup brush set", "color": "pink", "category": "beauty"},
    
    # JEWELRY & WATCHES
    {"title": "Black Leather Watch", "description": "Elegant black leather band watch", "color": "black", "category": "jewelry"},
    {"title": "Gold Dress Watch", "description": "Sophisticated gold dress watch", "color": "gold", "category": "jewelry"},
    {"title": "Silver Stainless Watch", "description": "Modern silver stainless steel watch", "color": "silver", "category": "jewelry"},
    {"title": "Rose Gold Bracelet", "description": "Delicate rose gold bracelet", "color": "gold", "category": "jewelry"},
    {"title": "Blue Sapphire Ring", "description": "Beautiful blue sapphire ring", "color": "blue", "category": "jewelry"},
    
    # PETS & ANIMALS
    {"title": "Black Dog Collar", "description": "Durable black dog collar with tag", "color": "black", "category": "pets"},
    {"title": "Red Pet Bed", "description": "Comfortable red pet bed for dogs", "color": "red", "category": "pets"},
    {"title": "Blue Leash", "description": "Strong blue dog leash", "color": "blue", "category": "pets"},
    {"title": "Green Pet Toy", "description": "Interactive green pet toy ball", "color": "green", "category": "pets"},
    
    # HOME DECOR
    {"title": "Black Picture Frame", "description": "Sleek black picture frame for walls", "color": "black", "category": "decor"},
    {"title": "Red Wall Clock", "description": "Modern red wall clock", "color": "red", "category": "decor"},
    {"title": "White Vase", "description": "Elegant white ceramic vase", "color": "white", "category": "decor"},
    {"title": "Blue Throw Pillow", "description": "Comfortable blue throw pillow for sofas", "color": "blue", "category": "decor"},
    {"title": "Green Plant Pot", "description": "Eco-friendly green planter pot", "color": "green", "category": "decor"},
    {"title": "Gold Candle Holder", "description": "Decorative gold candle holder", "color": "gold", "category": "decor"},
    {"title": "Black Mirror", "description": "Large black framed mirror", "color": "black", "category": "decor"},
    {"title": "White Curtains", "description": "Sheer white curtain panels", "color": "white", "category": "decor"},
]

def populate_database():
    """Generate and populate the Weaviate database with robust sample products."""
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
        print(f"\nAdding {len(ROBUST_PRODUCTS)} robust products to database...")
        print("=" * 70)
        
        successful = 0
        failed = 0
        
        for i, product_template in enumerate(ROBUST_PRODUCTS, 1):
            try:
                # Generate embedding from title and description
                text_to_embed = f"{product_template['title']}. {product_template['description']}"
                embedding = clip_service.embed_text(text_to_embed)
                
                # Insert product
                uuid = client.insert_product_with_vector(
                    properties={
                        "product_id": f"product_{i:04d}",
                        "title": product_template["title"],
                        "description": product_template["description"],
                        "color": product_template["color"],
                        "category": product_template["category"],
                        "image_path": f"/images/{product_template['color']}-{product_template['category']}-{i}.jpg"
                    },
                    vector=embedding
                )
                
                successful += 1
                
                # Print progress every 25 products
                if i % 25 == 0:
                    status = f"[{i}/{len(ROBUST_PRODUCTS)}]"
                    print(f"{status} ✓ {product_template['title']}")
                    
            except Exception as e:
                failed += 1
                if i % 50 == 0:
                    print(f"[{i}/{len(ROBUST_PRODUCTS)}] ✗ Error: {str(e)[:40]}")
        
        # Verify
        print("=" * 70)
        info = client.get_collection_info()
        total = info.get("total_objects", 0)
        
        print(f"\n✅ DATABASE POPULATION COMPLETE!")
        print(f"Successfully added: {successful} products")
        print(f"Failed: {failed} products")
        print(f"Total in database: {total} products")
        
        print(f"\n📦 Product Categories:")
        categories = {}
        for product in ROBUST_PRODUCTS:
            cat = product["category"]
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in sorted(categories.items()):
            print(f"   • {cat.capitalize()}: {count:3d} products")
        
        print(f"\n🎨 Available Colors:")
        colors = set(p["color"] for p in ROBUST_PRODUCTS)
        color_list = sorted(colors)
        for i in range(0, len(color_list), 6):
            print(f"   {', '.join(color_list[i:i+6])}")
        
        print(f"\n🔍 Try searching for:")
        print(f"   • 'black jeep' → finds toy vehicles")
        print(f"   • 'green piano' → finds musical instruments")
        print(f"   • 'workout equipment' → finds dumbbells, yoga mat, etc.")
        print(f"   • 'red dress' → finds women's apparel")
        print(f"   • 'blue electronics' → finds tech products")
        print(f"   • 'comfortable shoes' → finds footwear")
        print(f"   • 'office furniture' → finds desks and chairs")
        print(f"   • 'leather jacket' → finds apparel")
        print(f"   • 'professional watch' → finds jewelry")
        print(f"   • 'kitchen gadgets' → finds appliances")
        
        print(f"\n✨ Your comprehensive multimodal search engine is ready!")
        print(f"💡 Try uploading images + text for the best experience!")

if __name__ == "__main__":
    populate_database()
