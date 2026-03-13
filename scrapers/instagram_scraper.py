import requests
import pandas as pd
import time
import urllib.parse
import os

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from utils.instagram_bio_parser import parse_instagram_bio

HEADERS = {
	"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
	"Accept-Language": "en-US,en;q=0.9"
}

STATE_FILE = "instagram_state.json"


def safe_google_search(page, url):
	"""Navigates to Google safely, handling CAPTCHAs automatically."""
	page.goto(url, timeout=30000)
	
	try:
		page.wait_for_selector("h3", timeout=5000)
	except PlaywrightTimeoutError:
		if "sorry" in page.url.lower() or "captcha" in page.url.lower():
			print("\n GOOGLE CAPTCHA DETECTED ON INSTAGRAM SEARCH!")
			print("Cooling down for 10 minutes to reset Google's flags...")
			time.sleep(600)  
			print("\n Cool-down finished. Retrying...")
			page.goto(url, timeout=30000)
			page.wait_for_selector("h3", timeout=15000)
		else:
			raise PlaywrightTimeoutError("Timeout waiting for h3, and no CAPTCHA detected.")


def parse_instagram_profile(url, snippet_text=""):
	"""
	Fetches the public meta-description from Instagram and passes it to your bio parser.
	"""
	phone, email, whatsapp, bio = "", "", "", ""
	
	parsed_url = urllib.parse.urlparse(url)
	username = parsed_url.path.strip("/").split("/")[0]

	try:
		r = requests.get(url, headers=HEADERS, timeout=10)
		
		content = ""
		if r.status_code == 200:
			soup = BeautifulSoup(r.text, "lxml")
			meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
			if meta_desc:
				content = meta_desc.get("content", "")
				
				if ":" in content:
					bio = content.split(":", 1)[-1].strip()
					if bio.startswith('"') and bio.endswith('"'):
						bio = bio[1:-1]
				else:
					bio = content

		# Use the bio if we got it, otherwise fall back to Google's text snippet
		text_to_scan = bio if bio else snippet_text

		# ---------------------------------------------------------
		# PARSER IN ACTION
		# ---------------------------------------------------------
		email, phone, whatsapp = parse_instagram_bio(text_to_scan)

	except Exception as e:
		# Silencing errors for a cleaner terminal
		pass
		
	return phone, email, whatsapp, bio, username


def scrape_instagram(query, limit):
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
			print(f"[!] Loading saved browser session from {STATE_FILE}...")
			context_args["storage_state"] = STATE_FILE
		
		context = browser.new_context(**context_args)
		search_page = context.new_page()

		while len(results) < limit:
			dork = f"site:instagram.com {query} -inurl:p -inurl:reel -inurl:explore -inurl:tags"
			
			url = (
				"https://www.google.com/search?q="
				+ urllib.parse.quote_plus(dork)
				+ f"&start={page*10}"
			)

			print(f"\n INSTAGRAM Fetching Google Search Page {page + 1}")

			try:
				safe_google_search(search_page, url)
				
				extracted_data = search_page.evaluate("""
					() => {
						let data = [];
						// Look for all headings instead of specific div classes
						let headings = document.querySelectorAll('h3');
						
						headings.forEach(h3 => {
							let a_tag = h3.closest('a');
							if (a_tag && a_tag.href && a_tag.href.startsWith('http')) {
								
								// Traverse up the DOM tree to grab the snippet text
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

				print(f"\n INSTAGRAM Profiles detected on page: {len(extracted_data)}")

				if not extracted_data:
					break

				for item in extracted_data:
					if len(results) >= limit:
						break

					ig_url = item['url']
					snippet_text = item['snippet']

					if "instagram.com" not in ig_url or "/p/" in ig_url or "/reel/" in ig_url:
						continue
						
					if ig_url in seen:
						continue
					seen.add(ig_url)

					phone, email, whatsapp, bio, username = parse_instagram_profile(ig_url, snippet_text)

					if not username:
						continue

					results.append({
						"Company": item['title'].replace(" - Instagram", "").strip(),
						"Type": "Instagram Brand",
						"Website": "",
						"Email": email,
						"Phone": phone,
						"WhatsApp": whatsapp,
						"Profile": f"https://instagram.com/{username}",
						"Source": "Instagram",
						"Bio": bio
					})

					print(f"[FOUND] @{username} | Phone: {phone} | Email: {email}")
					time.sleep(1) 

			except PlaywrightTimeoutError:
				print("INSTAGRAM Skipping page due to timeout/no results.")
				break
			except Exception as e:
				print("INSTAGRAM error:", e)
				break

			page += 1

		print(f"\n Saving browser session to {STATE_FILE}...")
		context.storage_state(path=STATE_FILE)
		browser.close()

	df = pd.DataFrame(results)
	
	if not df.empty:
		df.drop_duplicates(subset=["Profile"], inplace=True)
		df = df.head(limit)

	os.makedirs("output", exist_ok=True)
	df.to_excel("output/instagram_leads.xlsx", index=False)
	print(f"\n INSTAGRAM Scraping finished. Saved {len(results)} leads.")