"""
Example 3: Integration with FastAPI

This example shows how to create a simple FastAPI endpoint that uses Clint
to generate personalized messages on-demand.

Prerequisites:
    - pip install sagarithm-clint fastapi uvicorn
    - Set OPENROUTER_API_KEY environment variable or pass it to Engine()

Usage:
    python examples/example_fastapi_integration.py
    
    # Then in another terminal:
    curl -X POST http://localhost:8000/personalize \
         -H "Content-Type: application/json" \
         -d '{
           "name": "Jane Doe",
           "company": "TechCorp",
           "title": "CTO",
           "category": "Technology"
         }'
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from clint import Engine
import uvicorn

# Initialize FastAPI
app = FastAPI(
    title="Clint Personalization API",
    description="Generate personalized outreach messages using Clint",
    version="1.0"
)

# Initialize Clint Engine
engine = Engine(api_key="sk_your_openrouter_key")

# Define request schema
class LeadRequest(BaseModel):
    name: str
    company: str = None
    title: str = None
    category: str = None
    rating: float = None
    reviews_count: int = None
    channel: str = "email"  # "email" or "whatsapp"
    outreach_step: int = 1  # 1, 2, or 3


class PersonalizationResponse(BaseModel):
    status: str
    lead_name: str
    subject: str = None  # None for WhatsApp
    body: str
    channel: str


@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "service": "Clint Personalization API",
        "version": "1.0",
        "status": "ready"
    }


@app.post("/personalize", response_model=PersonalizationResponse)
async def personalize_lead(lead: LeadRequest):
    """
    Generate a personalized message for a lead.
    
    Args:
        lead: Lead information including name, company, title, etc.
    
    Returns:
        PersonalizationResponse with generated message
    """
    try:
        # Convert Pydantic model to dict
        lead_dict = lead.dict(exclude_none=True)
        
        # Remove API-specific fields
        channel = lead_dict.pop("channel", "email")
        outreach_step = lead_dict.pop("outreach_step", 1)
        
        # Generate personalized message using Clint
        result = engine.personalize(
            lead_dict,
            channel=channel,
            outreach_step=outreach_step
        )
        
        return PersonalizationResponse(
            status="success",
            lead_name=result["lead_name"],
            subject=result.get("subject"),
            body=result["body"],
            channel=result["channel"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Personalization failed: {str(e)}")


@app.post("/personalize-batch")
async def personalize_batch(leads: list[LeadRequest]):
    """
    Generate personalized messages for multiple leads concurrently.
    
    Args:
        leads: List of lead information
    
    Returns:
        List of PersonalizationResponse objects
    """
    try:
        # Convert all leads to dicts
        lead_dicts = []
        for lead in leads:
            lead_dict = lead.dict(exclude_none=True)
            lead_dict.pop("channel", "email")
            lead_dict.pop("outreach_step", 1)
            lead_dicts.append(lead_dict)
        
        # Generate messages using async batch for better performance
        results = await engine.personalize_batch_async(
            lead_dicts,
            channel="email",
            outreach_step=1
        )
        
        return {
            "status": "success",
            "count": len(results),
            "messages": [
                PersonalizationResponse(
                    status="success",
                    lead_name=r["lead_name"],
                    subject=r.get("subject"),
                    body=r["body"],
                    channel=r["channel"]
                )
                for r in results
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch personalization failed: {str(e)}")


# Example usage
if __name__ == "__main__":
    print("Starting Clint Personalization API...")
    print("Visit http://localhost:8000/docs for interactive API documentation")
    print("\nExample requests:")
    print("""
    # Single lead
    curl -X POST http://localhost:8000/personalize \\
         -H "Content-Type: application/json" \\
         -d '{"name": "Jane Doe", "company": "TechCorp", "title": "CTO"}'
    
    # Multiple leads
    curl -X POST http://localhost:8000/personalize-batch \\
         -H "Content-Type: application/json" \\
         -d '[
           {"name": "Jane Doe", "company": "TechCorp"},
           {"name": "John Smith", "company": "DataFlow"}
         ]'
    """)
    
    # Run server
    uvicorn.run(app, host="127.0.0.1", port=8000)
