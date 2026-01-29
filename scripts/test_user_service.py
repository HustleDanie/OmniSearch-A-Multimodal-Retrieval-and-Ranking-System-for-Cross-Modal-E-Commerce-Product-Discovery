"""
Test script for user profile service functionality.
Demonstrates create, retrieve, and update operations.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.user_service import UserProfileService
from models.user import UserProfile, UserPreferences


def test_user_profile_service():
    """Test UserProfileService CRUD operations."""
    
    print("\n" + "="*70)
    print("USER PROFILE SERVICE TEST")
    print("="*70 + "\n")
    
    # Initialize service
    service = UserProfileService()
    
    try:
        # Connect to MongoDB
        print("1. Connecting to MongoDB...")
        service.connect()
        
        # Create user profiles
        print("\n2. Creating user profiles...")
        user1 = service.create_user_profile(
            user_id="USER-001",
            past_purchases=["Blue Running Shoes", "Cotton T-Shirt"],
            preferred_colors=["blue", "black", "gray"],
            preferred_categories=["footwear", "apparel"],
            price_range={"min": 20, "max": 200}
        )
        print(f"   Created: {user1['user_id']}")
        print(f"   Preferred colors: {user1['preferred_colors']}")
        print(f"   Price range: ${user1['price_range']['min']}-${user1['price_range']['max']}")
        
        user2 = service.create_user_profile(
            user_id="USER-002",
            past_purchases=["Red Dress", "Black Handbag"],
            preferred_colors=["red", "burgundy", "pink"],
            preferred_categories=["apparel", "accessories"],
            price_range={"min": 50, "max": 300}
        )
        print(f"   Created: {user2['user_id']}")
        
        # Retrieve user profile
        print("\n3. Retrieving user profile...")
        retrieved = service.get_user_profile("USER-001")
        print(f"   Retrieved: {retrieved['user_id']}")
        print(f"   Past purchases: {retrieved['past_purchases']}")
        print(f"   Preferred categories: {retrieved['preferred_categories']}")
        
        # Update preferences
        print("\n4. Updating user preferences...")
        updated = service.update_preferences(
            user_id="USER-001",
            preferred_colors=["blue", "teal", "navy"],
            price_range={"min": 25, "max": 250}
        )
        print(f"   Updated: {updated['user_id']}")
        print(f"   New preferred colors: {updated['preferred_colors']}")
        print(f"   New price range: ${updated['price_range']['min']}-${updated['price_range']['max']}")
        
        # Add purchase
        print("\n5. Adding purchase to user...")
        updated = service.add_purchase("USER-001", "Summer Dress")
        print(f"   Updated purchases: {updated['past_purchases']}")
        
        # Get all users
        print("\n6. Fetching all user profiles...")
        all_users = service.get_all_users()
        print(f"   Total users: {len(all_users)}")
        for user in all_users:
            print(f"   - {user['user_id']}: {len(user['past_purchases'])} purchases")
        
        # Try to create duplicate (should fail)
        print("\n7. Testing duplicate user creation (should fail)...")
        try:
            service.create_user_profile(user_id="USER-001")
            print("   ✗ Unexpectedly succeeded!")
        except ValueError as e:
            print(f"   ✓ Correctly rejected: {e}")
        
        # Get non-existent user
        print("\n8. Retrieving non-existent user...")
        result = service.get_user_profile("USER-999")
        print(f"   Result: {result}")
        
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        raise
    
    finally:
        # Disconnect
        service.disconnect()


def test_context_manager():
    """Test UserProfileService as context manager."""
    
    print("\n" + "="*70)
    print("CONTEXT MANAGER TEST")
    print("="*70 + "\n")
    
    try:
        with UserProfileService() as service:
            print("✓ Connected via context manager")
            
            # Get all users
            users = service.get_all_users()
            print(f"✓ Retrieved {len(users)} users")
        
        print("✓ Disconnected via context manager")
        print("\n" + "="*70)
        print("✓ CONTEXT MANAGER TEST PASSED")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Context manager test failed: {e}")
        raise


if __name__ == "__main__":
    try:
        test_user_profile_service()
        test_context_manager()
        print("\n✅ ALL TESTS COMPLETED SUCCESSFULLY\n")
    except KeyboardInterrupt:
        print("\n\n⚠ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ TESTS FAILED: {e}")
        exit(1)
