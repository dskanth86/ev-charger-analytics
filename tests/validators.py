"""Validation and anomaly detection for EV-Charger Analytics tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Anomaly:
    zip_code: str
    metric: str
    value: Any
    message: str


# Realistic ranges (very approximate, can be tuned over time)
RANGES = {
    "demand_score": (0, 100),
    "traffic_score": (0, 100),
    "ev_share_score": (0, 100),
    "poi_score": (0, 100),
    "competition_score": (0, 100),
    "parking_score": (0, 100),
    "utilization_index": (0, 100),
    "sessions_low": (0, 200),
    "sessions_high": (0, 400),
    "avg_sessions_per_day": (0, 400),
    "monthly_profit": (-1e5, 1e6),
    "payback_years": (0, 40),
}


def _check_range(name: str, value: Any, zip_code: str, anomalies: List[Anomaly]) -> None:
    if value is None:
        return
    if name not in RANGES:
        return
    lo, hi = RANGES[name]
    try:
        v = float(value)
    except Exception:
        anomalies.append(Anomaly(zip_code, name, value, "non-numeric value"))
        return
    if not (lo <= v <= hi):
        anomalies.append(
            Anomaly(
                zip_code,
                name,
                value,
                f"out of expected range [{lo}, {hi}]",
            )
        )


def validate_pipeline_output(zip_sample, output_dict: Dict[str, Any]) -> List[Anomaly]:
    anomalies: List[Anomaly] = []
    z = zip_sample.zip_code

    for metric in [
        "demand_score",
        "traffic_score",
        "ev_share_score",
        "poi_score",
        "competition_score",
        "parking_score",
        "utilization_index",
        "sessions_low",
        "sessions_high",
        "avg_sessions_per_day",
        "monthly_profit",
        "payback_years",
    ]:
        _check_range(metric, output_dict.get(metric), z, anomalies)

    # Additional consistency checks
    low = output_dict.get("sessions_low")
    high = output_dict.get("sessions_high")
    if low is not None and high is not None and low > high:
        anomalies.append(
            Anomaly(z, "sessions_range", (low, high), "sessions_low > sessions_high"),
        )

    return anomalies
