#!/usr/bin/env python
"""
Demo script for update_user_memory() function.
Shows how to track user interactions with recommendations.
"""
from db.user_service import UserProfileService
from datetime import datetime


def demo_basic_usage():
    """Demo 1: Basic usage - tracking a purchase."""
    print("\n" + "=" * 80)
    print("DEMO 1: Basic Usage - Tracking a Purchase")
    print("=" * 80)
    
    service = UserProfileService()
    service.connect()
    
    try:
        # Create a test user
        user_id = "demo_user_001"
        print(f"\n📝 Creating user: {user_id}")
        
        try:
            service.create_user_profile(
                user_id=user_id,
                preferred_colors=["black"],
                preferred_categories=["apparel"],
                price_range={"min": 30, "max": 100}
            )
            print(f"✓ User created")
        except ValueError:
            print(f"⚠ User already exists, continuing...")
        
        # Simulate a purchase
        purchased_product = {
            "title": "Blue Casual Shirt",
            "color": "blue",
            "category": "apparel",
            "price": 49.99,
            "description": "Comfortable cotton shirt"
        }
        
        print(f"\n🛒 User purchased: {purchased_product['title']}")
        
        # Update user memory
        updated = service.update_user_memory(user_id, purchased_product)
        
        if updated:
            print(f"\n✓ Updated user memory")
            print(f"  Purchase History: {updated['past_purchases']}")
            print(f"  Preferred Colors: {updated['preferred_colors']}")
            print(f"  Preferred Categories: {updated['preferred_categories']}")
            print(f"  Price Range: ${updated['price_range']['min']:.2f} - ${updated['price_range']['max']:.2f}")
        
    finally:
        service.disconnect()


def demo_recommendation_tracking():
    """Demo 2: Track multiple recommendation clicks."""
    print("\n" + "=" * 80)
    print("DEMO 2: Tracking Recommendation Clicks")
    print("=" * 80)
    
    service = UserProfileService()
    service.connect()
    
    try:
        user_id = "demo_user_002"
        
        # Create user
        try:
            service.create_user_profile(user_id=user_id)
            print(f"✓ Created user: {user_id}")
        except ValueError:
            print(f"⚠ User exists, continuing...")
        
        # Simulate user clicking multiple recommendations
        recommendations = [
            {
                "title": "Red Athletic Shoes",
                "color": "red",
                "category": "footwear",
                "price": 89.99
            },
            {
                "title": "Navy Blue Hoodie",
                "color": "navy",
                "category": "apparel",
                "price": 65.00
            },
            {
                "title": "Black Workout Leggings",
                "color": "black",
                "category": "apparel",
                "price": 45.00
            }
        ]
        
        print(f"\n📊 User clicked {len(recommendations)} recommendations:")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['title']} (${rec['price']:.2f})")
            updated = service.update_user_memory(user_id, rec)
            
            if updated:
                print(f"   ✓ Memory updated")
                print(f"   Colors: {updated['preferred_colors']}")
                print(f"   Categories: {updated['preferred_categories']}")
        
    finally:
        service.disconnect()


def demo_without_auto_update():
    """Demo 3: Add purchase without updating preferences (e.g., gift)."""
    print("\n" + "=" * 80)
    print("DEMO 3: Purchase Without Preference Update (Gift)")
    print("=" * 80)
    
    service = UserProfileService()
    service.connect()
    
    try:
        user_id = "demo_user_003"
        
        # Create user with specific preferences
        try:
            service.create_user_profile(
                user_id=user_id,
                preferred_colors=["blue", "black"],
                preferred_categories=["apparel"]
            )
            print(f"✓ Created user with preferences: blue, black, apparel")
        except ValueError:
            print(f"⚠ User exists")
        
        # User buys a gift (not their style)
        gift_product = {
            "title": "Pink Floral Dress",
            "color": "pink",
            "category": "dresses",
            "price": 79.99
        }
        
        print(f"\n🎁 User purchased gift: {gift_product['title']}")
        print(f"   (Not their style - should not update preferences)")
        
        # Update without auto-preferences
        updated = service.update_user_memory(
            user_id, 
            gift_product, 
            auto_update_preferences=False
        )
        
        if updated:
            print(f"\n✓ Purchase recorded but preferences unchanged")
            print(f"  Purchase History: {updated['past_purchases']}")
            print(f"  Preferred Colors: {updated['preferred_colors']}")
            print(f"  ⚠ Notice: Pink NOT added to colors (as intended)")
        
    finally:
        service.disconnect()


