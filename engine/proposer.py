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
                                is_reminder: bool = False) -> tuple:
        if not self.api_key:
            return ("Outreach", f"Draft: Hi {lead_name}, Following up on my previous message regarding your {'website' if has_website else 'digital presence'}...")

        channel_context = "Keep it concise (150 words max), professional, and conversational." if channel == "email" else "Keep it very short (50 words max), friendly, and direct for WhatsApp."
        
        deep_knowledge = ""
        if business_category: deep_knowledge += f"Industry: {business_category}\n"
        if rating > 0: deep_knowledge += f"Public Rating: {rating}/5 stars\n"
        if reviews_count > 0: deep_knowledge += f"Reviews: {reviews_count} reviews\n"
        if about_us_info: deep_knowledge += f"Company Background (Crawl): {about_us_info[:500]}\n"

        if is_reminder:
            goal = "Send a gentle follow-up/reminder. Refer to the previous audit/proposal and ask if they had time to review it. Keep it low-pressure but professional."
            specific_task = "- Mention that you're following up on the audit findings shared previously. Keep the tone helpful and curious."
        elif has_website:
            goal = "Pitch a Website Redesign by highlighting issues found in the audit."
            specific_task = "- Refer specifically to the audit findings and suggest how a redesign will fix them."
        else:
            goal = "Pitch a New Website Development since the lead has no online presence."
            specific_task = "- Focus on the benefits of having a digital platform for trust and visibility."

        prompt = f"""
        Role: {settings.SENDER_TITLE} at Pixartual Studio.
        Sender Name: {settings.SENDER_NAME}
        Sender Contact: {settings.SENDER_CONTACT}
        
        About Us: {self.about_us}
        User Services: {self.services}
        Lead: {lead_name}
        {deep_knowledge}
        Goal: {goal}
        Channel: {channel}
        
        Task: Write a highly personalized, warm, and human {'FOLLOW-UP' if is_reminder else 'Initial Outreach'} from Pixartual Studio. 
        {specific_task}
        - Use a warm, non-corporate tone. Avoid being 'salesy'.
        - If 'Company Background' is available, pick a specific detail to mention.
        - If the lead has good reviews, MENTION IT to build rapport.
        - Style: High-end, futuristic, yet remarkably human and curious.
        
        CRITICAL CONSTRAINTS:
        1. NO PLACEHOLDERS: Never use [Recipient's Name], [Your Name], or any brackets. If a person's name is unknown, use "Dear {lead_name} Team," or "To the {lead_name} leadership,".
        2. NO MARKDOWN: This is for a plain-text email. Do NOT use **bolding**, # headers, or list characters like *. Use standard capitalization or spacing for emphasis.
        3. SUBJECT LINE (Email Only): Generate a short, human subject line (e.g., "Quick question about {lead_name}" or "Thought for {lead_name}"). Do NOT use "Growth Opportunity".
        4. SIGNATURE: End with the exact signature below. 
        
        Ending: Use the following signature format (strictly no placeholders):
          Warm regards,
          
          {settings.SENDER_NAME}
          {settings.SENDER_TITLE}
          📞 {settings.SENDER_CONTACT}
          🌐 {settings.SENDER_SITE}
          ✨ {settings.SENDER_TAGLINE}
          
        - Ask for a 10-minute call.
        
        FORMAT: 
        SUBJECT: [Your generated subject]
        BODY: [Your generated message]
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
                    raw_content = data['choices'][0]['message']['content'].strip()
                    
                    subject = "Introduction: Pixartual Studio"
                    body = raw_content
                    
                    if "SUBJECT:" in raw_content and "BODY:" in raw_content:
                        parts = raw_content.split("BODY:", 1)
                        subject = parts[0].replace("SUBJECT:", "").strip()
                        body = parts[1].strip()
                    
                    logger.info(f"Proposal Generated for [bold cyan]{lead_name}[/bold cyan] ({channel})")
                    return (subject, body)
                else:
                    return ("Outreach Error", f"Error generating proposal: {response.text}")

        except Exception as e:
            logger.error(f"Proposal Exception: {e}")
            return ("Outreach Exception", f"Exception in proposal generation: {e}")

if __name__ == "__main__":
    proposer = Proposer()
    res = asyncio.run(proposer.generate_proposal("Dental Clinic", "Their website is not mobile responsive and has outdated 2010 graphics."))
    print(res)
