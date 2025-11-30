# backend/reports/pdf_report.py

import os
from pathlib import Path
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas


def generate_pdf_report(output_dir: str, context: dict) -> str:
    """
    Generates a one-page investor-ready PDF feasibility report
    including flood risk and 5-year income forecast.
    """

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = os.path.join(output_dir, "ev_site_report.pdf")

    c = canvas.Canvas(output_path, pagesize=LETTER)
    width, height = LETTER

    text = c.beginText(40, height - 50)

    # ---- HEADER ----
    text.setFont("Helvetica-Bold", 16)
    text.textLine("EV Charger Site Feasibility Report")
    text.moveCursor(0, 20)

    # ---- BASIC INFO ----
    text.setFont("Helvetica", 11)
    text.textLine(f"Address: {context['address']}")
    text.textLine(f"Coordinates: {context['lat']:.5f}, {context['lon']:.5f}")
    text.moveCursor(0, 12)

    # ---- SITE METRICS ----
    text.setFont("Helvetica-Bold", 12)
    text.textLine("Site Metrics")
    text.setFont("Helvetica", 11)

    text.textLine(f"Demand Score: {context['demand_score']}/100")
    text.textLine(f"Competition Score: {context['competition_score']}/100")
    text.textLine(
        f"Estimated Sessions/Day: {context['sessions_low']} – {context['sessions_high']}"
    )
    text.moveCursor(0, 12)

    # ---- CHARGER CONFIG ----
    text.setFont("Helvetica-Bold", 12)
    text.textLine("Charger Configuration")
    text.setFont("Helvetica", 11)

    text.textLine(f"Charger Type: {context['charger_type']}")
    text.textLine(f"Price per kWh: ${context['price_per_kwh']:.2f}")
    text.textLine(f"Electricity Cost per kWh: ${context['electricity_cost']:.2f}")
    text.textLine(f"kWh per Session: {context['kwh_per_session']}")
    text.textLine(f"Install Cost: ${context['install_cost']:,.0f}")
    text.moveCursor(0, 12)

    # ---- BASE FINANCIALS ----
    text.setFont("Helvetica-Bold", 12)
    text.textLine("Financial Performance (Base Year)")
    text.setFont("Helvetica", 11)

    text.textLine(f"Avg Sessions/Day: {context['avg_sessions_per_day']:.1f}")
    text.textLine(f"Monthly Profit: ${context['monthly_profit']:,.2f}")
    text.textLine(f"Payback Period: {context['payback_years']:.2f} years")
    text.moveCursor(0, 12)

    # ---- FLOOD RISK (FEMA) ----
    flood = context.get("flood", {})

    text.setFont("Helvetica-Bold", 12)
    text.textLine("Flood Risk Assessment (FEMA)")
    text.setFont("Helvetica", 11)

    zone = flood.get("zone", "N/A")
    in_100yr = flood.get("in_100yr", False)
    insurance_required = flood.get("insurance_required", False)
    bfe = flood.get("bfe", None)
    source = flood.get("source", "FEMA")

    text.textLine(f"FEMA Flood Zone: {zone}")
    text.textLine(f"100-Year Floodplain: {'Yes' if in_100yr else 'No'}")
    text.textLine(
        f"Flood Insurance Required: {'Yes' if insurance_required else 'No'}"
    )
    text.textLine(
        f"Base Flood Elevation (BFE): {bfe if bfe is not None else 'Not Applicable'}"
    )
    text.textLine(f"Data Source: {source}")
    text.moveCursor(0, 12)

    # ---- ✅ 5-YEAR INCOME FORECAST ----
    forecast = context.get("forecast_5yr", [])

    if forecast:
        text.setFont("Helvetica-Bold", 12)
        text.textLine("5-Year Income Forecast")
        text.setFont("Helvetica", 11)

        for row in forecast:
            roi_pct = row.get("cumulative_roi")
            if isinstance(roi_pct, (int, float)):
                roi_str = f"{roi_pct * 100:.1f}%"
            else:
                roi_str = "N/A"

            text.textLine(
                f"Year {row['year']}: "
                f"Annual Profit ${row['annual_profit']:,.0f}, "
                f"Cumulative ${row['cumulative_profit']:,.0f}, "
                f"ROI {roi_str}"
            )

        text.moveCursor(0, 12)

    # ---- FINAL VERDICT ----
    text.setFont("Helvetica-Bold", 13)
    text.textLine(f"Final Verdict: {context['verdict']}")

    c.drawText(text)
    c.showPage()
    c.save()

    return output_path
