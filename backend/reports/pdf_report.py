import os
from pathlib import Path
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas


def draw_gauge(c, x, y, score, label):
    """
    Draws a horizontal gauge bar (0–100%) with a label.
    """
    bar_width = 200
    bar_height = 12

    # Background
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.rect(x, y, bar_width, bar_height, fill=True, stroke=False)

    # Foreground proportional fill
    pct = max(0, min(100, score)) / 100
    c.setFillColorRGB(0.2, 0.6, 1.0)  # blue fill
    c.rect(x, y, bar_width * pct, bar_height, fill=True, stroke=False)

    # Border
    c.setStrokeColorRGB(0, 0, 0)
    c.rect(x, y, bar_width, bar_height, fill=False, stroke=True)

    # Label text
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 10)
    c.drawString(x + bar_width + 10, y + 1, f"{label}: {score}/100")


def generate_pdf_report(output_dir: str, context: dict) -> str:
    """
    Generates a one-page investor-ready PDF feasibility report.
    """

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = os.path.join(output_dir, "ev_site_report.pdf")

    c = canvas.Canvas(output_path, pagesize=LETTER)
    width, height = LETTER

    text = c.beginText(40, height - 230)

    # ---------------- HEADER ----------------
    text.setFont("Helvetica-Bold", 16)
    text.textLine("EV Charger Site Feasibility Report")
    text.moveCursor(0, 20)

    # ---------------- BASIC INFO ----------------
    text.setFont("Helvetica", 11)
    text.textLine(f"Address: {context['address']}")
    text.textLine(f"Coordinates: {context['lat']:.5f}, {context['lon']:.5f}")
    text.moveCursor(0, 12)

    # ---- SCORE GAUGES ----
    draw_gauge(c, 40, height - 110, context["traffic_score"], "Traffic")
    draw_gauge(c, 40, height - 130, context["ev_share_score"], "EV Adoption")
    draw_gauge(c, 40, height - 150, context["demand_score"], "Demand")
    draw_gauge(c, 40, height - 170, context["parking_score"], "Parking")
    draw_gauge(c, 40, height - 190, context["poi_score"], "POI Density")

    # ---------------- FLOOD RISK ----------------
    flood = context.get("flood", {})
    text.setFont("Helvetica-Bold", 12)
    text.textLine("Flood Risk (FEMA)")
    text.setFont("Helvetica", 11)
    text.textLine(f"Zone: {flood.get('zone', 'N/A')}")
    text.textLine(f"100-Year Floodplain: {flood.get('in_100yr', 'N/A')}")
    text.textLine(f"Insurance Required: {flood.get('insurance_required', 'N/A')}")
    text.moveCursor(0, 12)

    # ---------------- SITE METRICS ----------------
    text.setFont("Helvetica-Bold", 12)
    text.textLine("Live Demand Signals")
    text.setFont("Helvetica", 11)
    text.textLine(f"Demand Score: {context['demand_score']}/100")
    text.textLine(f"Traffic Score: {context.get('traffic_score', 'N/A')}/100")
    text.textLine(f"EV Adoption Score: {context.get('ev_share_score', 'N/A')}/100")
    text.textLine(f"Utilization Index: {context.get('util_index', 'N/A')}")
    text.textLine(f"Competition Score: {context['competition_score']}/100")
    text.textLine(f"Parking Score: {context['parking_score']}/100 (Count: {context['parking_count']})")
    text.textLine(f"Zoning: {context['zoning_label']}")
    text.textLine(f"Estimated Sessions/Day: {context['sessions_low']} – {context['sessions_high']}")
    text.moveCursor(0, 12)

    # ---------------- CHARGER CONFIG ----------------
    text.setFont("Helvetica-Bold", 12)
    text.textLine("Charger Configuration")
    text.setFont("Helvetica", 11)
    text.textLine(f"Charger Type: {context['charger_type']}")
    text.textLine(f"Price per kWh: ${context['price_per_kwh']:.2f}")
    text.textLine(f"Electricity Cost per kWh: ${context['electricity_cost']:.2f}")
    text.textLine(f"kWh per Session: {context['kwh_per_session']}")
    text.textLine(f"Install Cost: ${context['install_cost']:,.0f}")
    text.moveCursor(0, 12)

    # ---------------- FINANCIAL PERFORMANCE ----------------
    text.setFont("Helvetica-Bold", 12)
    text.textLine("Financial Performance")
    text.setFont("Helvetica", 11)
    text.textLine(f"Avg Sessions/Day: {context['avg_sessions_per_day']:.1f}")
    text.textLine(f"Monthly Profit: ${context['monthly_profit']:,.2f}")
    text.textLine(f"Payback Period: {context['payback_years']:.2f} years")
    text.moveCursor(0, 12)

    # ---------------- 5-YEAR FORECAST ----------------
    forecast = context.get("forecast")
    if forecast:
        text.setFont("Helvetica-Bold", 12)
        text.textLine("5-Year Income Forecast")
        text.setFont("Helvetica", 11)
        for year in range(1, 6):
            annual = forecast[year]["annual"]
            cumulative = forecast[year]["cumulative"]
            text.textLine(f"Year {year}: ${annual:,.0f}  |  Cumulative: ${cumulative:,.0f}")
        text.moveCursor(0, 12)

    # ---------------- VERDICT ----------------
    text.setFont("Helvetica-Bold", 13)
    text.textLine(f"Final Verdict: {context['verdict']}")

    c.drawText(text)

    # --- ROI PAGE ---
    roi_img_path = context.get("roi_img_path")
    if roi_img_path and os.path.exists(roi_img_path):

        c.showPage()  # start Page 2

        # Title
        c.setFont("Helvetica-Bold", 18)
        c.drawString(40, height - 50, "5-Year ROI Projection")

        # Draw ROI chart
        c.drawImage(
            roi_img_path,
            40,               # x
            height - 400,     # y
            width=520,
            height=330,
            preserveAspectRatio=True,
            mask='auto'
        )

        c.showPage()

    c.save()

    return output_path
