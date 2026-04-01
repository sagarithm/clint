"""
Example 2: Batch Personalization for Multiple Leads

This example shows how to process multiple leads in a batch, generating personalized
messages for each one.

Prerequisites:
    - pip install sagarithm-clint
    - Set OPENROUTER_API_KEY environment variable or pass it to Engine()

Usage:
    python examples/example_batch_leads.py
"""

import asyncio
from clint import Engine

# Sample leads (imagine these come from your CRM, CSV, or database)
SAMPLE_LEADS = [
    {
        "name": "Jane Doe",
        "company": "TechCorp",
        "title": "CTO",
        "category": "Technology",
        "rating": 4.5,
        "reviews_count": 120
    },
    {
        "name": "John Smith",
        "company": "DataFlow Analytics",
        "title": "VP Engineering",
        "category": "SaaS",
        "rating": 4.7,
        "reviews_count": 89
    },
    {
        "name": "Alice Johnson",
        "company": "CloudSys Inc",
        "title": "CEO",
        "category": "Cloud Infrastructure",
        "rating": 4.3,
        "reviews_count": 156
    }
]

def example_sync_batch():
    """Simple synchronous batch processing (easier but slower)"""
    print("=" * 70)
    print("BATCH EXAMPLE (SYNCHRONOUS)")
    print("=" * 70)
    
    engine = Engine(api_key="sk_your_openrouter_key")
    
    # Generate messages for all leads
    results = engine.personalize_batch(
        SAMPLE_LEADS,
        channel="email",
        outreach_step=1,
        service="Website Redesign & AI Suite"
    )
    
    # Display results
    for i, result in enumerate(results, 1):
        print(f"\n[LEAD {i}] {result['lead_name']}")
        print("-" * 70)
        print(f"Subject: {result['subject']}")
        print(f"Body: {result['body'][:150]}...")  # Show first 150 chars
    
    print("\n" + "=" * 70)
    print(f"✓ Generated {len(results)} personalized emails")
    print("=" * 70)


async def example_async_batch():
    """High-performance asynchronous batch (faster for large batches)"""
    print("\n" * 2)
    print("=" * 70)
    print("BATCH EXAMPLE (ASYNCHRONOUS - CONCURRENT PROCESSING)")
    print("=" * 70)
    
    engine = Engine(api_key="sk_your_openrouter_key")
    
    # Generate messages for all leads concurrently
    # This is much faster than sync when dealing with API latency
    results = await engine.personalize_batch_async(
        SAMPLE_LEADS,
        channel="email",
        outreach_step=1,
        service="Website Redesign & AI Suite"
    )
    
    # Display results
    for i, result in enumerate(results, 1):
        print(f"\n[LEAD {i}] {result['lead_name']}")
        print("-" * 70)
        print(f"Subject: {result['subject']}")
        print(f"Body: {result['body'][:150]}...")  # Show first 150 chars
    
    print("\n" + "=" * 70)
    print(f"✓ Generated {len(results)} personalized emails (async)")
    print("=" * 70)


def example_mixed_channels():
    """Send different messages via different channels"""
    print("\n" * 2)
    print("=" * 70)
    print("MIXED CHANNELS EXAMPLE (EMAIL + WHATSAPP)")
    print("=" * 70)
    
    engine = Engine(api_key="sk_your_openrouter_key")
    
    lead = SAMPLE_LEADS[0]
    
    # Generate email version (longer, formal)
    email_result = engine.personalize(lead, channel="email", outreach_step=1)
    print(f"\n[EMAIL TO {lead['name']}]")
    print("-" * 70)
    print(f"Subject: {email_result['subject']}")
    print(f"Body:\n{email_result['body']}")
    
    # Generate WhatsApp version (shorter, friendly)
    whatsapp_result = engine.personalize(lead, channel="whatsapp", outreach_step=1)
    print(f"\n[WHATSAPP TO {lead['name']}]")
    print("-" * 70)
    print(f"Message:\n{whatsapp_result['body']}")
    
    print("\n" + "=" * 70)
    print("✓ Generated multi-channel messages")
    print("=" * 70)


if __name__ == "__main__":
    # Run synchronous example
    example_sync_batch()
    
    # Run mixed channels example
    example_mixed_channels()
    
    # Run asynchronous example (faster for large batches)
    print("\n\nRunning async batch (best for performance with many leads)...")
    asyncio.run(example_async_batch())
