import asyncio
import httpx
import re
from bs4 import BeautifulSoup
from typing import Set, Dict
from core.logger import logger
from urllib.parse import urljoin, urlparse

class WebCrawler:
    def __init__(self):
        self.email_regex = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        # Common social media patterns
        self.social_patterns = {
            "linkedin": r'linkedin\.com/company/[^/"]+',
            "instagram": r'instagram\.com/[^/"]+',
            "facebook": r'facebook\.com/[^/"]+',
            "twitter": r'twitter\.com/[^/"]+'
        }

    async def crawl(self, url: str, lead_name: str = "Unassigned") -> Dict:
        if not url:
            return {}
        
        if not url.startswith("http"):
            url = f"https://{url}"

        # Setup paths
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', lead_name)
        screenshot_filename = f"data/screenshots/{safe_name}_{int(asyncio.get_event_loop().time())}.png"
        
        from playwright.async_api import async_playwright
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(viewport={'width': 1280, 'height': 800})
                
                # Load Page
                logger.info(f"Navigating to [cyan]{url}[/cyan]...")
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    await page.wait_for_timeout(3000) # Give time for animations to settle
                except Exception as e:
                    logger.warning(f"Resilient loading: Page.goto timed out or failed for {url}, proceeding with partial content: {e}")
                
                # Screenshot
                await page.screenshot(path=screenshot_filename)
                
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
                emails = set(self.email_regex.findall(html))
                social_links = {}
                for platform, pattern in self.social_patterns.items():
                    links = await page.evaluate(f"""
                        (patternStr) => {{
                            const reg = new RegExp(patternStr);
                            return Array.from(document.querySelectorAll('a'))
                                .map(a => a.href)
                                .filter(href => reg.test(href));
                        }}
                    """, pattern)
                    if links: social_links[platform] = links[0]
                
                # Deep Founder Search
                about_info = await self.extract_about_info(page)
                
                await browser.close()
                
                logger.info(f"Crawled [cyan]{url}[/cyan]: Screenshot saved to {screenshot_filename}")
                
                return {
                    "emails": list(emails),
                    "social_links": social_links,
                    "audit_info": audit_info,
                    "screenshot_path": screenshot_filename,
                    "about_us_info": about_info
                }

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
