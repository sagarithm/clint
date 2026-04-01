# How to Use Clint as a Library

Users can import and use Clint as a Python library in their own projects.

## Installation

### Option 1: Install from PyPI (Production)

```bash
pip install sagarithm-clint
```

Then import:

```python
from clint import Engine

engine = Engine(api_key="your_openrouter_key")
result = engine.personalize({"name": "Jane Doe", "company": "TechCorp"})
print(result["body"])
```

### Option 2: Install Locally (Development)

```bash
cd agent
pip install -e .  # Editable install for development
```

Then use the same import:

```python
from clint import Engine
```

### Option 3: Use Without Installation (Direct)

```python
import sys
sys.path.insert(0, "path/to/agent")

from clint import Engine
engine = Engine(api_key="your_key")
```

---

## Quick Start

### 1. Single Lead Personalization

```python
from clint import Engine

# Initialize engine
engine = Engine(api_key="sk_your_openrouter_key")

# Create a lead
lead = {
    "name": "Jane Doe",
    "company": "TechCorp",
    "title": "CTO"
}

# Generate personalized message
result = engine.personalize(lead)

print("Generated Message:")
print(result["body"])
# Output: Hi Jane, I noticed TechCorp has ...
```

### 2. Multi-Lead Batch Processing

```python
from clint import Engine

engine = Engine(api_key="sk_your_openrouter_key")

leads = [
    {"name": "Jane Doe", "company": "TechCorp", "title": "CTO"},
    {"name": "John Smith", "company": "DataFlow", "title": "CEO"},
    {"name": "Alice Johnson", "company": "CloudSys", "title": "VP Eng"}
]

# Generate for all leads
results = engine.personalize_batch(leads, channel="email")

for result in results:
    print(f"{result['lead_name']}: {result['body'][:100]}...")
```

### 3. Async High-Performance Batch

```python
import asyncio
from clint import Engine

async def personalize_all_leads():
    engine = Engine(api_key="sk_your_openrouter_key")
    
    leads = [
        {"name": f"Lead {i}", "company": f"Company {i}"}
        for i in range(1, 11)
    ]
    
    # Processes all concurrently (faster)
    results = await engine.personalize_batch_async(leads)
    
    for result in results:
        print(f"✓ {result['lead_name']}")
    
    return results

# Run async
asyncio.run(personalize_all_leads())
```

### 4. WhatsApp Messages

```python
from clint import Engine

engine = Engine(api_key="sk_your_openrouter_key")

lead = {"name": "Jane Doe", "company": "TechCorp"}

# Generate WhatsApp-friendly message (short, ~50 words)
result = engine.personalize(lead, channel="whatsapp")

print("WhatsApp message:")
print(result["body"])
# Output: Hi Jane! Quick question - is TechCorp looking at web redesigns?
```

### 5. Multi-Step Outreach Sequences

```python
from clint import Engine

engine = Engine(api_key="sk_your_openrouter_key")
lead = {"name": "Jane Doe", "company": "TechCorp"}

# Step 1: Initial pitch
msg1 = engine.personalize(lead, outreach_step=1)
print("STEP 1 (Pitch):", msg1["body"])

# Step 2: Soft follow-up (send 3-7 days later)
msg2 = engine.personalize(lead, outreach_step=2)
print("STEP 2 (Follow-up):", msg2["body"])

# Step 3: Final attempt (send 1 week later)
msg3 = engine.personalize(lead, outreach_step=3)
print("STEP 3 (Final):", msg3["body"])
```

---

## Full API Reference

### Engine Class

```python
from clint import Engine

engine = Engine(api_key="your_openrouter_api_key")
```

**Available Methods:**

- `personalize(lead, channel="email", outreach_step=1, service=None)` - Sync single lead
- `personalize_async(lead, ...)` - Async single lead
- `personalize_batch(leads, ...)` - Sync batch
- `personalize_batch_async(leads, ...)` - Async batch (concurrent)

### Result Format

All methods return a dictionary:

```python
{
    "subject": "Your Email Subject",  # email only
    "body": "Generated message body",
    "channel": "email",
    "lead_name": "Jane Doe"
}
```

### Lead Format

Minimal:
```python
{"name": "Jane Doe"}
```

Rich:
```python
{
    "name": "Jane Doe",
    "company": "TechCorp",
    "title": "CTO",
    "category": "Technology",
    "rating": 4.5,
    "reviews_count": 120,
    "score": 8,
    "has_website": True,
    "about_us_info": "Leading cloud provider founded in 2015..."
}
```

