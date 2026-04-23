"""Clint library API for typed outreach personalization workflows."""

import asyncio
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional
from uuid import uuid4

from core.config import settings
from core.logger import logger
from engine.proposer import Proposer


class EngineError(Exception):
    """Base class for stable library domain errors."""


class EngineValidationError(EngineError):
    """Raised when user input fails deterministic validation rules."""


class EngineProviderError(EngineError):
    """Raised when upstream AI/provider generation fails."""


@dataclass
class PersonalizationResult:
    """Typed result contract for personalization operations."""

    subject: Optional[str]
    body: str
    channel: str
    lead_name: str
    correlation_id: str
    reason_code: str = "generated"

    # Backward-compatible dict-style access for existing callers.
    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


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
    ) -> PersonalizationResult:
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
    ) -> PersonalizationResult:
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
        if channel not in {"email", "whatsapp"}:
            raise EngineValidationError("channel must be 'email' or 'whatsapp'")
        if outreach_step not in {1, 2, 3}:
            raise EngineValidationError("outreach_step must be 1, 2, or 3")

        lead_name = str(lead.get("name") or "there")
        business_category = lead.get("category") or lead.get("business_category")
        audit_summary = lead.get("audit_summary") or f"Professional in {business_category or 'their industry'}"
        correlation_id = str(lead.get("correlation_id") or uuid4())
        
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

        if body == "Generation failed.":
            raise EngineProviderError("proposal_generation_failed")

        return PersonalizationResult(
            subject=subject if channel == "email" else None,
            body=body,
            channel=channel,
            lead_name=lead_name,
            correlation_id=correlation_id,
            reason_code="generated",
        )

    def personalize_batch(
        self,
        leads: list[Dict[str, Any]],
        channel: str = "email",
        outreach_step: int = 1,
        service: str = None,
        max_concurrency: int = 5,
    ) -> list[PersonalizationResult]:
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
        return asyncio.run(
            self.personalize_batch_async(
                leads,
                channel,
                outreach_step,
                service,
                max_concurrency=max_concurrency,
            )
        )

    async def personalize_batch_async(
        self,
        leads: list[Dict[str, Any]],
        channel: str = "email",
        outreach_step: int = 1,
        service: str = None,
        max_concurrency: int = 5,
    ) -> list[PersonalizationResult]:
        """
        Generate personalized messages for multiple leads (async batch).
        
        Processes all leads concurrently for better performance.
        """
        bounded = max(1, int(max_concurrency))
        semaphore = asyncio.Semaphore(bounded)

        async def _run_one(lead: Dict[str, Any]) -> PersonalizationResult:
            async with semaphore:
                return await self.personalize_async(lead, channel, outreach_step, service)

        tasks = [_run_one(lead) for lead in leads]
        return await asyncio.gather(*tasks)


__all__ = [
    "Engine",
    "EngineError",
    "EngineValidationError",
    "EngineProviderError",
    "PersonalizationResult",
]
