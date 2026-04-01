# Clint Library API

This guide covers using Clint as a Python library in your own applications.

## Quick Start

```python
from clint import Engine

# Initialize
engine = Engine(api_key="sk_...")

# Personalize a message
result = engine.personalize({
    "name": "Jane Doe",
    "company": "TechCorp",
    "title": "CTO"
})

print(result["body"])
```

## Installation

```bash
pip install sagarithm-clint
```

## Core Concepts

Clint provides an `Engine` class that handles lead personalization and message generation using AI.

### Engine Class

The main interface for library usage.

```python
from clint import Engine

engine = Engine(api_key="your_openrouter_api_key")
```

**Parameters:**
- `api_key` (str, optional): OpenRouter API key. If not provided, uses `OPENROUTER_API_KEY` from environment.

## Methods

### `personalize(lead, channel="email", outreach_step=1, service=None)`

Generate a personalized message for a single lead (synchronous).

**Parameters:**
- `lead` (dict): Lead information with keys like `name`, `company`, `title`, `category`, etc.
- `channel` (str): `"email"` or `"whatsapp"` (default: `"email"`)
- `outreach_step` (int): `1` (pitch), `2` (followup), `3` (final) (default: `1`)
- `service` (str, optional): Service or product to pitch (e.g., "Website Redesign")

**Returns:**
- dict with keys:
  - `subject`: Email subject (only for email channel)
  - `body`: Message body
  - `channel`: The channel used
  - `lead_name`: The lead's name

**Example:**

```python
result = engine.personalize({
    "name": "Jane Doe",
    "company": "TechCorp",
    "title": "CTO",
    "category": "Technology",
    "rating": 4.5,
    "reviews_count": 120
}, channel="email")

print(result["subject"])  # Email subject
print(result["body"])     # Email body
```

### `personalize_async(lead, channel="email", outreach_step=1, service=None)`

Async version of `personalize()`. Use this for better performance when called from async code.

**Example:**

```python
import asyncio

async def send_personalized_email(lead):
    engine = Engine(api_key="sk_...")
    result = await engine.personalize_async(lead, channel="email")
    # Send email with result["body"]
    return result

asyncio.run(send_personalized_email(lead))
```

### `personalize_batch(leads, channel="email", outreach_step=1, service=None)`

Generate personalized messages for multiple leads (synchronous batch).

**Parameters:**
- `leads` (list[dict]): List of lead dictionaries
- `channel` (str): `"email"` or `"whatsapp"` (default: `"email"`)
- `outreach_step` (int): Campaign step
- `service` (str, optional): Service to pitch

**Returns:**
- list[dict]: List of result dictionaries, one per lead

**Example:**

```python
leads = [
    {"name": "Jane Doe", "company": "TechCorp", "title": "CTO"},
    {"name": "John Smith", "company": "DataFlow", "title": "CEO"},
    {"name": "Alice Johnson", "company": "CloudSys", "title": "VP Eng"}
]

results = engine.personalize_batch(leads, channel="email")

for result in results:
    print(f"{result['lead_name']}: {result['body'][:100]}...")
```

### `personalize_batch_async(leads, channel="email", outreach_step=1, service=None)`

Async batch personalization with concurrent processing.

**Example:**

```python
import asyncio

async def batch_send():
    engine = Engine(api_key="sk_...")
    leads = [...]  # Your lead list
    
    results = await engine.personalize_batch_async(
        leads,
        channel="email",
        outreach_step=1,
        service="Website Redesign & AI Suite"
    )
    
    for result in results:
        print(f"Generated for {result['lead_name']}")
    
    return results

asyncio.run(batch_send())
```

## Lead Dictionary Format

A lead can contain these optional fields:

```python
{
    "name": str,                 # Lead's full name
    "company": str,              # Company name
    "title": str,                # Job title
    "category": str,             # Business category/industry
    "business_category": str,    # Alternative to 'category'
    "audit_summary": str,        # Custom audit findings (if available)
    "score": int,                # Lead quality score (0-10)
    "has_website": bool,         # Whether lead has a website
    "rating": float,             # Business rating (0-5)
    "reviews_count": int,        # Number of reviews
    "about_us_info": str         # Company background info
}
```

