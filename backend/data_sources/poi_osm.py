"""backend/data_sources/poi_osm.py

POI-based demand layer using OpenStreetMap Overpass API.

Provides get_poi_score(lat, lon) which returns a normalized 0–100 score
based on nearby retail / workplace / services density.
"""

import math
import time
from typing import Dict

import requests


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Default search radius in meters (≈ 0.8 km)
_DEFAULT_RADIUS_M = 800.0


def _build_overpass_query(lat: float, lon: float, radius_m: float) -> str:
    """Builds an Overpass QL query for key POI categories around a point."""
    amenities = ["restaurant", "cafe", "fast_food", "bar", "parking", "hospital", "school", "university", "library", "bank", "cinema", "theatre", "place_of_worship", "clinic"]
    shops = ["supermarket", "mall", "department_store", "convenience", "retail"]
    offices = ["office"]
    leisure = ["fitness_centre", "sports_centre", "gym"]
    tourism = ["hotel"]

    def _or_values(key: str, values) -> str:
        parts = []
        for v in values:
            parts.append(f'node["{key}"="{v}"](around:{radius_m},{lat},{lon});')
        return "".join(parts)

    query = (
        "[out:json][timeout:25];("
        + _or_values("amenity", amenities)
        + _or_values("shop", shops)
        + _or_values("office", offices)
        + _or_values("leisure", leisure)
        + _or_values("tourism", tourism)
        + ");out body;"
    )
    return query


def _density_to_score(density_per_km2: float) -> float:
    """Map POI density to a 0–100 score with gentle saturation.

    The mapping is heuristic:
    - 0 density      ->  5
    - 20 / km²       -> 40
    - 50 / km²       -> 70
    - 100+ / km²     -> 95–100 (capped)
    """
    if density_per_km2 <= 0:
        return 5.0

    # Piecewise-linear segments with cap
    if density_per_km2 < 20:
        score = 5.0 + (density_per_km2 / 20.0) * (40.0 - 5.0)
    elif density_per_km2 < 50:
        score = 40.0 + ((density_per_km2 - 20.0) / 30.0) * (70.0 - 40.0)
    elif density_per_km2 < 100:
        score = 70.0 + ((density_per_km2 - 50.0) / 50.0) * (95.0 - 70.0)
    else:
        score = 100.0

    return max(0.0, min(100.0, score))


def get_poi_score(lat: float, lon: float, radius_m: float = _DEFAULT_RADIUS_M) -> Dict[str, float]:
    """Fetch POIs near a point and compute a normalized POI score.

    Args:
        lat: Latitude of the site.
        lon: Longitude of the site.
        radius_m: Search radius in meters (kept modest for rate limits).

    Returns:
        dict with keys:
            - poi_count: total number of POIs found
            - poi_density: POIs per square kilometer
            - poi_score: normalized 0–100 score

    Notes:
        - Uses Overpass API with a conservative timeout and small radius
          to respect usage limits.
        - On any network/API failure, falls back to a neutral mid-range
          score so the rest of the pipeline continues to work.
    """
    # Fallback neutral values in case of any failure
    fallback = {"poi_count": 0, "poi_density": 0.0, "poi_score": 50.0}

    try:
        query = _build_overpass_query(lat, lon, radius_m)

        headers = {"User-Agent": "ev-charger-analytics-poi/1.0"}
        # Tiny pause to be polite when called repeatedly
        time.sleep(0.2)
        resp = requests.post(OVERPASS_URL, data=query, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        elements = data.get("elements", [])
        poi_count = len(elements)

        # Compute density per km² based on circular search area
        radius_km = radius_m / 1000.0
        area_km2 = math.pi * (radius_km ** 2)
        if area_km2 <= 0:
            return fallback

        poi_density = poi_count / area_km2
        poi_score = _density_to_score(poi_density)

        return {
            "poi_count": poi_count,
            "poi_density": round(poi_density, 2),
            "poi_score": round(poi_score, 1),
        }

    except Exception:
        # Fail quietly and keep pipeline robust
        return fallback
