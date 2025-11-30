# backend/zoning_parking.py

import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def analyze_parking(lat: float, lon: float, radius_m: int = 300):
    """
    Uses OpenStreetMap (Overpass) to look for parking amenities nearby.
    Returns:
      - parking_count: number of parking features found
      - parking_score: 0–100 heuristic score
    """
    query = f"""
    [out:json];
    (
      node["amenity"="parking"](around:{radius_m},{lat},{lon});
      way["amenity"="parking"](around:{radius_m},{lat},{lon});
    );
    out center;
    """

    count = 0
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        count = len(data.get("elements", []))
    except Exception:
        # On failure, we just treat as unknown / low-parking case
        count = 0

    # Simple heuristic for score:
    if count == 0:
        score = 20   # likely street/limited parking
    elif count < 3:
        score = 60   # some parking options
    else:
        score = 85   # strong parking availability

    return {
        "parking_count": count,
        "parking_score": score,
    }


def analyze_zoning(lat: float, lon: float, radius_m: int = 200):
    """
    Very rough zoning proxy using landuse/building tags.
    Real zoning needs city parcel data; this is a directional hint only.
    Returns:
      - zoning_label: human-readable description
    """
    query = f"""
    [out:json];
    (
      way["landuse"](around:{radius_m},{lat},{lon});
      way["building"](around:{radius_m},{lat},{lon});
    );
    out tags;
    """

    zoning_label = "Unknown / Mixed Use"
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        tags_list = [el.get("tags", {}) for el in data.get("elements", [])]

        landuses = {t.get("landuse") for t in tags_list if "landuse" in t}
        buildings = {t.get("building") for t in tags_list if "building" in t}

        if "commercial" in landuses or "retail" in landuses:
            zoning_label = "Likely Commercial / Retail"
        elif "industrial" in landuses:
            zoning_label = "Likely Industrial"
        elif "residential" in landuses:
            zoning_label = "Likely Residential"
        elif buildings:
            # Show a few building types if nothing else
            short_list = ", ".join(sorted([b for b in buildings if b])[:3])
            zoning_label = f"Buildings nearby: {short_list}"
    except Exception:
        # Keep default label on error
        pass

    return {
        "zoning_label": zoning_label,
    }
