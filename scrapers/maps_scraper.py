import asyncio
import pandas as pd
import random
import urllib.parse
import os

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from utils.classifier import classify_business
from utils.contact_extractor import extract_contacts

SCROLL_LIMIT = 8
STATE_FILE = "browser_state.json"


async def safe_maps_load(page, url, max_retries=2):
    """Loads Google Maps safely, checking for CAPTCHAs and triggering a 10-min cool-down if needed."""
    for attempt in range(max_retries):
        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(3000)
        
        if "sorry" in page.url.lower() or "captcha" in page.url.lower():
            print(f"\n CAPTCHA DETECTED! Cooling down for 10 minutes... (Attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(600)  
            print("\n Cool-down finished. Retrying...")
            continue 
            
        return True 
        
    print("Failed to bypass CAPTCHA. Moving on.")
    return False


async def collect_place_links(page, query):
    links = []
    
    # UPDATED: Using the standard Google Maps search URL instead of the weird googleusercontent one
    search_url = f"https://www.google.com/maps/search/{urllib.parse.quote_plus(query)}"

    print(f"MAPS Searching: {query}")

    loaded_safely = await safe_maps_load(page, search_url)
    if not loaded_safely:
        return links

    # UPDATED: Explicitly target and scroll the sidebar feed using JavaScript
    feed_selector = 'div[role="feed"]'
    
    try:
        await page.wait_for_selector(feed_selector, timeout=15000)
        
        for _ in range(SCROLL_LIMIT):
            await page.evaluate(f"""
                let feed = document.querySelector('{feed_selector}');
                if (feed) feed.scrollBy(0, {random.randint(2000, 4000)});
            """)
            await page.wait_for_timeout(random.randint(800, 1400))
    except PlaywrightTimeoutError:
        print("    No scrollable feed found. Capturing visible pins.")

    anchors = await page.locator('a[href*="/maps/place"]').all()

    for a in anchors:
        try:
            href = await a.get_attribute("href")
            if href and href not in links:
                links.append(href)
        except:
            continue

    return links


async def parse_business(context, url):
    """UPDATED: Opens a temporary new tab for parsing to keep the browser environment clean."""
    page = await context.new_page()
    data = None
    
    try:
        loaded_safely = await safe_maps_load(page, url)
        if not loaded_safely:
            await page.close()
            return None

        name = ""
        try:
            name = await page.locator("h1").inner_text(timeout=5000)
        except:
            await page.close()
            return None

        website = ""
        try:
            website = await page.locator('a[data-item-id="authority"]').get_attribute("href")
        except:
            pass

        email = ""
        phone = ""
        whatsapp = ""

        if website:
            try:
                # UPDATED: Run sync requests scraper in a background thread!
                email, phone, whatsapp = await asyncio.to_thread(extract_contacts, name, website)
            except Exception as e:
                print(f"    Contact extraction failed for {name}: {e}")

        print("[FOUND]", name)

        data = {
            "Company": name,
            "Type": classify_business(name),
            "Website": website,
            "Email": email,
            "Phone": phone,
            "WhatsApp": whatsapp,
            "Source": "Google Maps"
        }

    except Exception as e:
        print("Business parse failed:", e)
    finally:
        await page.close()

    return data


async def run(query, limit):
    results = []

    async with async_playwright() as p:
        # UPDATED: Headless=False and stealth args
        browser = await p.chromium.launch(
            headless=False, 
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context_args = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-IN", 
            "timezone_id": "Asia/Kolkata"
        }

        # UPDATED: Load session cache
        if os.path.exists(STATE_FILE):
            print(f"Loading saved browser session from {STATE_FILE}...")
            context_args["storage_state"] = STATE_FILE

        context = await browser.new_context(**context_args)
        search_page = await context.new_page()

        links = await collect_place_links(search_page, query)

        print(f"MAPS Collected {len(links)} business URLs")

        # Step 2: Visit business pages
        for link in links[:limit * 2]:
            if len(results) >= limit:
                break

            data = await parse_business(context, link)

            if data:
                results.append(data)

            # UPDATED: Human-like delay
            await asyncio.sleep(random.uniform(2.0, 3.5))

        # UPDATED: Save session cache before closing
        print(f"Saving browser session to {STATE_FILE}...")
        await context.storage_state(path=STATE_FILE)
        
        await browser.close()

    df = pd.DataFrame(results)

    if not df.empty:
        df.drop_duplicates(subset=["Company"], inplace=True)
        df = df.head(limit)

    os.makedirs("output", exist_ok=True)
    df.to_excel("output/maps_leads.xlsx", index=False)

    print("MAPS Scraping finished")


def scrape_maps(query, limit, location=""):
    if location:
        query = f"{query} {location}"

    asyncio.run(run(query, limit))
