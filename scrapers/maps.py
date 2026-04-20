import asyncio
import random
import re
from typing import List, Dict, Set, Optional
from playwright.async_api import async_playwright, Page, BrowserContext, ElementHandle

from core.logger import logger
from core.database import get_db, init_db
from core.config import settings
from core.connectors import (
    log_connector_rejection,
    normalize_connector_record,
    persist_lead_source,
    validate_connector_record,
)

class MapsScraper:
    """
    A high-performance Google Maps scraper with advanced human-mimicry.
    
    Designed to extract business leads (names, websites, phones, ratings) 
    while avoiding detection through randomized interaction patterns.
    """

    def __init__(self) -> None:
        self.base_url: str = "https://www.google.com/maps"
        self.user_agents: List[str] = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
        ]

    async def scrape(self, query: str, max_results: int = 50) -> None:
        """
        Executes a targeted scrape based on the provided search query.
        
        Args:
            query: The search string (e.g., 'Dentists in Los Angeles').
            max_results: The maximum number of leads to collect.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': random.randint(1280, 1920), 'height': random.randint(720, 1080)},
                user_agent=random.choice(self.user_agents)
            )
            page = await context.new_page()
            
            search_url = f"{self.base_url}/search/{query.replace(' ', '+')}"
            logger.info(f"Initiating scrape for: [bold cyan]{query}[/bold cyan]")
            
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(5)
                
                await self._handle_consent(page)
                
                # Check for "No results found"
                if await page.query_selector('text="No results found"') or not await page.query_selector('a.hfpxzc'):
                    logger.warning(f"No results found for '{query}'. Trying expanded search...")
                    await page.goto(f"{search_url}+near+me", wait_until="domcontentloaded")
                    await asyncio.sleep(5)

                results_found = 0
                scraped_names: Set[str] = set()

                while results_found < max_results:
                    links = await page.query_selector_all('a.hfpxzc')
                    
                    if not links:
                        if "reached the end" in await page.content():
                            break
                        await page.mouse.wheel(0, 2000)
                        await asyncio.sleep(3)
                        continue

                    for link in links:
                        if results_found >= max_results:
                            break
                        
                        try:
                            label = await link.get_attribute("aria-label")
                            if not label or label in scraped_names:
                                continue

                            await self._interact_with_lead(page, link, label)
                            lead_data = await self._extract_lead_details(page, label, query)
                            
                            if lead_data:
                                await self.save_lead(lead_data)
                                scraped_names.add(label)
                                results_found += 1
                                logger.info(f"[[{results_found}/{max_results}]] Found Lead: [bold green]{label}[/bold green]")
                            
                        except Exception as e:
                            logger.debug(f"Lead extraction error for {label}: {e}")
                            continue
                    
                    # Scroll feed for more results
                    feed = await page.query_selector('div[role="feed"]')
                    if feed:
                        await feed.evaluate("node => node.scrollBy(0, 2000)")
                        await asyncio.sleep(4)

            except Exception as e:
                logger.error(f"Global scrape failure for query '{query}': {e}")
            finally:
                await browser.close()

    async def _handle_consent(self, page: Page) -> None:
        """Navigates through Google's consent or cookie popups if they appear."""
        try:
            consent = page.get_by_role("button", name=re.compile("Accept|Agree", re.I)).first
            if await consent.is_visible():
                await consent.click()
                await asyncio.sleep(2)
        except Exception as e:
            logger.debug(f"Consent handling error: {e}")

    async def _interact_with_lead(self, page: Page, link: ElementHandle, name: str) -> None:
        """Simulates human interaction (scrolling, clicking) with a lead link."""
        if random.random() > 0.5:
            await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
        await link.scroll_into_view_if_needed()
        await link.click()
        
        # Wait for the detail panel to update
        try:
            await page.wait_for_function(
                "name => document.querySelector('h1.DUwDvf')?.innerText.trim() === name || document.querySelector('h1')?.innerText.trim() === name",
                arg=name,
                timeout=8000
            )
        except Exception as e:
            logger.debug(f"Timeout waiting for lead panel {name}: {e}")
        await asyncio.sleep(random.uniform(1, 2))

    async def _extract_lead_details(self, page: Page, name: str, category: str) -> Optional[Dict]:
        """Extracts deep metadata from the lead's detail panel."""
        # 1. Verification: Is the target correct?
        check_name_el = await page.query_selector('h1.DUwDvf')
        if not check_name_el:
            check_name_el = await page.query_selector('h1')
        current_name = await check_name_el.inner_text() if check_name_el else ""
        
        if name.lower() not in current_name.lower() and current_name.lower() not in name.lower():
            return None

        # 2. Extract Phone
        phone = None
        phone_el = await page.query_selector('button[data-item-id^="phone:tel:"]')
        if phone_el:
            phone_attr = await phone_el.get_attribute("data-item-id") or await phone_el.get_attribute("aria-label")
            phone = phone_attr.replace("phone:tel:", "").replace("Phone: ", "").strip()

        # 3. Extract Website
        website = None
        website_el = await page.query_selector('a[data-item-id="authority"]')
        if not website_el:
            website_el = await page.query_selector('a[aria-label^="Website:"]')
        if website_el:
            website = await website_el.get_attribute("href")

        # 4. Extract Rating & Business Type
        rating = 0.0
        reviews = 0
        biz_cat = None
        try:
            rating_el = await page.query_selector('span.ZkP5Je')
            if rating_el:
                txt = await rating_el.get_attribute("aria-label")
                if txt:
                    r_m = re.search(r"(\d+\.\d+)", txt)
                    rv_m = re.search(r"(\d+[\d,]*) [Rr]eviews", txt)
                    if r_m: rating = float(r_m.group(1))
                    if rv_m: reviews = int(rv_m.group(1).replace(",", ""))
            
            cat_el = await page.query_selector('button.DkEaL')
            if cat_el:
                biz_cat = await cat_el.inner_text()
        except Exception as e:
            logger.debug(f"Metadata extraction error for {name}: {e}")

        return {
            "name": name,
            "website": website,
            "phone": phone,
            "rating": rating,
            "reviews_count": reviews,
            "business_category": biz_cat,
            "source": "Google Maps",
            "category": category,
            "source_platform": "google_maps",
            "source_url": page.url,
        }

    async def save_lead(self, data: Dict) -> None:
        """Saves a lead and source provenance, logging normalized rejections."""
        normalized_source = normalize_connector_record(data)
        valid, reason_code = validate_connector_record(normalized_source)

        async with get_db() as db:
            if not valid:
                await log_connector_rejection(
                    db,
                    source_platform=normalized_source.get("source_platform", "unknown_source"),
                    reason_code=reason_code or "invalid_source_record",
                    reason_detail="Failed connector record validation before lead write.",
                    raw_payload=data,
                )
                await db.commit()
                return

            async with db.execute("SELECT id FROM leads WHERE name = ?", (data['name'],)) as cursor:
                existing = await cursor.fetchone()
                if existing:
                    await persist_lead_source(
                        db,
                        lead_id=existing[0],
                        record=normalized_source,
                        adapter_version="maps.v2",
                    )
                    await log_connector_rejection(
                        db,
                        source_platform=normalized_source["source_platform"],
                        reason_code="duplicate_lead_name",
                        reason_detail="Lead skipped because name already exists.",
                        raw_payload=data,
                    )
                    await db.commit()
                    return

            insert_cursor = await db.execute("""
                INSERT INTO leads (name, website, phone, rating, reviews_count, business_category, source, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (data['name'], data['website'], data['phone'], data['rating'], data['reviews_count'], data['business_category'], data['source'], data['category']))

            lead_id = insert_cursor.lastrowid
            if lead_id is not None:
                await persist_lead_source(
                    db,
                    lead_id=int(lead_id),
                    record=normalized_source,
                    adapter_version="maps.v2",
                )

            await db.commit()

if __name__ == "__main__":
    scraper = MapsScraper()
    asyncio.run(scraper.scrape("Dentists in California", max_results=5))
