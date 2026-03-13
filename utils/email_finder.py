import re
import requests
from bs4 import BeautifulSoup


EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"


def extract_email_from_text(text):

	emails = re.findall(EMAIL_REGEX, text)

	if emails:
		return list(set(emails))

	return []


def check_common_contact_pages(domain):

	pages = [
		"/contact",
		"/contact-us",
		"/about",
		"/about-us"
	]

	found = []

	for page in pages:

		try:

			url = domain.rstrip("/") + page

			r = requests.get(url, timeout=8)

			emails = extract_email_from_text(r.text)

			if emails:
				found.extend(emails)

		except:
			continue

	return list(set(found))


def google_email_search(company, domain):

	query = f"{company} email {domain}"

	search_url = f"https://www.google.com/search?q={query}"

	try:

		r = requests.get(
			search_url,
			headers={"User-Agent": "Mozilla/5.0"},
			timeout=10
		)

		return extract_email_from_text(r.text)

	except:
		return []


def find_email(company, website):

	if not website:
		return ""

	domain = website.split("/")[0] + "//" + website.split("/")[2]

	try:

		r = requests.get(website, timeout=8)

		emails = extract_email_from_text(r.text)

		if emails:
			return emails[0]

	except:
		pass

	emails = check_common_contact_pages(domain)

	if emails:
		return emails[0]

	emails = google_email_search(company, domain)

	if emails:
		return emails[0]

	return ""