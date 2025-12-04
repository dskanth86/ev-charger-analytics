# backend/model/arc_lm.py

"""
Advanced Regional Charger Load Model (ARC-LM).

Deterministic multi-factor utilization and session-range estimator.

Inputs are provided via a feature vector built from geographic context
and previously computed scores.
"""

from typing import Dict, Any


def build_feature_vector(lat: float, lon: float, context: Dict[str, Any]) -> Dict[str, float]:
    """Build a cleaned and normalized feature vector for ARC-LM.

    Expects `context` to contain the following keys (all 0-100 unless noted):

    - demand_score
    - traffic_score
    - ev_share_score
    - poi_score
    - competition_score
    - parking_score
    - zoning_label (string: "commercial"/"industrial"/"residential"/other)
    - charger_type ("L2" or "DCFC")
    - parking_count (absolute count, used only for light scaling)
    - region_hint (optional: "urban"/"suburban"/"rural"). If missing,
      it is inferred from demand_score and traffic_score.
    """

    demand_score = float(context.get("demand_score", 50.0))
    traffic_score = float(context.get("traffic_score", 50.0))
    ev_share_score = float(context.get("ev_share_score", 50.0))
    poi_score = float(context.get("poi_score", 50.0))
    competition_score = float(context.get("competition_score", 50.0))
    parking_score = float(context.get("parking_score", 50.0))

    zoning_label = str(context.get("zoning_label", "other")).lower()
    charger_type = str(context.get("charger_type", "L2")).upper()
    parking_count = float(context.get("parking_count", 0.0))

    # Normalize core scores to 0-1
    demand = max(0.0, min(1.0, demand_score / 100.0))
    traffic = max(0.0, min(1.0, traffic_score / 100.0))
    ev_share = max(0.0, min(1.0, ev_share_score / 100.0))
    poi = max(0.0, min(1.0, poi_score / 100.0))

    # Higher competition_score means more nearby chargers and therefore *lower* opportunity.
    # Convert to a saturation index where 1.0 = strongly saturated (bad), 0.0 = no competitors.
    competition_sat = max(0.0, min(1.0, competition_score / 100.0))

    parking = max(0.0, min(1.0, parking_score / 100.0))

    # Zoning encoding
    if "comm" in zoning_label:
        zoning_type = "commercial"
    elif "ind" in zoning_label:
        zoning_type = "industrial"
    elif "res" in zoning_label:
        zoning_type = "residential"
    else:
        zoning_type = "other"

    # Region inference if not explicitly provided
    region_hint = str(context.get("region_hint", "")).lower()
    if region_hint not in {"urban", "suburban", "rural"}:
        # Simple heuristic: high demand + traffic ⇒ urban,
        # moderate ⇒ suburban, otherwise rural.
        combined = (demand_score + traffic_score) / 2.0
        if combined >= 70:
            region = "urban"
        elif combined >= 45:
            region = "suburban"
        else:
            region = "rural"
    else:
        region = region_hint

    # Fleet vs household split derived from EV share and zoning.
    # Industrial zones lean more to fleet use; residential to household.
    base_fleet_share = 0.3 + 0.4 * ev_share  # 0.3–0.7
    if zoning_type == "industrial":
        fleet_share = min(0.9, base_fleet_share + 0.2)
    elif zoning_type == "residential":
        fleet_share = max(0.1, base_fleet_share - 0.15)
    else:
        fleet_share = base_fleet_share
    household_share = 1.0 - fleet_share

    # Charger-type sensitivity and dwell-time are strongly correlated.
    # DCFC has short dwell time but higher turnover; L2 has long dwell time
    # and lower turnover per plug.
    if charger_type == "DCFC":
        charger_sensitivity = 1.2  # more sensitive to traffic & POIs
        dwell_time_factor = 0.7    # short dwell, more sessions per kW
    else:
        charger_sensitivity = 1.0
        dwell_time_factor = 1.0

    # Regional multiplier capturing macro siting differences.
    if region == "urban":
        regional_multiplier = 1.15
    elif region == "suburban":
        regional_multiplier = 1.0
    else:  # rural
        regional_multiplier = 0.8

    # Light normalization of parking capacity (saturate at ~50 spaces).
    parking_capacity_factor = max(0.5, min(1.3, 0.5 + min(parking_count, 50.0) / 100.0))

    return {
        "lat": float(lat),
        "lon": float(lon),
        "demand": demand,
        "traffic": traffic,
        "ev_share": ev_share,
        "poi": poi,
        "competition_sat": competition_sat,
        "parking": parking,
        "parking_capacity_factor": parking_capacity_factor,
        "zoning_type": zoning_type,
        "region": region,
        "fleet_share": fleet_share,
        "household_share": household_share,
        "charger_type": charger_type,
        "charger_sensitivity": charger_sensitivity,
        "dwell_time_factor": dwell_time_factor,
        "regional_multiplier": regional_multiplier,
    }


