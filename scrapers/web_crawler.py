import asyncio
import httpx
import re
import random
import os
from bs4 import BeautifulSoup
from typing import List, Dict, Set, Optional
from playwright.async_api import async_playwright, Page, BrowserContext

from core.logger import logger
from core.utils import is_valid_email

class WebCrawler:
    """
    An advanced web crawler designed for deep contact enrichment.
    
    Extracts emails, social media links, and contextual business information 
    (About Us) to empower AI-driven personalization.
    """

    def __init__(self) -> None:
        self.email_regex: re.Pattern = re.compile(
            r'[a-zA-Z0-9._%+-]+@(?![0-9]x)[a-zA-Z0-9.-]+\.(?!png|jpg|jpeg|gif|webp|svg|pdf|zip|mp4|png|js|css|woff|woff2)[a-zA-Z]{2,}', 
            re.I
        )
        self.social_patterns: Dict[str, str] = {
            "linkedin": r'linkedin\.com/(?:company|in)/[^/"]+',
            "facebook": r'facebook\.com/[^/"]+',
            "instagram": r'instagram\.com/[^/"]+',
            "twitter": r'twitter\.com/[^/"]+'
        }

    async def crawl(self, url: str, business_name: str, query_id: str = "default") -> Dict[str, any]:
        """
        Performs a deep crawl of a business website.
        
        Args:
            url: The base URL of the business.
            business_name: Name of the business for context enhancement.
            query_id: ID of the search query for folder organization.
            
        Returns:
            A dictionary containing discovered emails, social links, and About Us info.
        """
        if not url or "google.com" in url:
            return {}
        
        if not url.startswith("http"):
            url = f"https://{url}"

        # Ensure directory exists
        screenshot_dir = os.path.join("data", "screenshots", query_id)
        os.makedirs(screenshot_dir, exist_ok=True)
        safe_name = re.sub(r'[^\w\s-]', '', business_name).strip().replace(' ', '_')
        screenshot_filename = os.path.join(screenshot_dir, f"{safe_name}_{random.randint(1000, 9999)}.png")
        
        try:
            async with async_playwright() as p:
                # Stealth Setup
                user_agents = [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
                ]
                browser = await p.chromium.launch(headless=True)
                try:
                    context = await browser.new_context(
                        user_agent=random.choice(user_agents),
                        viewport={'width': random.randint(1024, 1440), 'height': random.randint(768, 900)}
                    )
                    page = await context.new_page()
                    
                    # Load Page
                    logger.info(f"Navigating to [cyan]{url}[/cyan]...")
                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                        await asyncio.sleep(3) # Give time for animations to settle
                    except Exception as e:
                        logger.warning(f"Resilient loading for {url}: {e}")
                    
                    # Screenshot
                    try:
                        await page.screenshot(path=screenshot_filename, timeout=10000)
                    except:
                        logger.warning(f"Screenshot failed for {url}")
                    
                    # Content Extraction
                    html = await page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    text_content = await page.evaluate("() => document.body.innerText")
                    
                    # General Audit Info
                    audit_info = {
                        "title": await page.title(),
                        "has_og_image": bool(soup.find("meta", property="og:image")),
                        "is_responsive": "viewport" in html.lower(),
                        "has_modern_framework": any(kw in html.lower() for kw in ["next.js", "react", "tailwind", "webflow", "framer"]),
                        "text_content": text_content[:2000]
                    }
                    
                    # Extract Emails & Socials
                    found_emails = self.email_regex.findall(html)
                    emails = {e.lower().strip() for e in found_emails if is_valid_email(e)}
                    
                    social_links = {}
                    for platform, pattern in self.social_patterns.items():
                        links = await page.evaluate("""
                            (patternStr) => {{
                                const reg = new RegExp(patternStr);
                                return Array.from(document.querySelectorAll('a'))
                                    .map(a => a.href)
                                    .filter(href => reg.test(href));
                            }}
                        """, pattern)
                        if links: social_links[platform] = links[0]
                    
                    if emails and social_links:
                        logger.info("Smart Crawl: Essential info found on home page. Skipping deep 'About' crawl.")
                        about_info = text_content[:1500]  # Use home page content for AI context
                    else:
                        # Deep Founder Search
                        about_info = await self.extract_about_info(page)
                    
                    logger.info(f"Crawled [cyan]{url}[/cyan]: Metadata extracted.")
                    
                    return {
                        "emails": list(emails),
                        "social_links": social_links,
                        "audit_info": audit_info,
                        "screenshot_path": screenshot_filename if os.path.exists(screenshot_filename) else None,
                        "about_us_info": about_info
                    }
                finally:
                    await browser.close()

        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return {}

    async def extract_about_info(self, page) -> str:
        """Finds About/Team links and extracts personal/vision context."""
        try:
            # Find About/Team links
            about_link = await page.evaluate("""
                () => {
                    const keywords = ['about', 'team', 'story', 'our-values', 'who-we-are', 'contact'];
                    const links = Array.from(document.querySelectorAll('a'));
                    const found = links.find(a => 
                        keywords.some(kw => a.href.toLowerCase().includes(kw)) ||
                        keywords.some(kw => a.innerText.toLowerCase().includes(kw))
                    );
                    return found ? found.href : null;
                }
            """)
            
            if about_link and about_link.startswith("http"):
                logger.info(f"Found Deep Link: [yellow]{about_link}[/yellow]")
                await page.goto(about_link, wait_until="networkidle", timeout=15000)
                text = await page.evaluate("() => document.body.innerText")
                return text[:1500] # Limit to 1500 chars for AI
            return ""
        except Exception as e:
            logger.warning(f"Could not extract deep about info: {e}")
            return ""

if __name__ == "__main__":
    crawler = WebCrawler()
    res = asyncio.run(crawler.crawl("https://example.com"))
    print(res)
