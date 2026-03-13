import re

EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
PHONE_REGEX = r"\+?\d[\d\s\-]{8,}"


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