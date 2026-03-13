import pandas as pd
import os


def merge_outputs():
	files = [
		"output/maps_leads.xlsx",
		"output/indiamart_leads.xlsx",
		"output/instagram_leads.xlsx",
		"output/instagram_network_leads.xlsx",
		"output/linkedin_leads.xlsx",
	]

	frames = []

	for f in files:
		if os.path.exists(f):
			try:
				df = pd.read_excel(f)
				frames.append(df)
			except:
				pass

	if not frames:
		return

	merged = pd.concat(frames, ignore_index=True)

	key_cols = [c for c in ["Company", "Website", "Instagram", "LinkedIn"] if c in merged.columns]
	if key_cols:
		merged.drop_duplicates(subset=key_cols, inplace=True)
	else:
		merged.drop_duplicates(inplace=True)

	merged.to_excel("output/master_leads.xlsx", index=False)