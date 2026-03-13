import re

COMMON_LOCATIONS = {
    "tirupur", "surat", "delhi", "new delhi", "mumbai", "bangalore",
    "bengaluru", "jaipur", "ludhiana", "noida", "kolkata", "chennai",
    "coimbatore", "erode", "karur", "hyderabad", "pune", "india"
}

def clean_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s\-&]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text

def split_query_parts(query: str):
    cleaned = clean_text(query)
    words = cleaned.split()

    locations = []
    non_locations = []

    i = 0
    while i < len(words):
        two_word = " ".join(words[i:i+2])
        if two_word in COMMON_LOCATIONS:
            locations.append(two_word)
            i += 2
            continue

        if words[i] in COMMON_LOCATIONS:
            locations.append(words[i])
        else:
            non_locations.append(words[i])
        i += 1

    return locations, non_locations

def build_cleaned_query(tokens):
    keep = []
    for token in tokens:
        if token not in {"in", "near", "around"}:
            keep.append(token)
    return " ".join(keep).strip()

def normalize_query(query: str):
    locations, non_locations = split_query_parts(query)

    if not non_locations:
        non_locations = clean_text(query).split()

    primary_location = locations[0] if locations else ""
    
    # Core query without location
    base_search = build_cleaned_query(non_locations) or query.strip()

    maps_query = query.strip()
    
    # Combine the core search with the location for the dorks
    dork_query = f'"{base_search}" {primary_location}'.strip()

    return {
        "maps_query": maps_query,
        "indiamart_query": dork_query,
        "linkedin_query": dork_query,
        "instagram_query": dork_query,
        "location": primary_location,
        "tokens": non_locations,
    }