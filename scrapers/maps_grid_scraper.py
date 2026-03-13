import asyncio
import pandas as pd
import random
import urllib.parse
import os

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Assuming these are your local modules
from utils.geo_utils import generate_grid
from utils.contact_extractor import extract_contacts
from utils.classifier import classify_business

# --- SAFE CONFIGURATION ---
GRID_WORKERS = 1           # Down to 1 to mimic a single human browsing safely
PER_CELL_LIMIT = 8         # How many leads to grab per grid coordinate
SCROLL_LOOPS = 6           # How many times to scroll the Maps sidebar
STATE_FILE = "browser_state.json"  # Saves your session to prevent repeated bot checks


async def safe_maps_load(page, url, max_retries=2):
    """Loads Google Maps and checks for CAPTCHAs. Triggers a 10-min cool-down if blocked."""
    for attempt in range(max_retries):
        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(3000)
        
        # Check if Google redirected us to their "Sorry" CAPTCHA page
        if "sorry" in page.url.lower() or "captcha" in page.url.lower():
            print(f"\n CAPTCHA DETECTED! Google is suspicious of our speed.")
            print(f"Cooling down for 10 minutes... (Attempt {attempt + 1}/{max_retries})")
            
            # Sleep for exactly 10 minutes (600 seconds)
            await asyncio.sleep(600)  
            
            print("\n Cool-down finished. Retrying the search...")
            continue # Loop restarts and tries to load the URL again
            
        return True # Loaded safely!
        
    print("Failed to bypass CAPTCHA after cool-downs. Moving to next cell.")
    return False


async def collect_links(page, query, lat, lon):
    links = []
    # Standard, reliable Google Maps search URL format
    safe_query = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/maps/search/{safe_query}/@{lat},{lon},14z"

    print(f"[GRID] Scanning {lat},{lon}")

    try:
        # Pass the URL through our safe loader
        loaded_safely = await safe_maps_load(page, url)
        if not loaded_safely:
            return links

        # Explicitly target the scrollable sidebar feed instead of blind mouse wheeling
        feed_selector = 'div[role="feed"]'
        
        try:
            await page.wait_for_selector(feed_selector, timeout=10000)
            
            for _ in range(SCROLL_LOOPS):
                # Use JavaScript to cleanly scroll the container to the bottom
                await page.evaluate(f"""
                    let feed = document.querySelector('{feed_selector}');
                    if (feed) feed.scrollBy(0, {random.randint(2000, 4000)});
                """)
                await page.wait_for_timeout(random.randint(1000, 2000))
        except PlaywrightTimeoutError:
            print(f"    No scrollable feed found for {lat},{lon}. Capturing visible pins.")

        # Grab the links for the businesses
        anchors = await page.locator('a[href*="/maps/place"]').all()

        for a in anchors:
            try:
                href = await a.get_attribute("href")
                if href and href not in links:
                    links.append(href)
            except:
                continue

    except Exception as e:
        print(f"    Error collecting links at {lat},{lon}: {e}")

    return links


async def parse_business(context, link):
    """Opens a temporary new tab for parsing to keep the browser environment clean."""
    page = await context.new_page()
    data = None
    
    try:
        # Check for CAPTCHAs on the individual business page too
        loaded_safely = await safe_maps_load(page, link)
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
                # RUNS IN BACKGROUND: Prevents your synchronous 'requests' scraper from freezing Playwright!
                email, phone, whatsapp = await asyncio.to_thread(extract_contacts, name, website)
            except Exception as e:
                print(f"    Contact extraction failed for {name}: {e}")

        print(f"[FOUND] {name}")

        data = {
            "Company": name,
            "Type": classify_business(name),
            "Website": website,
            "Email": email,
            "Phone": phone,
            "WhatsApp": whatsapp,
            "Source": "Google Maps Grid"
        }

    except Exception as e:
        print(f"   Business parse failed for {link}: {e}")
    finally:
        # Always close the temporary tab to free up RAM
        await page.close()

    return data


async def scrape_cell(context, query, lat, lon, results, limit):
    search_page = await context.new_page()

    try:
        links = await collect_links(search_page, query, lat, lon)
        print(f"  Collected {len(links)} links in cell.")

        for link in links[:PER_CELL_LIMIT]:
            if len(results) >= limit:
                break

            data = await parse_business(context, link)

            if data:
                results.append(data)

            # HUMAN BEHAVIOR: Sleep for a random interval between 2 and 3.5 seconds
            await asyncio.sleep(random.uniform(2.0, 3.5))

    except Exception as e:
        print(f"Grid cell failed: {e}")
    finally:
        await search_page.close()


async def worker(context, queue, query, results, limit):
    while not queue.empty():
        lat, lon = await queue.get()
        
        if len(results) >= limit:
            queue.task_done()
            continue
            
        await scrape_cell(context, query, lat, lon, results, limit)
        queue.task_done()


async def run(query, limit, city):
    results = []
    grid = generate_grid(city)
    queue = asyncio.Queue()

    for cell in grid:
        await queue.put(cell)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False, # Headless=False is infinitely safer against Google Bot Detection
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context_args = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-IN", 
            "timezone_id": "Asia/Kolkata"
        }

        # LOAD SESSION: Proves to Google you are the same human from yesterday
        if os.path.exists(STATE_FILE):
            print(f"[!] Loading saved browser session from {STATE_FILE}...")
            context_args["storage_state"] = STATE_FILE

        context = await browser.new_context(**context_args)
        tasks = []

        for _ in range(GRID_WORKERS):
            tasks.append(
                asyncio.create_task(
                    worker(context, queue, query, results, limit)
                )
            )

        await queue.join()

        for t in tasks:
            t.cancel()

        # SAVE SESSION: Saves cookies for tomorrow's run
        print(f"Saving browser session to {STATE_FILE}...")
        await context.storage_state(path=STATE_FILE)

        await browser.close()

    df = pd.DataFrame(results)

    if not df.empty:
        df.drop_duplicates(subset=["Company"], inplace=True)
        df = df.head(limit)

    os.makedirs("output", exist_ok=True)
    df.to_excel("output/maps_grid_leads.xlsx", index=False)

    print(f"GRID Scraping finished. Saved {len(df)} leads.")


def scrape_maps_grid(query, limit, city):
    if city:
        query = f"{query} {city}"

    asyncio.run(run(query, limit, city))