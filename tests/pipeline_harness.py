"""Black-box pipeline harness for EV-Charger Analytics tests.

This module orchestrates the full analytics stack for a synthetic
address derived from a ZIP sample, using only production logic imported
from the backend package. No production modules are modified.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict
import importlib
import sys
from pathlib import Path


# Ensure the backend directory is on sys.path so that imports like
# `from data_sources...` and `from scoring...` inside main.py work the
# same way they do when running `python backend/main.py`.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_DIR = _PROJECT_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# Now we can import the same modules main.py uses as top-level modules.
main_mod = importlib.import_module("main")
traffic_mod = importlib.import_module("data_sources.traffic_aadt")
flood_mod = importlib.import_module("data_sources.flood_fema")
poi_mod = importlib.import_module("data_sources.poi_osm")
ev_mod = importlib.import_module("data_sources.ev_adoption")
zoning_mod = importlib.import_module("zoning_parking")
demand_mod = importlib.import_module("scoring.demand")
competition_mod = importlib.import_module("scoring.competition")
arc_mod = importlib.import_module("model.arc_lm")
roi_mod = importlib.import_module("roi.roi")


@dataclass
class PipelineInputs:
    address: str
    charger_type: str = "L2"
    price_per_kwh: float = 0.35
    electricity_cost: float = 0.15
    kwh_per_session: float = 35.0
    install_cost: float = 75000.0


@dataclass
class PipelineOutputs:
    # Geospatial & risk
    lat: float
    lon: float
    flood: Dict[str, Any]
    # Scores
    demand_score: float
    traffic_score: float
    ev_share_score: float
    poi_score: float
    competition_score: float
    parking_score: float
    parking_count: int
    zoning_label: str
    # ARC-LM
    arc_features: Dict[str, Any]
    arc_result: Dict[str, Any]
    utilization_index: float
    sessions_low: int
    sessions_high: int
    # ROI
    roi_results: Dict[str, Any]
    forecast_5yr: Any

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Flatten a few convenience fields
        d["avg_sessions_per_day"] = self.roi_results.get("avg_sessions_per_day")
        return d


def _address_from_zip(zip_code: str, state: str, city: str | None = None) -> str:
    """Construct a generic street address string for a ZIP.

    This keeps tests deterministic and avoids the need for a full
    geocoded address list while still exercising the geocoder.
    """

    # Use a simple pattern that still looks realistic enough for
    # geocoding services. If a city is known for this ZIP, include it.
    if city:
        return f"123 Main St, {city}, {state} {zip_code}, USA"
    return f"123 Main St, {state} {zip_code}, USA"


def run_pipeline_for_zip(zip_sample, *, inputs: PipelineInputs | None = None) -> PipelineOutputs:
    """Run the full analytics pipeline for a single ZIP sample.

    All computation is delegated to production modules; this function
    only wires them together and captures intermediate outputs.
    """

    if inputs is None:
        address = _address_from_zip(zip_sample.zip_code, zip_sample.state, getattr(zip_sample, "city", None))
        inputs = PipelineInputs(address=address)
    else:
        address = inputs.address

    # GEO
    geocode_address = main_mod.geocode_address
    fetch_nearby_chargers = main_mod.fetch_nearby_chargers

    lat, lon = geocode_address(address)

    # Traffic & EV adoption
    traffic_score = traffic_mod.get_traffic_score(lat, lon)
    ev_share_score = ev_mod.get_ev_share_score(lat, lon)

    # Flood risk
    flood = flood_mod.get_flood_risk(lat, lon)

    # Demand
    demand_score = demand_mod.estimate_demand_score(lat, lon)

    # Competition
    chargers = fetch_nearby_chargers(lat, lon)
    competition_score = competition_mod.compute_competition_score(len(chargers))

    # POI
    poi_result = poi_mod.get_poi_score(lat, lon)
    poi_score = poi_result.get("poi_score", 50.0)

    # Parking & zoning
    parking_info = zoning_mod.analyze_parking(lat, lon)
    zoning_info = zoning_mod.analyze_zoning(lat, lon)

    # ARC-LM
    arc_context = {
        "demand_score": demand_score,
        "traffic_score": traffic_score,
        "ev_share_score": ev_share_score,
        "poi_score": poi_score,
        "competition_score": competition_score,
        "parking_score": parking_info["parking_score"],
        "parking_count": parking_info["parking_count"],
        "zoning_label": zoning_info["zoning_label"],
        "charger_type": inputs.charger_type,
    }
    features = arc_mod.build_feature_vector(lat, lon, arc_context)
    arc_result = arc_mod.arc_lm_predict(features)

    utilization = float(arc_result["utilization_index"])
    sessions_low = int(arc_result["sessions_low"])
    sessions_high = int(arc_result["sessions_high"])

    # ROI
    roi_results = roi_mod.roi_model(
        sessions_low,
        sessions_high,
        price_per_kwh=inputs.price_per_kwh,
        electricity_cost=inputs.electricity_cost,
        kwh_per_session=inputs.kwh_per_session,
        install_cost=inputs.install_cost,
    )
    forecast_5yr = roi_mod.forecast_roi_5yr(
        base_daily_sessions=roi_results["avg_sessions_per_day"],
        price_per_kwh=inputs.price_per_kwh,
        electricity_cost=inputs.electricity_cost,
        kwh_per_session=inputs.kwh_per_session,
        install_cost=inputs.install_cost,
    )

    return PipelineOutputs(
        lat=lat,
        lon=lon,
        flood=flood,
        demand_score=demand_score,
        traffic_score=traffic_score,
        ev_share_score=ev_share_score,
        poi_score=poi_score,
        competition_score=competition_score,
        parking_score=parking_info["parking_score"],
        parking_count=parking_info["parking_count"],
        zoning_label=zoning_info["zoning_label"],
        arc_features=features,
        arc_result=arc_result,
        utilization_index=utilization,
        sessions_low=sessions_low,
        sessions_high=sessions_high,
        roi_results=roi_results,
        forecast_5yr=forecast_5yr,
    )
