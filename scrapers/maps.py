import asyncio
import asyncio
import random
import re
from typing import List, Dict
from playwright.async_api import async_playwright
from core.logger import logger
from core.database import init_db
import aiosqlite
from core.config import settings

class MapsScraper:
    def __init__(self):
        self.base_url = "https://www.google.com/maps"

    async def scrape(self, query: str, max_results: int = 50):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True) 
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
            logger.info(f"Navigating to: [bold cyan]{search_url}[/bold cyan]")
            
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)
            
            # Handle Consent
            try:
                consent = page.get_by_role("button", name=re.compile("Accept|Agree", re.I)).first
                if await consent.is_visible():
                    await consent.click()
                    await asyncio.sleep(2)
            except:
                pass
            
            # Check for "No results found" and try expansion
            if await page.query_selector('text="No results found"') or not await page.query_selector('a.hfpxzc'):
                logger.warning(f"No results found for '{query}'. Trying expanded search...")
                expanded_query = f"{query} near me" if "near" not in query.lower() else query
                search_url = f"https://www.google.com/maps/search/{expanded_query.replace(' ', '+')}"
                await page.goto(search_url, wait_until="domcontentloaded")
                await asyncio.sleep(5)

            results_found = 0
            scraped_names = set()

            while results_found < max_results:
                # Get the verified result links
                links = await page.query_selector_all('a.hfpxzc')
                
                if not links:
                    logger.warning("No business links found. Scrolling page...")
                    await page.mouse.wheel(0, 2000)
                    await asyncio.sleep(3)
                    # Check if actually reached end
                    if "reached the end" in await page.content(): break
                    continue

                for link in links:
                    if results_found >= max_results: break
                    
                    try:
                        # The ARIA label of the link IS the business name usually!
                        label = await link.get_attribute("aria-label")
                        if not label or label in scraped_names:
                            continue

                        # Clean label (omit "Click to view..." parts)
                        name = label.strip()
                        
                        await link.scroll_into_view_if_needed()
                        await link.click()
                        
                        # WAIT for the detail panel to update to the new lead name
                        # This prevents the "same data for multiple leads" issue
                        try:
                            # Use new selector h1.DUwDvf for the business name in detail panel
                            await page.wait_for_function(
                                "name => document.querySelector('h1.DUwDvf')?.innerText.trim() === name || document.querySelector('h1')?.innerText.trim() === name",
                                arg=name,
                                timeout=8000
                            )
                        except:
                            logger.debug(f"Timeout waiting for detail panel update for {name}, proceeding anyway.")
                        
                        await asyncio.sleep(random.uniform(1, 2)) # Final settle
                        
                        # Website (Very important for audit)
                        website = None
                        website_el = await page.query_selector('a[data-item-id="authority"]')
                        if not website_el:
                            website_el = await page.query_selector('a[aria-label^="Website:"]')
                        
                        if website_el:
                            website = await website_el.get_attribute("href")
                        
                        # Double-check: Is the detail panel still showing the correct lead?
                        # Re-read name from detail panel
                        check_name_el = await page.query_selector('h1.DUwDvf')
                        if not check_name_el: check_name_el = await page.query_selector('h1')
                        current_detail_name = await check_name_el.inner_text() if check_name_el else ""
                        
                        if name.lower() not in current_detail_name.lower() and current_detail_name.lower() not in name.lower():
                            if current_detail_name.strip() == "Results":
                                logger.debug(f"Still seeing 'Results' header for {name}, trying one more brief wait...")
                                await asyncio.sleep(2)
                                current_detail_name = await check_name_el.inner_text() if check_name_el else ""
                            
                            if name.lower() not in current_detail_name.lower() and current_detail_name.lower() not in name.lower():
                                logger.warning(f"Data Mismatch! Expected {name} but found {current_detail_name}. Skipping...")
                                continue

                        # Deep Knowledge Extraction
                        rating = 0.0
                        reviews_count = 0
                        business_category = None
                        
                        # Rating & Reviews
                        try:
                            # Primary: combined aria-label on span.ZkP5Je
                            rating_el = await page.query_selector('span.ZkP5Je')
                            if not rating_el: rating_el = await page.query_selector('span.ceNzR')
                            
                            if rating_el:
                                rating_text = await rating_el.get_attribute("aria-label")
                                if rating_text:
                                    rating_match = re.search(r"(\d+\.\d+)", rating_text)
                                    if rating_match: rating = float(rating_match.group(1))
                                    
                                    reviews_match = re.search(r"(\d+[\d,]*) [Rr]eviews", rating_text)
                                    if reviews_match: 
                                        reviews_count = int(reviews_match.group(1).replace(",", ""))
                            
                            # Fallback if combined fails
                            if rating == 0.0:
                                val_el = await page.query_selector('span.MW4etd')
                                if val_el: rating = float(await val_el.inner_text())
                            if reviews_count == 0:
                                cnt_el = await page.query_selector('span.UY7F9')
                                if cnt_el:
                                    cnt_text = await cnt_el.inner_text()
                                    cnt_match = re.search(r"(\d+[\d,]*)", cnt_text)
                                    if cnt_match: reviews_count = int(cnt_match.group(1).replace(",", ""))
                        except Exception as e: 
                            logger.debug(f"Rating extraction error: {e}")

                        # Business Category
                        try:
                            category_el = await page.query_selector('button.DkEaL')
                            if not category_el: category_el = await page.query_selector('button[class*="DByne"]')
                            if category_el:
                                business_category = await category_el.inner_text()
                        except Exception as e:
                            logger.debug(f"Category extraction error: {e}")

                        # Phone (Very important for WhatsApp)
                        phone = None
                        phone_el = await page.query_selector('button[data-item-id^="phone:tel:"]')
                        if not phone_el:
                            phone_el = await page.query_selector('button[aria-label^="Phone:"]')
                            
                        if phone_el:
                            phone_attr = await phone_el.get_attribute("data-item-id") or await phone_el.get_attribute("aria-label")
                            phone = phone_attr.replace("phone:tel:", "").replace("Phone: ", "").strip()
                        
                        # Address
                        address = None
                        address_el = await page.query_selector('button[data-item-id="address"]')
                        if address_el:
                            address = await address_el.inner_text()

                        # Collect all leads as requested by user
                        logger.info(f"[[{results_found+1}/{max_results}]] Found Lead: [bold green]{name}[/bold green] | Web: {website or 'N/A'} | Phone: {phone or 'N/A'}")
                        
                        await self.save_lead({
                            "name": name,
                            "website": website,
                            "phone": phone,
                            "address": address,
                            "rating": rating,
                            "reviews_count": reviews_count,
                            "business_category": business_category,
                            "source": "Google Maps",
                            "category": query
                        })
                        
                        scraped_names.add(name)
                        results_found += 1
                        
                    except Exception as e:
                        logger.debug(f"Extraction error: {e}")
                        continue
                
                # Scroll the feed
                feed = await page.query_selector('div[role="feed"]')
                if feed:
                    await feed.evaluate("node => node.scrollBy(0, 2000)")
                    await asyncio.sleep(4)
                else:
                    await page.mouse.wheel(0, 2000)
                    await asyncio.sleep(4)

            logger.info(f"Done. Collected {results_found} leads for: {query}")
            await browser.close()

    async def save_lead(self, data: Dict):
        async with aiosqlite.connect(settings.DB_PATH) as db:
            async with db.execute("SELECT id FROM leads WHERE name = ?", (data['name'],)) as cursor:
                if await cursor.fetchone(): return
            
            await db.execute("""
                INSERT INTO leads (name, website, phone, address, rating, reviews_count, business_category, source, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (data['name'], data['website'], data['phone'], data['address'], data['rating'], data['reviews_count'], data['business_category'], data['source'], data['category']))
            await db.commit()
