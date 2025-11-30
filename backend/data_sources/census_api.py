# backend/data_sources/census_api.py

import requests

CENSUS_GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
ACS_API_URL = "https://api.census.gov/data/2022/acs/acs5"


def latlon_to_geoid(lat: float, lon: float):
    """
    Convert (lat, lon) to Census GEOID parts using the Census geocoder.
    Tries Tract first, then Block Group.
    """
    params = {
        "x": lon,
        "y": lat,
        "benchmark": "Public_AR_Current",
        "vintage": "Current_Current",
        "format": "json",
    }

    resp = requests.get(CENSUS_GEOCODER_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    geos = data.get("result", {}).get("geographies", {})

    # ✅ Preferred: Census Tracts
    if "Census Tracts" in geos and len(geos["Census Tracts"]) > 0:
        geo = geos["Census Tracts"][0]
        return {
            "state": geo["STATE"],
            "county": geo["COUNTY"],
            "tract": geo["TRACT"],
        }

    # ✅ Fallback: Census Block Groups
    if "Census Block Groups" in geos and len(geos["Census Block Groups"]) > 0:
        geo = geos["Census Block Groups"][0]
        return {
            "state": geo["STATE"],
            "county": geo["COUNTY"],
            "tract": geo["TRACT"],
        }

    return None


def fetch_population_income(lat: float, lon: float):
    """
    Returns (population, median_income) using ACS 5-year data at the tract level.

    population    -> B01003_001E
    median_income -> B19013_001E
    """
    geoids = latlon_to_geoid(lat, lon)
    if not geoids:
        return None, None

    state = geoids["state"]
    county = geoids["county"]
    tract = geoids["tract"]

    params = {
        "get": "B01003_001E,B19013_001E",
        "for": f"tract:{tract}",
        "in": f"state:{state} county:{county}",
    }

    resp = requests.get(ACS_API_URL, params=params, timeout=30)
    resp.raise_for_status()
    json_data = resp.json()

    if len(json_data) < 2:
        return None, None

    row = json_data[1]

    try:
        population = int(row[0])
    except Exception:
        population = None

    try:
        median_income = int(row[1])
    except Exception:
        median_income = None

    return population, median_income
