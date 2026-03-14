import pandas as pd
import time
import urllib.parse
import os

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from utils.instagram_bio_parser import parse_instagram_bio

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

STATE_FILE = "instagram_state.json"
MASTER_SEEN_FILE = "output/master_seen_urls.txt"

# Ensure output directory exists for our master file
os.makedirs("output", exist_ok=True)

def load_seen_urls():
    """Loads previously scraped URLs from previous runs."""
    if os.path.exists(MASTER_SEEN_FILE):
        with open(MASTER_SEEN_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_seen_url(url):
    """Saves a URL permanently so we never scrape it again."""
    with open(MASTER_SEEN_FILE, "a", encoding="utf-8") as f:
        f.write(f"{url}\n")


def safe_google_search(page, url):
    """Navigates to Google safely, handling CAPTCHAs automatically."""
    page.goto(url, timeout=30000)
    
    try:
        page.wait_for_selector("h3", timeout=5000)
    except PlaywrightTimeoutError:
        if "sorry" in page.url.lower() or "captcha" in page.url.lower():
            print("\nGOOGLE CAPTCHA DETECTED ON INSTAGRAM SEARCH!")
            print("Cooling down for 10 minutes to reset Google's flags...")
            time.sleep(600)  
            print("\n Cool-down finished. Retrying...")
            page.goto(url, timeout=30000)
            page.wait_for_selector("h3", timeout=15000)
        else:
            raise PlaywrightTimeoutError("Timeout waiting for h3, and no CAPTCHA detected.")


def parse_instagram_profile(url, snippet_text=""):
    """
    DEPRECATED: Now using Playwright inline for better bio extraction.
    Kept for compatibility.
    """
    return "", "", "", "", ""


def scrape_instagram(query, limit, start_page=0):
    results = []
    
    # Load historical cache so we don't repeat work from yesterday!
    seen = load_seen_urls()
    initial_seen_count = len(seen)
    
    print(f"INSTAGRAM Loaded {initial_seen_count} previously scraped profiles from master cache.")
    
    page = start_page

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context_args = {
            "user_agent": HEADERS["User-Agent"],
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-IN", 
            "timezone_id": "Asia/Kolkata"
        }

        if os.path.exists(STATE_FILE):
            print(f"Loading saved browser session from {STATE_FILE}...")
            context_args["storage_state"] = STATE_FILE
        
        context = browser.new_context(**context_args)
        search_page = context.new_page()

        while len(results) < limit:
            dork = f"site:instagram.com {query} -inurl:p -inurl:reel -inurl:explore -inurl:tags -inurl:stories"
            
            # &nfpr=1 explicitly tells Google "DO NOT Auto-Correct my query"
            url = (
                "https://www.google.com/search?q="
                + urllib.parse.quote_plus(dork)
                + f"&start={page*10}"
                + "&nfpr=1"
            )

            print(f"\nINSTAGRAM Fetching Google Search Page {page + 1} (Start Offset: {page*10})")

            try:
                safe_google_search(search_page, url)
                
                extracted_data = search_page.evaluate("""
                    () => {
                        let data = [];
                        let headings = document.querySelectorAll('h3');
                        
                        headings.forEach(h3 => {
                            let a_tag = h3.closest('a');
                            if (a_tag && a_tag.href && a_tag.href.startsWith('http')) {
                                
                                let container = h3.closest('.g') || h3.parentElement.parentElement.parentElement;
                                let snippet = container ? container.innerText : h3.innerText; 
                                
                                data.push({
                                    title: h3.innerText,
                                    url: a_tag.href,
                                    snippet: snippet
                                });
                            }
                        });
                        return data;
                    }
                """)

                print(f"INSTAGRAM Profiles detected on page: {len(extracted_data)}")

                if not extracted_data:
                    print("INSTAGRAM Reached the end of Google results.")
                    break

                for item in extracted_data:
                    if len(results) >= limit:
                        break

                    ig_url = item['url']
                    snippet_text = item['snippet']

                    # Ensure it's a valid profile and not a generic Instagram link
                    if "instagram.com" not in ig_url or any(x in ig_url for x in ["/p/", "/reel/", "/explore/", "/tags/", "/stories/", "/dir/"]):
                        continue
                        
                    if ig_url in seen:
                        continue
                    
                    seen.add(ig_url)
                    save_seen_url(ig_url) # Save permanently to the master text file!

                    # Parse profile using Playwright for better bio extraction
                    phone, email, whatsapp, bio, username = "", "", "", "", ""
                    parsed_url = urllib.parse.urlparse(ig_url)
                    username = parsed_url.path.strip("/").split("/")[0]

                    if username and username not in ["about", "developer", "help"]:
                        try:
                            with context.new_page() as profile_page:
                                profile_page.goto(ig_url, timeout=30000)
                                profile_page.wait_for_load_state('networkidle')

                                # Try to get bio from meta description
                                meta_desc = profile_page.query_selector('meta[name="description"]')
                                if meta_desc:
                                    content = meta_desc.get_attribute('content')
                                    if content and ":" in content:
                                        bio = content.split(":", 1)[-1].strip()
                                        if bio.startswith('"') and bio.endswith('"'):
                                            bio = bio[1:-1]

                                # If not found, try to find the actual bio element on the page
                                if not bio:
                                    # Instagram bio is typically in a span or div with specific structure
                                    bio_element = profile_page.query_selector('div[data-testid="user-biography"] span') or \
                                                 profile_page.query_selector('span[data-testid="user-biography"]') or \
                                                 profile_page.query_selector('.-vDIg span')  # Fallback class
                                    if bio_element:
                                        bio = bio_element.inner_text()

                                text_to_scan = f"{bio} {snippet_text}"
                                email, phone, whatsapp = parse_instagram_bio(text_to_scan)

                        except Exception as e:
                            print(f"Error parsing profile {ig_url}: {e}")

                    # Skip if no username
                    if not username:
                        continue

                    results.append({
                        "Company": item['title'].replace(" - Instagram", "").replace("Instagram", "").strip(" -|"),
                        "Type": "Instagram Brand",
                        "Website": "",
                        "Email": email,
                        "Phone": phone,
                        "WhatsApp": whatsapp,
                        "Profile": f"https://instagram.com/{username}",
                        "Source": "Instagram",
                        "Bio": bio
                    })

                    print(f"FOUND @{username} | Phone: {phone} | Email: {email}")
                    time.sleep(1) 

            except PlaywrightTimeoutError:
                print("INSTAGRAM Skipping page due to timeout/no results.")
                break
            except Exception as e:
                print("INSTAGRAM error:", e)
                break

            page += 1

        print(f"\nSaving browser session to {STATE_FILE}...")
        context.storage_state(path=STATE_FILE)
        browser.close()

    df = pd.DataFrame(results)
    
    if not df.empty:
        df.drop_duplicates(subset=["Profile"], inplace=True)
        df = df.head(limit)

    os.makedirs("output", exist_ok=True)
    df.to_excel("output/instagram_leads.xlsx", index=False)
    print(f"\nINSTAGRAM Scraping finished. Saved {len(results)} new leads.")