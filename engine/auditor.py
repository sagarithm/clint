import asyncio
import httpx
from typing import Dict, Optional
from core.config import settings
from core.logger import logger

class AIAuditor:
    """
    An AI-driven website auditor that identifies business pain points.
    
    Uses LLMs (via OpenRouter) to analyze business context and generate 
    targeted hooks for outreach personalization.
    """

    def __init__(self) -> None:
        self.api_key: str = settings.OPENROUTER_API_KEY
        self.url: str = "https://openrouter.ai/api/v1/chat/completions"

    async def audit_website(self, lead_name: str, site_data: Dict[str, any]) -> str:
        """
        Analyzes website metadata to identify 3 core areas for improvement.
        
        Args:
            lead_name: The name of the business.
            site_data: Dictionary containing 'about_us_info' or 'text_content'.
            
        Returns:
            A concise 3-sentence summary of the main 'pain point' discovered.
        """
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY is missing. Skipping AI Audit.")
            return "Audit skipped: Missing credentials."

        context = site_data.get("about_us_info") or site_data.get("text_content", "No content found.")
        
        prompt = f"""
        [ROLE] Senior Business Auditor at Pixartual Studio.
        [ACTION] Analyze the provided business context and identify 3 CRITICAL "Leakage Points" where this business is losing money or authority.
        
        [TARGET] {lead_name}
        [DATA] {context[:3000]}

        [AREAS OF FOCUS]
        1. TRUST LEAK: Is their website/brand outdated or unprofessional?
        2. CONVERSION LEAK: Is it hard for a customer to book or buy?
        3. INNOVATION GAP: How would AI or Automation save them 20+ hours a week?

        [RESPONSE] 
        - Provide exactly 3 short, punchy bullet points of 'Technical Weaknesses'.
        - End with a 1-sentence 'Founder's Observation' that is direct but respectful.
        - NO fluff. NO polite introductions. Just the raw intelligence.
        """

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    self.url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": settings.SENDER_SITE,
                        "X-Title": "ColdMailer Pro",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": settings.AI_MODEL,
                        "messages": [
                            {"role": "system", "content": "You are a senior business auditor at Pixartual Studio."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.4
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    audit_text = result['choices'][0]['message']['content'].strip()
                    logger.info(f"AI Audit Complete: [bold green]{lead_name}[/bold green]")
                    return audit_text
                else:
                    logger.error(f"AI Audit API Error ({response.status_code}): {response.text}")
                    return "Audit unavailable: API error."

        except Exception as e:
            logger.error(f"AI Audit Exception for {lead_name}: {e}")
            return "Audit unavailable: System exception."

if __name__ == "__main__":
    auditor = AIAuditor()
    # test = asyncio.run(auditor.audit_website("Example Clinic", {"about_us_info": "We have a slow site."}))
    # print(test)
