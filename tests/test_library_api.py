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
    engine = Engine(api_key="test_key_for_library")
    print("✓ Engine initialized successfully")

    lead = {
        "name": "Jane Doe",
        "company": "TechCorp",
        "title": "CTO",
        "category": "Technology",
    }

    print(f"✓ Engine accepts lead data: {lead}")

    assert hasattr(engine, "personalize"), "Engine missing personalize method"
    assert hasattr(engine, "personalize_async"), "Engine missing personalize_async method"
    assert hasattr(engine, "personalize_batch"), "Engine missing personalize_batch method"
    assert hasattr(engine, "personalize_batch_async"), "Engine missing personalize_batch_async method"
    print("✓ Engine has all required methods")

    print("\n✅ Library API test passed!")


if __name__ == "__main__":
    success = test_library_api()
    sys.exit(0 if success else 1)
