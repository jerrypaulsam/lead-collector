import asyncio
import pandas as pd
import urllib.parse
import os
import re
from bs4 import BeautifulSoup

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

STATE_FILE = "linkedin_state.json"
MASTER_SEEN_FILE = "output/master_seen_urls.txt"

PHONE_REGEX = r"(?:\+91[\-\s]?)?(?:0?[6-9]\d{9}|0?\(?\d{2,4}\)?[\-\s]?\d{6,8})"
EMAIL_REGEX = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

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


def build_queries(query):
    return [
        f"site:linkedin.com/company {query}",
        f"{query} site:linkedin.com/company",
        f"{query} manufacturer linkedin",
        f"{query} supplier linkedin",
    ]

async def extract_contacts(context, website_url):
    phone = ""
    email = ""
    whatsapp = ""

    if not website_url:
        return phone, email, whatsapp

    try:
        response = await context.request.get(website_url, timeout=10000)
        
        if not response.ok:
            return phone, email, whatsapp

        html = await response.text()
        soup = BeautifulSoup(html, "lxml")
        visible_text = soup.get_text(" ", strip=True)

        phones = re.findall(PHONE_REGEX, visible_text)
        if phones:
            phone = re.sub(r'[\-\s]', '', phones[0])

        emails = re.findall(EMAIL_REGEX, visible_text)
        if emails:
            email = emails[0]

        for link in soup.find_all("a", href=True):
            href = link.get("href", "").lower()
            original_href = link.get("href", "")
            
            if "whatsapp" in href or "wa.me" in href:
                whatsapp = original_href
                
            if "mailto:" in href and not email:
                email = original_href.replace("mailto:", "").replace("MAILTO:", "").split("?")[0].strip()

    except Exception:
        pass

    return phone, email, whatsapp

async def safe_google_search(page, url):
    """Async version: Navigates to Google and explicitly waits/checks for CAPTCHAs."""
    await page.goto(url, timeout=30000)
    
    try:
        await page.wait_for_selector("h3", timeout=5000)
    except PlaywrightTimeoutError:
        if "sorry" in page.url.lower() or "captcha" in page.url.lower():
            print("\n[🚨] GOOGLE CAPTCHA DETECTED! Please solve it in the browser window...")
            await page.wait_for_selector("h3", timeout=300000) 
            print("[✅] CAPTCHA solved! Resuming scrape...")
        else:
            raise PlaywrightTimeoutError("Timeout waiting for h3, and no CAPTCHA detected.")

async def find_official_website(website_page, company_name):
    query = f"{company_name} official website -linkedin -indiamart -justdial"
    # Added &nfpr=1 to prevent Google auto-correct here as well
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query) + "&nfpr=1"

    try:
        await safe_google_search(website_page, url)
        
        first_link = await website_page.evaluate("""
            () => {
                let headings = document.querySelectorAll('h3');
                for (let h3 of headings) {
                    let a_tag = h3.closest('a');
                    if (a_tag && a_tag.href && a_tag.href.startsWith('http') && !a_tag.href.includes('google.com')) {
                        return a_tag.href;
                    }
                }
                return "";
            }
        """)
        return first_link
    except:
        return ""


# Added start_page parameter!
async def run(query, limit, start_page=0):
    results = []
    
    # Load historical cache
    seen = load_seen_urls()
    print(f"[LinkedIn] Loaded {len(seen)} previously scraped profiles from master cache.")
    
    queries = build_queries(query)

    async with async_playwright() as p:
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

        if os.path.exists(STATE_FILE):
            print(f"Loading saved browser session from {STATE_FILE}...")
            context_args["storage_state"] = STATE_FILE

        context = await browser.new_context(**context_args)
        
        search_page = await context.new_page()
        website_page = await context.new_page() 

        for q in queries:
            page_num = start_page # Apply pagination!

            while len(results) < limit:
                url = (
                    "https://www.google.com/search?q="
                    + urllib.parse.quote_plus(q)
                    + f"&start={page_num*10}"
                    + "&nfpr=1" # Anti-autocorrect added
                )

                print(f"\n[LinkedIn] Opening: {url}")

                try:
                    await safe_google_search(search_page, url)

                    extracted_links = await search_page.evaluate("""
                        () => {
                            let data = [];
                            let headings = document.querySelectorAll('h3');
                            headings.forEach(h3 => {
                                let a_tag = h3.closest('a');
                                if (a_tag && a_tag.href && a_tag.href.startsWith('http')) {
                                    data.push({
                                        title: h3.innerText,
                                        url: a_tag.href
                                    });
                                }
                            });
                            return data;
                        }
                    """)

                    print(f"LinkedIn results detected on page: {len(extracted_links)}")

                    if not extracted_links:
                        print("[LinkedIn] Reached the end of Google results for this query.")
                        break

                    for item in extracted_links:
                        if len(results) >= limit:
                            break

                        linkedin_url = item['url']
                        
                        if "linkedin.com/company" not in linkedin_url or linkedin_url in seen:
                            continue

                        # Save to both our local run set and the permanent cache file!
                        seen.add(linkedin_url)
                        save_seen_url(linkedin_url)

                        title = item['title']
                        company = title.replace(" | LinkedIn", "").replace("- LinkedIn", "").strip()

                        print(f"Found LinkedIn: {company}. Hunting for official website...")
                        
                        website_url = await find_official_website(website_page, company)
                        
                        phone = ""
                        email = ""
                        whatsapp = ""

                        if website_url:
                            print(f"    -> Found website: {website_url}. Extracting contacts...")
                            phone, email, whatsapp = await extract_contacts(context, website_url)
                        else:
                            print("    -> No official website found.")

                        results.append({
                            "Company": company,
                            "Website": website_url,
                            "Email": email,
                            "Phone": phone,
                            "WhatsApp": whatsapp,
                            "LinkedIn": linkedin_url,
                            "Source": "LinkedIn"
                        })

                        await asyncio.sleep(1)

                except PlaywrightTimeoutError:
                    print("LinkedIn Skipping page due to timeout/no results.")
                    break 
                except Exception as e:
                    print(f"LinkedIn Error: {e}")
                    break

                page_num += 1

            if len(results) >= limit:
                break

        print(f"\nSaving browser session to {STATE_FILE}...")
        await context.storage_state(path=STATE_FILE)
        
        await browser.close()

    df = pd.DataFrame(results)

    if not df.empty:
        df.drop_duplicates(subset=["LinkedIn"], inplace=True)
        df = df.head(limit)

    os.makedirs("output", exist_ok=True)
    df.to_excel("output/linkedin_leads.xlsx", index=False)

    print(f"LinkedIn Scraping finished. Saved {len(results)} new leads.")

def scrape_linkedin(query, limit, start_page=0):
    asyncio.run(run(query, limit, start_page))