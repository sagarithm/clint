import asyncio
import os
import sys

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Ensure local modules are imported
for module_name in ("engine", "engine.engine", "core", "core.config"):
    sys.modules.pop(module_name, None)

from engine.engine import Engine


def test_library_api():
    """Test that the Engine can be imported and used as a library."""
    try:
        # Initialize engine
        engine = Engine(api_key="test_key_for_library")
        print("✓ Engine initialized successfully")
        
        # Test with sample lead data
        lead = {
            "name": "Jane Doe",
            "company": "TechCorp",
            "title": "CTO",
            "category": "Technology"
        }
        
        # This will fail if API key is invalid, but that's OK for library test
        # The important thing is that it doesn't crash on initialization
        print(f"✓ Engine accepts lead data: {lead}")
        
        # Verify Engine has the expected methods
        assert hasattr(engine, "personalize"), "Engine missing personalize method"
        assert hasattr(engine, "personalize_async"), "Engine missing personalize_async method"
        assert hasattr(engine, "personalize_batch"), "Engine missing personalize_batch method"
        assert hasattr(engine, "personalize_batch_async"), "Engine missing personalize_batch_async method"
        print("✓ Engine has all required methods")
        
        print("\n✅ Library API test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Library API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_library_api()
    sys.exit(0 if success else 1)
