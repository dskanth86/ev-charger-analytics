"""Statistical analysis utilities for EV-Charger Analytics tests."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean, pstdev
from typing import Any, Dict, Iterable, List, Tuple


def _basic_stats(values: Iterable[float]) -> Dict[str, float]:
    vals = [v for v in values if v is not None]
    if not vals:
        return {"count": 0}
    return {
        "count": len(vals),
        "mean": mean(vals),
        "stdev": pstdev(vals) if len(vals) > 1 else 0.0,
        "min": min(vals),
        "max": max(vals),
    }


def compute_benchmark_stats(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute aggregate statistics over pipeline outputs.

    Returns a JSON-serializable dict suitable for benchmark_stats.json.
    """

    metrics = [
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
    ]

    stats: Dict[str, Any] = {"metrics": {}, "counts_by_region": {}, "counts_by_ev_band": {}}

    for m in metrics:
        stats["metrics"][m] = _basic_stats(
            float(r[m]) for r in records if r.get(m) is not None
        )

    # Simple counts by categorical bands if present on zip_sample-derived fields
    region_counts = defaultdict(int)
    ev_band_counts = defaultdict(int)
    for r in records:
        region = r.get("region_type")
        ev_band = r.get("ev_share_band")
        if region:
            region_counts[region] += 1
        if ev_band:
            ev_band_counts[ev_band] += 1

    stats["counts_by_region"] = dict(region_counts)
    stats["counts_by_ev_band"] = dict(ev_band_counts)

    return stats


def compute_correlation(x: List[float], y: List[float]) -> float | None:
    """Compute a simple Pearson correlation coefficient.

    Returns None if correlation is undefined (e.g. fewer than 2 points).
    """

    if len(x) != len(y) or len(x) < 2:
        return None
    mx = mean(x)
    my = mean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den_x = sum((a - mx) ** 2 for a in x)
    den_y = sum((b - my) ** 2 for b in y)
    if den_x == 0 or den_y == 0:
        return None
    return num / (den_x ** 0.5 * den_y ** 0.5)


def correlation_summary(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute a few key correlations for diagnostics."""

    out: Dict[str, Any] = {}
    def series(name: str) -> List[float]:
        return [float(r[name]) for r in records if r.get(name) is not None]

    # Align by index for simplicity
    n = min(len(records), 5000)  # cap
    sub = records[:n]

    def aligned(name: str) -> List[float]:
        return [float(r.get(name, 0.0)) for r in sub]

    pairs: List[Tuple[str, str]] = [
        ("demand_score", "sessions_high"),
        ("traffic_score", "sessions_high"),
        ("ev_share_score", "sessions_high"),
        ("poi_score", "sessions_high"),
        ("utilization_index", "avg_sessions_per_day"),
    ]

    for a, b in pairs:
        ca = aligned(a)
        cb = aligned(b)
        out[f"corr_{a}_vs_{b}"] = compute_correlation(ca, cb)

    return out
