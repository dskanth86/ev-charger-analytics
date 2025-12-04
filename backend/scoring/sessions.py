"""
Session estimation module for EV charger analytics.

This module now delegates to the ARC-LM deterministic model as the
single source of truth for utilization and session ranges.
"""

from typing import Tuple

from model.arc_lm import build_feature_vector, arc_lm_predict

def estimate_sessions_range(
    demand_score: float,
    competition_score: float,
    parking_score: float,
    charger_type: str,
    traffic_score: float = 50.0,
    ev_share_score: float = 50.0,
    poi_score: float = 50.0,
    *,
    zoning_label: str = "",
    parking_count: int = 0,
    region_hint: str = "",
) -> Tuple[int, int, float]:
    """Estimate the range of charging sessions per day via ARC-LM.

    This function preserves the original public API while forwarding the
    computation to the ARC-LM model, which is now the single source of
    truth for utilization and sessions.
    """

    context = {
        "demand_score": demand_score,
        "traffic_score": traffic_score,
        "ev_share_score": ev_share_score,
        "poi_score": poi_score,
        "competition_score": competition_score,
        "parking_score": parking_score,
        "zoning_label": zoning_label,
        "parking_count": parking_count,
        "charger_type": charger_type,
        "region_hint": region_hint,
    }

    # Lat/lon are not part of the legacy API, but ARC-LM only uses them
    # as identifiers, so we safely pass zeros here.
    features = build_feature_vector(0.0, 0.0, context)
    result = arc_lm_predict(features)

    return (
        int(result["sessions_low"]),
        int(result["sessions_high"]),
        float(result["utilization_index"]),
    )
