import requests
import pandas as pd
import time
import urllib.parse
import re
import os

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

STATE_FILE = "browser_state.json"

PHONE_REGEX = r"(?:\+?91[\-\s]?)?[6789]\d{2}[\-\s]?\d{3}[\-\s]?\d{4}"
EMAIL_REGEX = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

def extract_phone(text):
    phones = re.findall(PHONE_REGEX, text)
    return re.sub(r'[\-\s]', '', phones[0]) if phones else ""

def extract_email(text):
    emails = re.findall(EMAIL_REGEX, text)
    return emails[0] if emails else ""

def scrape_page_for_contacts(url):
    phone = ""
    email = ""
    website = ""
    whatsapp = ""

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        
        if r.status_code != 200:
            return phone, email, website, whatsapp
            
        soup = BeautifulSoup(r.text, "lxml")
        visible_text = soup.get_text(" ", strip=True)

        phone = extract_phone(visible_text)
        email = extract_email(visible_text)

        links = soup.find_all("a", href=True)
        for link in links:
            href = link.get("href", "").lower()
            original_href = link.get("href", "")
            
            if "whatsapp" in href or "wa.me" in href:
                whatsapp = original_href
                
            if "mailto:" in href and not email:
                email = original_href.replace("mailto:", "").replace("MAILTO:", "").split("?")[0].strip()
            
            if href.startswith("http"):
                ignore_list = ["indiamart.com", "tradeindia.com", "facebook.com", "twitter.com", "whatsapp.com", "wa.me", "instagram.com", "linkedin.com"]
                if not any(domain in href for domain in ignore_list):
                    if not website: 
                        website = original_href

    except Exception:
        pass

    return phone, email, website, whatsapp

def safe_google_search(page, url):
    """Navigates to Google and explicitly waits/checks for CAPTCHAs."""
    page.goto(url, timeout=30000)
    
    try:
        page.wait_for_selector("h3", timeout=5000)
    except PlaywrightTimeoutError:
        if "sorry" in page.url.lower():
            print("\n GOOGLE CAPTCHA DETECTED! Please solve it in the browser window...")
            page.wait_for_selector("h3", timeout=300000) 
            print("CAPTCHA solved! Resuming scrape...")
        else:
            raise PlaywrightTimeoutError("Timeout waiting for h3, and no CAPTCHA detected.")

def find_official_website(website_page, company_name):
    query = f"{company_name} official website -indiamart -tradeindia -justdial"
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)

    try:
        safe_google_search(website_page, url)
        
        first_link = website_page.evaluate("""
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

def scrape_supplier_search(query, limit):
    results = []
    seen = set()
    page = 0

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
        website_page = context.new_page()

        while len(results) < limit:
            search_query = f"{query} manufacturer supplier site:indiamart.com OR site:tradeindia.com"

            url = (
                "https://www.google.com/search?q="
                + urllib.parse.quote_plus(search_query)
                + f"&start={page*10}"
            )

            print("\n SUPPLIER SEARCH Fetching:", url)

            try:
                safe_google_search(search_page, url)
                
                extracted_links = search_page.evaluate("""
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

                print(f"SUPPLIER SEARCH results detected on page: {len(extracted_links)}")

                if not extracted_links:
                    break

                for item in extracted_links:
                    if len(results) >= limit:
                        break

                    supplier_url = item['url']
                    raw_title = item['title'].strip()

                    if "google.com" in supplier_url or supplier_url in seen:
                        continue
                    seen.add(supplier_url)

                    im_phone, im_email, im_website, im_whatsapp = scrape_page_for_contacts(supplier_url)
                    company_name = raw_title.split("-")[0].split(" in ")[0].replace("IndiaMART", "").strip()

                    final_website = im_website
                    
                    if not final_website:
                        print(f" No website on directory. Hunting Google for: {company_name}")
                        final_website = find_official_website(website_page, company_name)
                    else:
                        print(f" Found website directly on directory: {final_website}")

                    final_phone, final_email, final_whatsapp = im_phone, im_email, im_whatsapp

                    if final_website:
                        print(f"    -> Extracting contacts from: {final_website}")
                        w_phone, w_email, _, w_whatsapp = scrape_page_for_contacts(final_website)

                        if w_phone: final_phone = w_phone
                        if w_email: final_email = w_email
                        if w_whatsapp: final_whatsapp = w_whatsapp

                    source = "Other"
                    if "indiamart" in supplier_url: source = "IndiaMART"
                    elif "tradeindia" in supplier_url: source = "TradeIndia"

                    results.append({
                        "Company": company_name,
                        "Website": final_website,
                        "Email": final_email,
                        "Phone": final_phone,
                        "WhatsApp": final_whatsapp,
                        "Profile": supplier_url,
                        "Source": source
                    })

                    print(f"FOUND {company_name} | Phone: {final_phone} | Email: {final_email}")
                    time.sleep(1)

            except PlaywrightTimeoutError:
                print("SUPPLIER SEARCH Skipping page due to timeout/no results.")
                break
            except Exception as e:
                print("SUPPLIER SEARCH error:", e)
                break

            page += 1

        print(f"\n Saving browser session to {STATE_FILE}...")
        context.storage_state(path=STATE_FILE)
        browser.close()

    df = pd.DataFrame(results)
    os.makedirs("output", exist_ok=True)
    df.to_excel("output/supplier_search_leads.xlsx", index=False)
    print(f"SUPPLIER SEARCH Scraping finished. Saved {len(results)} leads.")