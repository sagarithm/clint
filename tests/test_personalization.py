import asyncio
import os
import sys

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Ensure local modules are imported even if similarly named packages were loaded earlier.
for module_name in ("core", "core.database", "engine", "engine.proposer"):
    sys.modules.pop(module_name, None)

from engine.proposer import Proposer
from core.config import settings
from core.database import init_db

async def _run_generation_test():
    os.makedirs(os.path.join(PROJECT_ROOT, "data"), exist_ok=True)
    settings.DB_PATH = os.path.join(PROJECT_ROOT, "data", "test_clint.db")
    await init_db()
    proposer = Proposer()
    
    lead_name = "Coimbatore Public School"
    audit_summary = "Website is slow, mobile-unresponsive, and lacks a modern enrollment form. Significant 'leakage' of parent inquiries."
    business_category = "Education / School"
    service = "Website Redesign & AI Enrollment Suite"
    
    # Test Email
    subject, body = await proposer.generate_proposal(
        lead_name, audit_summary, channel="email",
        business_category=business_category,
        service=service
    )
    
    print("--- EMAIL TEST ---")
    print(f"Subject: {subject}")
    print(f"Body:\n{body}")
    print("\n")
    
    # Test WhatsApp
    subject, body = await proposer.generate_proposal(
        lead_name, audit_summary, channel="whatsapp",
        business_category=business_category,
        service=service
    )
    
    print("--- WHATSAPP TEST ---")
    print(f"Body:\n{body}")


def test_generation():
    # Keep test runner compatibility without requiring pytest async plugins.
    asyncio.run(_run_generation_test())

if __name__ == "__main__":
    asyncio.run(_run_generation_test())
