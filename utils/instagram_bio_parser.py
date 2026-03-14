import re

# Improved phone regex to handle more international formats
PHONE_REGEX = r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{1,4}\)?[-.\s]?)?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}"

# Standard email regex
EMAIL_REGEX = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"


def extract_email(text):
	emails = re.findall(EMAIL_REGEX, text)
	if emails:
		return emails[0]
	return ""


def extract_phone(text):
	phones = re.findall(PHONE_REGEX, text)
	# Filter for reasonable phone lengths (7-15 digits)
	valid_phones = [p for p in phones if 7 <= len(re.sub(r'\D', '', p)) <= 15]
	if valid_phones:
		return valid_phones[0]
	return ""


def extract_whatsapp(text):
	text = text.lower()

	if "whatsapp" in text or "wa" in text:
		phone = extract_phone(text)
		if phone:
			return phone

	return ""


def parse_instagram_bio(bio):

	email = extract_email(bio)
	phone = extract_phone(bio)
	whatsapp = extract_whatsapp(bio)

	return email, phone, whatsapp