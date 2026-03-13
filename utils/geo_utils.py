import math

CITY_COORDS = {
    # --- TIER 1 (The 8 Major Metros) ---
    "mumbai": (19.0760, 72.8777),
    "delhi": (28.6139, 77.2090),
    "bangalore": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "ahmedabad": (23.0225, 72.5714),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "pune": (18.5204, 73.8567),

    # --- TIER 2 (North & West) ---
    "jaipur": (26.9124, 75.7873),
    "surat": (21.1702, 72.8311),
    "lucknow": (26.8467, 80.9462),
    "kanpur": (26.4499, 80.3319),
    "nagpur": (21.1458, 79.0882),
    "indore": (22.7196, 75.8577),
    "chandigarh": (30.7333, 76.7794),
    "ludhiana": (30.9010, 75.8573),
    "agra": (27.1767, 78.0081),
    "vadodara": (22.3072, 73.1812),
    "nashik": (19.9975, 73.7898),
    "gurgaon": (28.4595, 77.0266),
    "noida": (28.5355, 77.3910),

    # --- TIER 2 (South & East) ---
    "kochi": (9.9312, 76.2673),
    "visakhapatnam": (17.6868, 83.2185),
    "coimbatore": (11.0168, 76.9558),
    "madurai": (9.9252, 78.1198),
    "mysore": (12.2958, 76.6394),
    "thiruvananthapuram": (8.5241, 76.9366),
    "tirupur": (11.1085, 77.3411),
    "bhubaneswar": (20.2961, 85.8245),
    "patna": (25.5941, 85.1376),
    "guwahati": (26.1445, 91.7362),
    "ranchi": (23.3441, 85.3094),
    "raipur": (21.2514, 81.6296)
}


def generate_grid(city, grid_size=3, step_km=2):
    if city not in CITY_COORDS:
        return []

    lat_deg, lon_deg = CITY_COORDS[city]
    coords = []

    # Latitude step is constant: ~111km per degree
    step_lat = step_km / 111.0
    
    # Longitude step shrinks as you move away from the equator
    step_lon = step_km / (111.0 * math.cos(math.radians(lat_deg)))

    for i in range(-grid_size, grid_size + 1):
        for j in range(-grid_size, grid_size + 1):
            new_lat = lat_deg + (i * step_lat)
            new_lon = lon_deg + (j * step_lon)
            coords.append((new_lat, new_lon))

    return coords