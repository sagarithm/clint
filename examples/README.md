# Examples

This folder contains production-ready examples of using Clint as a library.

## Quick Start

All examples require:
```bash
pip install sagarithm-clint
```

And set your API key:
```bash
export OPENROUTER_API_KEY=sk_your_key
```

Or pass it directly:
```python
engine = Engine(api_key="sk_your_key")
```

---

## Examples

### 1. Single Lead Personalization (Basic)

**File:** `example_single_lead.py`

Generate a full 3-step outreach sequence for one lead:
- Step 1: Initial email pitch
- Step 2: Soft follow-up email
- Step 3: Final touch email

```bash
python example_single_lead.py
```

**Use case:** Testing, debug, generating message for one contact.

---

### 2. Batch Processing Multiple Leads

**File:** `example_batch_leads.py`

Process multiple leads at once with three approaches:
- Synchronous batch (simple, slower)
- Asynchronous batch (concurrent, faster)
- Mixed channels (email + WhatsApp)

```bash
python example_batch_leads.py
```

**Use case:** Processing CRM exports, bulk outreach campaigns, performance testing.

---

### 3. FastAPI Web Service

**File:** `example_fastapi_integration.py`

Deploy Clint as a REST API service:
- `/personalize` - Generate message for one lead
- `/personalize-batch` - Generate for multiple leads
- `/docs` - Interactive API documentation

```bash
python example_fastapi_integration.py

# In another terminal:
curl -X POST http://localhost:8000/personalize \
     -H "Content-Type: application/json" \
     -d '{"name": "Jane Doe", "company": "TechCorp", "title": "CTO"}'
```

**Use case:** Web integration, CRM webhooks, mobile app backends.

---

## Integration Patterns

### Django View
```python
from clint import Engine

engine = Engine(api_key="sk_...")

def generate_email(request):
    lead = {
        "name": request.POST["name"],
        "company": request.POST["company"]
    }
    result = engine.personalize(lead, channel="email")
    return JsonResponse({"body": result["body"]})
```

### Async Task (Celery)
```python
from celery import shared_task
from clint import Engine

@shared_task
def personalize_leads_async(lead_ids):
    engine = Engine(api_key="sk_...")
    leads = Lead.objects.filter(id__in=lead_ids)
    results = engine.personalize_batch([
        {"name": l.name, "company": l.company}
        for l in leads
    ])
    return results
```

### Webhook Handler
```python
from clint import Engine

def on_new_crm_lead(webhook_data):
    engine = Engine(api_key="sk_...")
    
    result = engine.personalize({
        "name": webhook_data["contact_name"],
        "company": webhook_data["company_name"]
    })
    
    # Send via email service
    send_email(
        to=webhook_data["email"],
        subject=result["subject"],
        body=result["body"]
    )
```

---

## Tips

1. **Reuse the Engine instance** - Don't create a new one for each request:
   ```python
   engine = Engine(api_key="sk...")  # Create once
   for lead in leads:
       result = engine.personalize(lead)  # Reuse
   ```

2. **Use async for batches** - Process multiple leads concurrently:
   ```python
   results = await engine.personalize_batch_async(large_list)  # Fast
   ```

3. **Handle errors gracefully**:
   ```python
   try:
       result = engine.personalize(lead)
   except Exception as e:
       print(f"Error: {e}")
       # Use fallback message
   ```

---

## More Documentation

- **Full API Reference:** [../LIBRARY.md](../LIBRARY.md)
- **Launch Guide:** [../LAUNCH.md](../LAUNCH.md)
- **Main README:** [../README.md](../README.md)
