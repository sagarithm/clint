import asyncio
import httpx
from core.config import settings
from core.logger import logger
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

        channel_context = "Keep it concise (150 words max), professional, and conversational." if channel == "email" else "Keep it very short (50 words max), friendly, and direct for WhatsApp."
        
        deep_knowledge = ""
        if business_category: deep_knowledge += f"Industry: {business_category}\n"
        if rating > 0: deep_knowledge += f"Public Rating: {rating}/5 stars\n"
        if reviews_count > 0: deep_knowledge += f"Reviews: {reviews_count} reviews\n"
        if about_us_info: deep_knowledge += f"Company Background (Crawl): {about_us_info[:500]}\n"

        if outreach_step == 1:
            if has_website:
                goal = "Pitch a Website Redesign by highlighting issues found in the audit."
                specific_task = "- Refer specifically to the audit findings and suggest how a redesign will fix them."
            else:
                goal = "Pitch a New Website Development since the lead has no online presence."
                specific_task = "- Focus on the benefits of having a digital platform for trust and visibility."
        elif outreach_step == 2:
            goal = "Soft Follow-up: Check if they saw the previous email/audit. Keep it helpful, not pushy."
            specific_task = "- Mention you shared some thoughts a few days ago and wanted to ensure they reached the right person. Re-emphasize you are here to help."
        else:
            goal = "Final Re-engagement: Offer a quick value-add or a very short 5-min chat. Last attempt."
            specific_task = "- Keep it extremely brief. Ask if they are still the right person to talk to about digital strategy."

        # Multi-Condition Messaging Adaptation
        if score >= 8:
            if rating < 3.5:
                tone_strategy = "RESCUE: The business is struggling online. Be empathetic but firm about the risks of inaction."
            else:
                tone_strategy = "SCALE: The business is doing well but missing digital leverage. Be ambitious and focus on market dominance."
        else:
            tone_strategy = "STANDARD: Professional, curious, and value-focused."

        # Service Inference
        if not service:
            service = "Website Redesign" if has_website else "Website Development"

        prompt = f"""
        [ROLE] {settings.SENDER_NAME}, Founder at Pixartual.
        [GOAL] {goal}
        [SERVICE] {service}
        [STRATEGY] {tone_strategy}
        [DNA] {settings.SENDER_TAGLINE}
        [TASK] {specific_task}

        [CONTEXT]
        - Target Business: {lead_name}
        - Industry: {business_category or 'Local Business'}
        - Social Proof: {rating}/5 Stars ({reviews_count} Reviews)
        - Site Crawl: {about_us_info[:300] if about_us_info else 'No crawl data'}
        - Audit Findings: {audit_summary}

        [SYSTEM INSTRUCTIONS]
        1. SALUTATION: Start exactly with "Dear {lead_name}," (or "Dear {lead_name} Team," if it's a generic entity).
        2. SERVICE MENTION: Explicitly mention that you are reaching out regarding "[SERVICE]".
        3. PERSUASIVE HOOK: Immediately follow with a specific, direct observation about their {business_category or 'business'} or 'Audit Finding'.
        4. NO FLUFF: Avoid "I hope this email finds you well" or "My name is...".
        5. FOUNDER TONE: Be authoritative, slightly provocative, but professional. You are an expert peer.
        6. CHANNEL ADAPTATION: {'[EMAIL] Subject: [Hook] | Body: [Salutation] [3 Paras Max]' if channel == 'email' else '[WHATSAPP] [Salutation] [3 Sentences Max].'}

        [CONSTRAINTS]
        - NO PLACEHOLDERS.
        - NO MARKDOWN (Bold/Italic).
        - PLAIN TEXT ONLY.
        - SIGNATURE: Use exactly this signature at the end:
          Warm regards,

          {settings.SENDER_NAME}
          Founder | Pixartual
          🌐 https://www.pixartual.studio
          ✨ Where Brands Evolve Into Power.
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

                    if "Dear" not in body[:20] and channel == "email":
                        salutation = f"Dear {lead_name},\n\n"
                        body = salutation + body
                    
                    if "Warm regards," not in body:
                        signature = f"\n\nWarm regards,\n\n{settings.SENDER_NAME}\nFounder | Pixartual\n🌐 https://www.pixartual.studio\n✨ Where Brands Evolve Into Power."
                        body += signature

                    logger.info(f"Proposal Generated: [bold green]{lead_name}[/bold green]")
                    return subject, body
                else:
                    logger.error(f"Proposer API Error ({response.status_code}): {response.text}")
                    return "Important Note", "Generation failed."

        except Exception as e:
            logger.error(f"Proposer Exception for {lead_name}: {e}")
            return "Important Note", "Generation failed."

if __name__ == "__main__":
    proposer = Proposer()
    # Test call
    # res = asyncio.run(proposer.generate_proposal("Dental Clinic", "Their website is not mobile responsive."))
    # print(res)