---

## Integration Examples

### Django Email View

```python
# views.py
from django.http import JsonResponse
from clint import Engine

engine = Engine(api_key="sk_your_key")

def generate_email(request):
    lead = {
        "name": request.POST.get("name"),
        "company": request.POST.get("company"),
        "title": request.POST.get("title")
    }
    
    result = engine.personalize(lead, channel="email")
    
    return JsonResponse({
        "subject": result["subject"],
        "body": result["body"]
    })
```

### FastAPI Endpoint

```python
# main.py
from fastapi import FastAPI
from clint import Engine

app = FastAPI()
engine = Engine(api_key="sk_your_key")

@app.post("/personalize")
async def personalize_endpoint(lead: dict):
    result = await engine.personalize_async(lead, channel="email")
    return result

# Test with:
# curl -X POST http://localhost:8000/personalize \
#      -H "Content-Type: application/json" \
#      -d '{"name": "Jane Doe", "company": "TechCorp"}'
```

### Webhook Handler (CRM Integration)

```python
import requests
from clint import Engine

engine = Engine(api_key="sk_your_key")

def on_new_lead_created(webhook_payload):
    """Called when a new lead is created in your CRM"""
    
    lead = {
        "name": webhook_payload["contact_name"],
        "company": webhook_payload["company"],
        "title": webhook_payload["job_title"]
    }
    
    # Generate personalized email
    result = engine.personalize(lead, channel="email")
    
    # Send via your email service
    requests.post(
        "https://your-email-api.com/send",
        json={
            "to": webhook_payload["email"],
            "subject": result["subject"],
            "body": result["body"]
        }
    )
```

---

## Configuration & Advanced

### Custom Sender Information

```python
from clint import Engine
from core.config import settings

# Set before initializing
settings.SENDER_NAME = "Your Name"
settings.SENDER_TITLE = "Your Title"
settings.FROM_EMAIL = "your@email.com"

engine = Engine(api_key="sk_your_key")
```

### Error Handling

```python
from clint import Engine

try:
    engine = Engine(api_key="invalid_key")
    result = engine.personalize({"name": "Jane"})
except Exception as e:
    print(f"Error: {e}")
    # Handle fallback or retry
```

### Rate Limiting & Retry

```python
import asyncio
from clint import Engine

async def retry_with_backoff(lead, max_retries=3):
    engine = Engine(api_key="sk_your_key")
    
    for attempt in range(max_retries):
        try:
            return await engine.personalize_async(lead)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # Exponential backoff
            print(f"Retry in {wait_time}s...")
            await asyncio.sleep(wait_time)

# Usage
result = asyncio.run(retry_with_backoff(lead))
```

---

## Performance Tips

1. **Use async for batches** - Processes leads concurrently:
   ```python
   # Fast
   results = await engine.personalize_batch_async(large_list)
   
   # Slower
   results = engine.personalize_batch(large_list)
   ```

2. **Reuse engine instance**:
   ```python
   engine = Engine(api_key="sk_your_key")  # Create once
   
   # Reuse for multiple calls
   for lead in leads:
       result = engine.personalize(lead)
   ```

3. **Handle timeouts**:
   ```python
   import signal
   
   def timeout_handler(signum, frame):
       raise TimeoutError("Personalization took too long")
   
   signal.signal(signal.SIGALRM, timeout_handler)
   signal.alarm(30)  # 30 second timeout
   
   result = engine.personalize(lead)
   signal.alarm(0)  # Cancel alarm
   ```

---

## Troubleshooting

### Import Error

```
ModuleNotFoundError: No module named 'clint'
```

**Fix:**
```bash
pip install sagarithm-clint  # Install package
# OR
cd agent && pip install -e .  # Local development install
```

### API Key Error

```python
from clint import Engine

# Pass API key directly
engine = Engine(api_key="sk_your_openrouter_key")

# OR set environment variable
import os
os.environ["OPENROUTER_API_KEY"] = "sk_your_key"
engine = Engine()
```

### No Results

```python
# Ensure lead has a name at minimum
result = engine.personalize({"name": "Jane Doe"})

# Rich lead = better results
result = engine.personalize({
    "name": "Jane Doe",
    "company": "TechCorp",
    "title": "CTO",
    "category": "Technology"
})
```

---

## Support

- **GitHub**: https://github.com/sagarithm/clint
- **Issues**: https://github.com/sagarithm/clint/issues
- **PyPI**: https://pypi.org/project/sagarithm-clint/
