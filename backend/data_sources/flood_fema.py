import requests

FEMA_ARCGIS_URL = (
    "https://hazards.fema.gov/arcgis/rest/services"
    "/NFHL/MapServer/28/query"
)

def get_flood_risk(lat: float, lon: float):
    params = {
        "f": "json",
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "FLD_ZONE,ZONE_SUBTY,BFE,STATIC_BFE",
        "returnGeometry": "false",
    }

    try:
        r = requests.get(FEMA_ARCGIS_URL, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return {
            "zone": None,
            "in_100yr": None,
            "in_500yr": None,
            "bfe": None,
            "insurance_required": None,
            "source": "FEMA ArcGIS (unavailable)",
            "error": str(e),
        }

    features = data.get("features", [])

    # ✅ If no polygon hit → Zone X (minimal risk)
    if not features:
        return {
            "zone": "X",
            "in_100yr": False,
            "in_500yr": False,
            "bfe": None,
            "insurance_required": False,
            "source": "FEMA ArcGIS",
        }

    attrs = features[0].get("attributes", {})
    zone = attrs.get("FLD_ZONE")
    bfe = attrs.get("BFE") or attrs.get("STATIC_BFE")

    in_100yr = zone in ("A", "AE", "AO", "AH", "AR", "A1", "A99", "VE", "V")
    in_500yr = zone in ("X500",)

    return {
        "zone": zone,
        "in_100yr": in_100yr,
        "in_500yr": in_500yr,
        "bfe": bfe,
        "insurance_required": in_100yr,
        "source": "FEMA ArcGIS",
    }
