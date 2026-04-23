import asyncio
import httpx
from core.config import settings
from core.logger import logger
from core.prompt_compiler import PromptContext, compile_outreach_prompt
from typing import Dict, List

class Proposer:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.about_us = """
        Pixartual Studio creates intelligent, future-focused digital experiences where imagination meets engineering, 
        blending AI, design, strategy, and innovation to build platforms, brands, and products that perform beautifully, 
        evolve with purpose, and shape the digital tomorrow. 
        "Where Brands Evolve Into Power." 
        We craft intelligent identities, build futuristic platforms, and design emotionally engaging digital experiences 
        that convert curiosity into trust and attention into lasting success.
        """
        self.services = """
        SERVICES OFFERED:
        01 Branding: Visual identity, Logo, Guidelines, Intelligent Identities.
        02 Interactive Design: UI/UX, User Research, Prototyping, Emotionally engaging experiences.
        03 Product Design: SaaS Design, MVP Development, Futuristic Platforms.
        04 Development: Web/Mobile Apps, Custom API Integration, Engineering-led Innovation.
        05 SEO & Marketing: Growth Marketing, Analytics, Strategy.
        06 AI & Innovation: Intelligence Automation, Machine Learning, Blending AI with Design.
        """

    async def generate_proposal(self, lead_name: str, audit_summary: str, channel: str = "email", 
                                rating: float = 0.0, reviews_count: int = 0, business_category: str = None,
                                has_website: bool = True, about_us_info: str = None,
                                outreach_step: int = 1, score: float = 0.0, service: str = None) -> tuple:
        if not self.api_key:
            return ("Outreach", f"Draft: Hi {lead_name}, Following up on my previous message regarding your {'website' if has_website else 'digital presence'}...")

        # Service Inference
        if not service:
            service = "Website Redesign" if has_website else "Website Development"

        prompt = compile_outreach_prompt(
            PromptContext(
                lead_name=lead_name,
                channel=channel,
                outreach_step=outreach_step,
                service=service,
                business_category=business_category,
                has_website=has_website,
                rating=rating,
                reviews_count=reviews_count,
                about_us_info=about_us_info,
                audit_summary=audit_summary,
                score=score,
            )
        )

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
                            {"role": "system", "content": "You are the Founder of Pixartual Studio. You write short, high-conversion, authoritative emails."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.6
                    }
                )
                
                if response.status_code == 200:
                    content = response.json()['choices'][0]['message']['content'].strip()
                    
                    # Parsing Logic
                    subject = f"Regarding {lead_name}"
                    body = content
                    
                    if "Subject:" in content:
                        parts = content.split("Body:", 1)
                        if len(parts) > 1:
                            subject = parts[0].replace("Subject:", "").strip()
                            body = parts[1].strip()
                        else:
                            # fallback if Body: is missing
                            lines = content.split("\n", 1)
                            subject = lines[0].replace("Subject:", "").strip()
                            body = lines[1].strip() if len(lines) > 1 else content

                    if "Dear" not in body[:20]:
                        salutation = f"Dear {lead_name},\n\n"
                        body = salutation + body
                    
                    if channel == "email" and "Warm regards," not in body:
                        signature = f"\n\nWarm regards,\n\n{settings.SENDER_NAME}\nFounder | Pixartual\n🌐 https://www.pixartual.studio\n✨ Where Brands Evolve Into Power."
                        body += signature
                    elif channel == "whatsapp":
                        # Ensure no signature in WA even if LLM added it
                        if "Warm regards," in body:
                            body = body.split("Warm regards,")[0].strip()

                    logger.info(f"Proposal Generated: [bold green]{lead_name}[/bold green]")
                    return subject, body
                else:
                    logger.error(f"Proposer API Error ({response.status_code}): {response.text}")
                    return self._fallback_template(lead_name, has_website, channel)

        except Exception as e:
            logger.error(f"Proposer Exception for {lead_name}: {e}")
            return self._fallback_template(lead_name, has_website, channel)

    def _fallback_template(self, lead_name: str, has_website: bool, channel: str) -> tuple:
        if not settings.FALLBACK_TEMPLATE_ENABLED:
            return "Important Note", "Generation failed."
            
        logger.warning(f"Using deterministic fallback template for {lead_name}")
        subject = f"Connecting regarding your {'website' if has_website else 'digital presence'}"
        body = f"Dear {lead_name},\n\nI was reviewing your business and noticed opportunities to enhance your digital presence and conversion rate. Would you be open to a brief chat to discuss how we can help you capture more leads?\n"
        
        if channel == "email":
            body += f"\nWarm regards,\n\n{settings.SENDER_NAME}\n{settings.SENDER_TITLE}\n🌐 {settings.SENDER_SITE}\n✨ {settings.SENDER_TAGLINE}"
            
        return subject, body

if __name__ == "__main__":
    proposer = Proposer()
    # Test call
    # res = asyncio.run(proposer.generate_proposal("Dental Clinic", "Their website is not mobile responsive."))
    # print(res)
