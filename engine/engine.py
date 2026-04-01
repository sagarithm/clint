"""
Clint Library API: Programmatic interface for lead personalization and outreach.

Usage:
    import clint
    
    engine = clint.Engine(api_key="your_openrouter_key")
    result = engine.personalize({
        "name": "Jane Doe",
        "company": "TechCorp",
        "title": "CTO"
    })
    print(result["generated_hook"])
"""

import asyncio
from typing import Dict, Any, Optional

from engine.proposer import Proposer
from core.config import settings
from core.logger import logger


class Engine:
    """
    High-level library interface for Clint personalization and outreach.
    
    Provides both sync and async methods for generating personalized email/WhatsApp messages.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Clint Engine.
        
        Args:
            api_key: OpenRouter API key. If not provided, uses OPENROUTER_API_KEY from env.
        
        Example:
            engine = Engine(api_key="sk_...")
        """
        if api_key:
            settings.OPENROUTER_API_KEY = api_key
        self.proposer = Proposer()
        logger.info("Clint Engine initialized.")

    def personalize(
        self,
        lead: Dict[str, Any],
        channel: str = "email",
        outreach_step: int = 1,
        service: str = None
    ) -> Dict[str, str]:
        """
        Generate a personalized message for a lead (synchronous wrapper).
        
        Args:
            lead: Dictionary containing lead information (name, company, title, etc.)
            channel: "email" or "whatsapp"
            outreach_step: 1 (pitch), 2 (followup), 3 (final)
            service: Optional service to pitch (e.g., "Website Redesign & AI Enrollment Suite")
        
        Returns:
            Dictionary with keys: "subject" (email only), "body", "channel"
        
        Example:
            result = engine.personalize({
                "name": "Jane Doe",
                "company": "TechCorp",
                "title": "CTO"
            })
            print(result["body"])
        """
        return asyncio.run(self.personalize_async(lead, channel, outreach_step, service))

    async def personalize_async(
        self,
        lead: Dict[str, Any],
        channel: str = "email",
        outreach_step: int = 1,
        service: str = None
    ) -> Dict[str, str]:
        """
        Generate a personalized message for a lead (async).
        
        Args:
            lead: Dictionary containing lead information
            channel: "email" or "whatsapp"
            outreach_step: 1 (pitch), 2 (followup), 3 (final)
            service: Optional service to pitch
        
        Returns:
            Dictionary with keys: "subject" (email only), "body", "channel"
        """
        lead_name = lead.get("name", "there")
        business_category = lead.get("category") or lead.get("business_category")
        audit_summary = lead.get("audit_summary") or f"Professional in {business_category or 'their industry'}"
        
        subject, body = await self.proposer.generate_proposal(
            lead_name=lead_name,
            audit_summary=audit_summary,
            channel=channel,
            business_category=business_category,
            service=service,
            outreach_step=outreach_step,
            score=lead.get("score", 0),
            has_website=lead.get("has_website", True),
            rating=lead.get("rating", 0.0),
            reviews_count=lead.get("reviews_count", 0),
            about_us_info=lead.get("about_us_info")
        )
        
        return {
            "subject": subject if channel == "email" else None,
            "body": body,
            "channel": channel,
            "lead_name": lead_name
        }

    def personalize_batch(
        self,
        leads: list[Dict[str, Any]],
        channel: str = "email",
        outreach_step: int = 1,
        service: str = None
    ) -> list[Dict[str, str]]:
        """
        Generate personalized messages for multiple leads (synchronous batch).
        
        Args:
            leads: List of lead dictionaries
            channel: "email" or "whatsapp"
            outreach_step: 1 (pitch), 2 (followup), 3 (final)
            service: Optional service to pitch
        
        Returns:
            List of result dictionaries, one per lead
        
        Example:
            results = engine.personalize_batch([
                {"name": "Jane", "company": "TechCorp"},
                {"name": "John", "company": "DataFlow"}
            ])
        """
        return asyncio.run(self.personalize_batch_async(leads, channel, outreach_step, service))

    async def personalize_batch_async(
        self,
        leads: list[Dict[str, Any]],
        channel: str = "email",
        outreach_step: int = 1,
        service: str = None
    ) -> list[Dict[str, str]]:
        """
        Generate personalized messages for multiple leads (async batch).
        
        Processes all leads concurrently for better performance.
        """
        tasks = [
            self.personalize_async(lead, channel, outreach_step, service)
            for lead in leads
        ]
        return await asyncio.gather(*tasks)


__all__ = ["Engine"]
