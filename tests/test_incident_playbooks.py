import pytest
import asyncio
from core.database import init_db, get_db
from core.quality_gate import evaluate_message_quality
from engine.engine import Engine, EngineProviderError

@pytest.mark.asyncio
async def test_fallback_template_incident_recovery():
    """
    Test Playbook: Engine Provider Outage (OpenRouter Unreachable)
    Expected Action: Engine seamlessly uses deterministic fallback template
    so operations do not lock up.
    """
    engine = Engine(api_key="invalid_test_key_simulating_outage")
    
    # We monkeypatch the proposer api_key to simulate zero config outage
    engine.proposer.api_key = ""
    
    lead_sim = {
        "name": "Jane Incident",
        "company": "Outage Corp",
        "title": "CEO",
        "has_website": True,
        "category": "Technology",
    }
    
    # Run the generator
    result = await engine.personalize_async(lead_sim)
    
    # Validate playbook successfully recovered using the fallback
    assert result.body is not None
    assert "Important Note" not in result.subject
    assert "Jane Incident" in result.body
    assert "generation failed" not in result.body.lower()
    assert result.reason_code == "generated"

def test_quality_gate_incident_blocker():
    """
    Test Playbook: Rogue LLM hallucinating placeholder tokens.
    Expected Action: Quality Gate aggressively blocks the dispatch.
    """
    rogue_body = "Hello Jane, we can provide you with [SERVICE] to improve your [GOAL]."
    
    evaluation = evaluate_message_quality(
        lead_name="Jane",
        subject="Your Business",
        body=rogue_body,
        channel="email"
    )
    
    assert evaluation["passed"] is False
    assert "placeholder_tokens_found" in evaluation["reasons"]
    assert evaluation["quality_score"] < 60
