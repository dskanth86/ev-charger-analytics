"""Test reporting utilities for EV-Charger Analytics.

Produces:
- EV_Analytics_Test_Results.pdf
- anomalies.csv
- benchmark_stats.json
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from .stats_analysis import compute_benchmark_stats, correlation_summary


def write_anomalies_csv(path: Path, anomalies: Iterable[Dict[str, Any]]) -> None:
    rows = list(anomalies)
    if not rows:
        # Still create an empty file with header for convenience.
        fieldnames = ["zip_code", "metric", "value", "message"]
    else:
        fieldnames = sorted(rows[0].keys())

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_benchmark_stats_json(path: Path, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    stats = compute_benchmark_stats(records)
    stats["correlations"] = correlation_summary(records)
    with path.open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, default=str)
    return stats


def generate_results_pdf(path: Path, records: List[Dict[str, Any]], stats: Dict[str, Any]) -> None:
    """Generate a lightweight multi-section PDF summarizing test results."""

    Path(path.parent).mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=LETTER)
    width, height = LETTER

    # Page 1 - Summary
    text = c.beginText(40, height - 60)
    text.setFont("Helvetica-Bold", 16)
    text.textLine("EV Analytics Test Results")
    text.moveCursor(0, 20)

    text.setFont("Helvetica", 11)
    text.textLine(f"Total test cases: {len(records)}")

    demand_stats = stats["metrics"].get("demand_score", {})
    util_stats = stats["metrics"].get("utilization_index", {})
    sessions_stats = stats["metrics"].get("avg_sessions_per_day", {})

    text.moveCursor(0, 16)
    text.textLine("Key Metrics (mean / stdev):")
    if demand_stats:
        text.textLine(
            f"  Demand Score: {demand_stats.get('mean', 0):.1f} +/- {demand_stats.get('stdev', 0):.1f}"
        )
    if util_stats:
        text.textLine(
            f"  Utilization Index: {util_stats.get('mean', 0):.1f} +/- {util_stats.get('stdev', 0):.1f}"
        )
    if sessions_stats:
        text.textLine(
            "  Avg Sessions/Day: "
            f"{sessions_stats.get('mean', 0):.1f} +/- {sessions_stats.get('stdev', 0):.1f}"
        )

    corr = stats.get("correlations", {})
    if corr:
        text.moveCursor(0, 16)
        text.textLine("Selected correlations:")
        for name, val in corr.items():
            text.textLine(f"  {name}: {val:.3f}" if val is not None else f"  {name}: N/A")

    c.drawText(text)
    c.showPage()

    # Additional pages (heatmaps/plots) could be added here; for now we
    # keep the PDF lightweight and text-based to avoid extra heavyweight
    # plotting dependencies.

    c.save()
