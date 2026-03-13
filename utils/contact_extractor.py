import re
import requests
from bs4 import BeautifulSoup

from utils.email_finder import find_email

# STRICT regex for Indian Mobile Numbers (e.g., +91 9876543210, 98765-43210)
# Ensures it starts with 6, 7, 8, or 9
PHONE_REGEX = r"(?:\+?91[\-\s]?)?[6789]\d{2}[\-\s]?\d{3}[\-\s]?\d{4}"

# Standard email regex fallback
EMAIL_REGEX = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

def extract_contacts(company, website):
    email = ""
    phone = ""
    whatsapp = ""

    if not website:
        return email, phone, whatsapp

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        
        r = requests.get(website, headers=headers, timeout=10)

        soup = BeautifulSoup(r.text, "lxml")
        
        visible_text = soup.get_text(" ", strip=True)

        phones = re.findall(PHONE_REGEX, visible_text)
        if phones:
            phone = re.sub(r'[\-\s]', '', phones[0])

        for link in soup.find_all("a", href=True):
            href = link["href"].lower()

            if "whatsapp" in href or "wa.me" in href:
                whatsapp = link["href"]
            
            if "mailto:" in href and not email:
                email = href.replace("mailto:", "").split("?")[0].strip()

        if not email:
            emails = re.findall(EMAIL_REGEX, visible_text)
            if emails:
                email = emails[0]

    except Exception as e:
        print(f" Error scraping {website}: {e}")

    if not email:
        email = find_email(company, website)

    return email, phone, whatsapp