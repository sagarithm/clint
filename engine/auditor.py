import asyncio
import httpx
from core.config import settings
from core.logger import logger
from typing import Dict

class AIAuditor:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    async def audit_website(self, lead_name: str, crawl_data: Dict) -> str:
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not found. Skipping AI Audit.")
            return "Audit skipped: No API Key."

        audit_info = crawl_data.get("audit_info", {})
        text_content = audit_info.get("text_content", "No content found.")
        
        prompt = f"""
        Analyze this business website data and identify 3 specific areas for improvement in:
        1. Branding/Visual Identity
        2. UI/UX (User Experience)
        3. Innovation (AI/Automation potential)

        Lead Name: {lead_name}
        Website Title: {audit_info.get('title')}
        Text Content (Snippet): {text_content[:1500]}
        Is Responsive: {audit_info.get('is_responsive')}
        Modern Framework: {audit_info.get('has_modern_framework')}

        Provide a concise 3-sentence summary of the main 'pain point' we can use to pitch our services.
        Be professional but direct.
        """

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": settings.AI_MODEL,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    summary = data['choices'][0]['message']['content'].strip()
                    logger.info(f"AI Audit Complete for [bold green]{lead_name}[/bold green]: {summary[:100]}...")
                    return summary
                else:
                    logger.error(f"OpenRouter Error: {response.text}")
                    return "Audit failed: API Error."

        except Exception as e:
            logger.error(f"Audit Exception: {e}")
            return "Audit failed: Exception."

if __name__ == "__main__":
    auditor = AIAuditor()
    # Test
    res = asyncio.run(auditor.audit_website("Example Agency", {"audit_info": {"title": "Slow Site", "text_content": "We do stuff."}}))
    print(res)
