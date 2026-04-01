"""
Example 1: Basic Single-Lead Personalization

This example shows the simplest way to use Clint to generate a personalized message
for a single lead.

Prerequisites:
    - pip install sagarithm-clint
    - Set OPENROUTER_API_KEY environment variable or pass it to Engine()

Usage:
    python examples/example_single_lead.py
"""

from clint import Engine

# Initialize the Engine with your API key
# If you have OPENROUTER_API_KEY in .env or environment, Engine() will auto-load it
engine = Engine(api_key="sk_your_openrouter_key")

# Define a lead
lead = {
    "name": "Jane Doe",
    "company": "TechCorp",
    "title": "Chief Technology Officer",
    "category": "Technology",
    "rating": 4.5,
    "reviews_count": 120
}

print("=" * 60)
print("CLINT PERSONALIZATION EXAMPLE")
print("=" * 60)

# Step 1: Generate an email pitch
print("\n[STEP 1] INITIAL EMAIL PITCH")
print("-" * 60)
result = engine.personalize(
    lead,
    channel="email",
    outreach_step=1,
    service="Website Redesign & AI Integration"
)
print(f"To: {lead['name']} ({lead['company']})")
print(f"Subject: {result['subject']}")
print(f"Body:\n{result['body']}")

# Step 2: Generate a follow-up email (for 3-7 days later)
print("\n[STEP 2] FOLLOW-UP EMAIL (3-7 days later)")
print("-" * 60)
result = engine.personalize(
    lead,
    channel="email",
    outreach_step=2
)
print(f"Subject: {result['subject']}")
print(f"Body:\n{result['body']}")

# Step 3: Generate a final touch email
print("\n[STEP 3] FINAL EMAIL (1 week later)")
print("-" * 60)
result = engine.personalize(
    lead,
    channel="email",
    outreach_step=3
)
print(f"Subject: {result['subject']}")
print(f"Body:\n{result['body']}")

print("\n" + "=" * 60)
print("✓ Personalization complete!")
print("=" * 60)