def arc_lm_predict(features: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic ARC-LM utilization and sessions estimate.

    Returns a dict containing at minimum:

    - utilization_index (0-100)
    - sessions_low (int)
    - sessions_high (int)

    and additional keys describing the factor-level contribution breakdown
    and percentage influence useful for reporting.
    """

    demand = float(features["demand"])
    traffic = float(features["traffic"])
    ev_share = float(features["ev_share"])
    poi = float(features["poi"])
    competition_sat = float(features["competition_sat"])
    parking = float(features["parking"])
    parking_capacity_factor = float(features["parking_capacity_factor"])
    zoning_type = str(features["zoning_type"])
    region = str(features["region"])
    fleet_share = float(features["fleet_share"])
    household_share = float(features["household_share"])
    charger_type = str(features["charger_type"])
    charger_sensitivity = float(features["charger_sensitivity"])
    dwell_time_factor = float(features["dwell_time_factor"])
    regional_multiplier = float(features["regional_multiplier"])

    # Core factor weights (sum to 1.0 before secondary multipliers).
    # These represent how much each primary dimension drives utilization.
    w_base_demand = 0.25
    w_traffic = 0.15
    w_poi = 0.15
    w_ev_fleet = 0.10
    w_competition = 0.12
    w_parking = 0.10
    w_zoning = 0.05
    w_region = 0.08

    # Base demand component from long-term structural demand.
    base_demand_component = w_base_demand * demand

    # Traffic elasticity component. DCFC is more sensitive to traffic & dwell
    # is captured later via dwell_time_factor.
    traffic_component = w_traffic * traffic * charger_sensitivity

    # POI attraction component, reflecting trip generation strength.
    poi_component = w_poi * poi * charger_sensitivity

    # Fleet vs household adoption. We assume fleets generate more predictable
    # and higher utilization than households.
    fleet_component = w_ev_fleet * (0.5 * household_share + 1.0 * fleet_share) * ev_share

    # Competition load: higher saturation reduces utilization. We invert
    # the saturation here (1 - competition_sat).
    competition_component = w_competition * (1.0 - competition_sat)

    # Parking availability, amplified by absolute capacity.
    parking_component = w_parking * parking * parking_capacity_factor

    # Zoning factor: commercial is best for public charging, then mixed/other,
    # then industrial, with residential in between.
    if zoning_type == "commercial":
        zoning_score = 1.0
    elif zoning_type == "residential":
        zoning_score = 0.8
    elif zoning_type == "industrial":
        zoning_score = 0.7
    else:
        zoning_score = 0.85
    zoning_component = w_zoning * zoning_score

    # Regional multiplier converted into a normalized regional score.
    # We map the 0.8–1.15 multiplier band roughly to a 0.6–1.0 score range.
    if region == "urban":
        regional_score = 1.0
    elif region == "suburban":
        regional_score = 0.85
    else:  # rural
        regional_score = 0.65
    region_component = w_region * regional_score

    # Aggregate raw utilization score in 0–1 range (before global multipliers).
    raw_utilization_score = (
        base_demand_component
        + traffic_component
        + poi_component
        + fleet_component
        + competition_component
        + parking_component
        + zoning_component
        + region_component
    )

    # Global multipliers capturing charger-specific throughput and dwell time.
    # Higher dwell_time_factor slightly reduces effective utilization, while
    # regional_multiplier scales everything based on macro siting quality.
    global_multiplier = regional_multiplier * (0.9 + 0.2 * (1.0 - dwell_time_factor))

    effective_utilization = max(0.0, min(1.0, raw_utilization_score * global_multiplier))
    utilization_index = effective_utilization * 100.0

    # Map utilization index to an L2-equivalent session band.
    if utilization_index < 20:
        base_low, base_high = 1, 3
    elif utilization_index < 40:
        base_low, base_high = 3, 6
    elif utilization_index < 60:
        base_low, base_high = 6, 10
    elif utilization_index < 80:
        base_low, base_high = 10, 16
    else:
        base_low, base_high = 16, 24

    # Charger-type sensitivity: DCFC has higher turnover, so we apply a
    # deterministic uplift relative to L2.
    if charger_type == "DCFC":
        sessions_low = int(round(base_low * 1.8))
        sessions_high = int(round(base_high * 1.8))
    else:
        sessions_low = base_low
        sessions_high = base_high

    # Factor percentage influence relative to the *raw* utilization score.
    # This keeps the breakdown interpretable (sum to ~100%).
    components = {
        "Base Demand": base_demand_component,
        "Traffic Elasticity": traffic_component,
        "POI Attraction": poi_component,
        "Fleet EV Factor": fleet_component,
        "Competitor Load": competition_component,
        "Parking Availability": parking_component,
        "Zoning": zoning_component,
        "Regional Multiplier": region_component,
    }

    total_components = sum(components.values()) or 1e-6
    factor_percentages = {
        name: (value / total_components) * 100.0 for name, value in components.items()
    }

    return {
        "utilization_index": utilization_index,
        "sessions_low": sessions_low,
        "sessions_high": sessions_high,
        "raw_utilization_score": raw_utilization_score,
        "effective_utilization": effective_utilization,
        "components": components,
        "factor_percentages": factor_percentages,
    }
