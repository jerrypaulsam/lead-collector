def classify_business(name):

	name = name.lower()

	if "manufacturer" in name or "factory" in name:
		return "Manufacturer"

	if "boutique" in name:
		return "Boutique"

	if "fashion" in name or "label" in name:
		return "Brand"

	return "Unknown"