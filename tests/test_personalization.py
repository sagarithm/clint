import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.proposer import Proposer
from core.database import init_db

async def test_generation():
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

if __name__ == "__main__":
    asyncio.run(test_generation())