**Minimal example:**
```python
engine.personalize({"name": "Jane Doe"})
```

**Rich example:**
```python
engine.personalize({
    "name": "Jane Doe",
    "company": "TechCorp",
    "title": "CTO",
    "category": "Technology",
    "rating": 4.5,
    "reviews_count": 120,
    "score": 8,
    "has_website": True,
    "about_us_info": "Leading cloud infrastructure provider founded in 2015..."
})
```

## Outreach Steps

Control message tone and content:

- **Step 1 (Pitch)**: Initial cold outreach introducing your service.
- **Step 2 (Followup)**: Soft follow-up checking if they received or read your message.
- **Step 3 (Final)**: Last attempt offering value or quick conversation.

```python
# Initial pitch
result1 = engine.personalize(lead, outreach_step=1)

# 3-7 days later, followup
result2 = engine.personalize(lead, outreach_step=2)

# Final attempt
result3 = engine.personalize(lead, outreach_step=3)
```

## Channels

### Email

```python
result = engine.personalize(lead, channel="email")
# result["subject"]  - Email subject line
# result["body"]     - Email body
```

### WhatsApp

```python
result = engine.personalize(lead, channel="whatsapp")
# result["body"]     - WhatsApp message (short, ~50 words)
# result["subject"]  - None (not applicable for WhatsApp)
```

## Advanced: Custom Configuration

Override default settings:

```python
from clint import Engine
from core.config import settings

# Customize before or after Engine init
settings.SENDER_NAME = "Sagar Kewat"
settings.SENDER_TITLE = "Founder | Pixartual"
settings.FROM_EMAIL = "hello@pixartual.studio"

engine = Engine(api_key="sk_...")
result = engine.personalize(lead)
```

## Error Handling

```python
from clint import Engine

try:
    engine = Engine(api_key="invalid_key")
    result = engine.personalize({"name": "Jane"})
except Exception as e:
    print(f"Error: {e}")
```

## Performance Tips

1. **Use async for batches**: Async methods process multiple leads concurrently.
   ```python
   # Fast (concurrent)
   results = await engine.personalize_batch_async(large_list)
   
   # Slower (sequential)
   results = engine.personalize_batch(large_list)
   ```

2. **Set API key once**: Initialize Engine once, reuse it.
   ```python
   engine = Engine(api_key="sk_...")
   # Use engine multiple times
   ```

3. **Handle rate limits**: OpenRouter may throttle requests. Implement retry logic:
   ```python
   import asyncio
   
   async def retry_personalize(lead, max_retries=3):
       for attempt in range(max_retries):
           try:
               return await engine.personalize_async(lead)
           except Exception as e:
               if attempt == max_retries - 1:
                   raise
               await asyncio.sleep(2 ** attempt)  # Exponential backoff
   ```

## Integration Examples

### Django Integration

```python
# views.py
from django.http import JsonResponse
from clint import Engine

engine = Engine(api_key="sk_...")

def generate_email(request):
    lead_data = request.POST.dict()
    result = engine.personalize(lead_data, channel="email")
    return JsonResponse(result)
```

### FastAPI Integration

```python
# main.py
from fastapi import FastAPI
from clint import Engine

app = FastAPI()
engine = Engine(api_key="sk_...")

@app.post("/personalize")
async def personalize_endpoint(lead: dict):
    return await engine.personalize_async(lead, channel="email")
```

### Webhook for CRM

```python
# Trigger personalization when new lead enters CRM
import requests
from clint import Engine

engine = Engine(api_key="sk_...")

def on_new_lead(crm_lead):
    result = engine.personalize({
        "name": crm_lead["contact_name"],
        "company": crm_lead["company_name"],
        "title": crm_lead["job_title"],
        "category": crm_lead["industry"]
    })
    
    # Send personalized email via webhook
    requests.post(
        "https://your-email-service/send",
        json={"to": crm_lead["email"], "body": result["body"]}
    )
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/sagarithm/clint/issues
- Documentation: https://github.com/sagarithm/clint
