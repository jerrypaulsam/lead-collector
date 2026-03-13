import re

PHONE_REGEX = r"(?:\+91[\-\s]?)?(?:0?[6-9]\d{9}|0?\(?\d{2,4}\)?[\-\s]?\d{6,8})"

# Standard email regex fallback
EMAIL_REGEX = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"


def extract_email(text):
	emails = re.findall(EMAIL_REGEX, text)
	if emails:
		return emails[0]
	return ""


def extract_phone(text):
	phones = re.findall(PHONE_REGEX, text)
	if phones:
		return phones[0]
	return ""


def extract_whatsapp(text):
	text = text.lower()

	if "whatsapp" in text:
		phone = extract_phone(text)
		if phone:
			return phone

	return ""


def parse_instagram_bio(bio):

	email = extract_email(bio)
	phone = extract_phone(bio)
	whatsapp = extract_whatsapp(bio)

	return email, phone, whatsapp