def demo_price_range_expansion():
    """Demo 4: Price range expansion with expensive purchase."""
    print("\n" + "=" * 80)
    print("DEMO 4: Price Range Expansion")
    print("=" * 80)
    
    service = UserProfileService()
    service.connect()
    
    try:
        user_id = "demo_user_004"
        
        # Create user with narrow price range
        try:
            service.create_user_profile(
                user_id=user_id,
                price_range={"min": 20, "max": 60}
            )
            print(f"✓ Created user with price range: $20 - $60")
        except ValueError:
            print(f"⚠ User exists")
        
        # Show initial range
        initial = service.get_user_profile(user_id)
        print(f"\nInitial price range: ${initial['price_range']['min']:.2f} - ${initial['price_range']['max']:.2f}")
        
        # Purchase expensive item
        expensive_product = {
            "title": "Designer Leather Jacket",
            "color": "brown",
            "category": "outerwear",
            "price": 299.99
        }
        
        print(f"\n💰 User purchased expensive item: {expensive_product['title']}")
        print(f"   Price: ${expensive_product['price']:.2f} (above current max)")
        
        updated = service.update_user_memory(user_id, expensive_product)
        
        if updated:
            print(f"\n✓ Price range expanded automatically")
            print(f"  New range: ${updated['price_range']['min']:.2f} - ${updated['price_range']['max']:.2f}")
            print(f"  Maximum increased from $60 to ${updated['price_range']['max']:.2f}")
        
    finally:
        service.disconnect()


def demo_new_user_creation():
    """Demo 5: Auto-create user if not exists."""
    print("\n" + "=" * 80)
    print("DEMO 5: Auto-Create User if Not Exists")
    print("=" * 80)
    
    service = UserProfileService()
    service.connect()
    
    try:
        # Use a random user ID that doesn't exist
        new_user_id = f"new_user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        print(f"📝 Attempting to update memory for non-existent user: {new_user_id}")
        
        product = {
            "title": "First Purchase",
            "color": "green",
            "category": "apparel",
            "price": 39.99
        }
        
        # This will auto-create the user
        updated = service.update_user_memory(new_user_id, product)
        
        if updated:
            print(f"\n✓ User auto-created and memory updated")
            print(f"  User ID: {updated['user_id']}")
            print(f"  Purchases: {updated['past_purchases']}")
            print(f"  Colors: {updated['preferred_colors']}")
            print(f"  Categories: {updated['preferred_categories']}")
            print(f"\n💡 User profile created on-the-fly!")
        
    finally:
        service.disconnect()


def demo_error_handling():
    """Demo 6: Error handling examples."""
    print("\n" + "=" * 80)
    print("DEMO 6: Error Handling")
    print("=" * 80)
    
    service = UserProfileService()
    service.connect()
    
    try:
        user_id = "demo_user_error"
        
        # Error 1: Product without title
        print("\n❌ Test 1: Product without title")
        invalid_product = {
            "color": "blue",
            "category": "apparel"
        }
        
        try:
            service.update_user_memory(user_id, invalid_product)
        except ValueError as e:
            print(f"   Caught error: {e}")
        
        # Success: Valid product
        print("\n✓ Test 2: Valid product")
        valid_product = {
            "title": "Valid Product",
            "color": "blue"
        }
        
        updated = service.update_user_memory(user_id, valid_product)
        if updated:
            print(f"   Success: {valid_product['title']} added")
        
        # Edge case: Empty strings
        print("\n⚠ Test 3: Product with empty strings (should handle gracefully)")
        edge_case = {
            "title": "Edge Case Product",
            "color": "",
            "category": "   "
        }
        
        updated = service.update_user_memory(user_id, edge_case)
        if updated:
            print(f"   Success: Handled empty values gracefully")
        
    finally:
        service.disconnect()


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("🎯 UPDATE_USER_MEMORY() FUNCTION DEMO")
    print("=" * 80)
    print("\nThis demo shows how to use update_user_memory() to track")
    print("user interactions with recommendations and purchases.")
    
    try:
        demo_basic_usage()
        demo_recommendation_tracking()
        demo_without_auto_update()
        demo_price_range_expansion()
        demo_new_user_creation()
        demo_error_handling()
        
        print("\n" + "=" * 80)
        print("✨ All demos completed!")
        print("=" * 80)
        
        print("\n💡 Key Takeaways:")
        print("  1. Always connect before using the service")
        print("  2. Product title is required, other fields optional")
        print("  3. Auto-updates preferences by default (can disable)")
        print("  4. Expands price range automatically")
        print("  5. Creates user if not exists")
        print("  6. Handles errors gracefully")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("   Make sure MongoDB is running!")


if __name__ == "__main__":
    main()
