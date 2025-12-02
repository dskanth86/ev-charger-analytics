# backend/main.py

import sys
import requests

# ✅ FLOOD RISK (FEMA)
from data_sources.flood_fema import get_flood_risk
from data_sources.traffic_aadt import get_traffic_score
from data_sources.ev_adoption import get_ev_share_score

# ✅ USER CONFIG (D)
from input_config import prompt_user_inputs

# ✅ SCORING MODULES (A + Competition)
from scoring.demand import estimate_demand_score
from scoring.competition import compute_competition_score
from scoring.sessions import estimate_sessions_range

# ✅ ROI MODULE (base + 5-year forecast)
from roi.roi import roi_model, forecast_roi_5yr

# ✅ MAP OUTPUT (B)
from maps.map_html import generate_map_html

# ✅ PDF REPORT (C)
from reports.pdf_report import generate_pdf_report
from reports.roi_curve import generate_roi_curve

# ✅ ZONING + PARKING (E)
from zoning_parking import analyze_parking, analyze_zoning


# -----------------------------
# CONFIG
# -----------------------------
AFDC_API_URL = "https://developer.nrel.gov/api/alt-fuel-stations/v1.json"
AFDC_API_KEY = "DEMO_KEY"  # dev only


# -----------------------------
# GEO FUNCTIONS
# -----------------------------
def geocode_address(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json"}
    headers = {"User-Agent": "ev-charger-analytics"}

    response = requests.get(url, params=params, headers=headers, timeout=30).json()

    if not response:
        raise ValueError("❌ Address not found")

    return float(response[0]["lat"]), float(response[0]["lon"])


# -----------------------------
# DATA FETCH
# -----------------------------
def fetch_nearby_chargers(lat, lon, radius_miles=1):
    params = {
        "api_key": AFDC_API_KEY,
        "latitude": lat,
        "longitude": lon,
        "radius": radius_miles,
        "fuel_type": "ELEC",
        "limit": 200
    }
    data = requests.get(AFDC_API_URL, params=params, timeout=30).json()
    return data.get("fuel_stations", [])


# -----------------------------
# MAIN EXECUTION
# -----------------------------
def main():
    if len(sys.argv) < 2:
        print('Usage: python backend/main.py "FULL ADDRESS"')
        return

    address = sys.argv[1]

    print("\nEV CHARGER SITE FEASIBILITY CHECK")
    print("---------------------------------")
    print(f"Address: {address}")

    # ✅ GEO
    lat, lon = geocode_address(address)
    print(f"Coordinates: {lat:.5f}, {lon:.5f}")
    
    # Traffic Score (AADT)
    traffic_score = get_traffic_score(lat, lon)
    print(f"Traffic Score: {traffic_score}/100")
    ev_share_score = get_ev_share_score(lat, lon)
    print(f"EV Adoption Score: {ev_share_score}/100")

    # ✅ FLOOD RISK (LIVE FEMA)
    flood_data = get_flood_risk(lat, lon)

    print("\nFlood Risk:")
    print(f"  FEMA Zone: {flood_data['zone']}")
    print(f"  100-Year Floodplain: {flood_data['in_100yr']}")
    print(f"  Insurance Required: {flood_data['insurance_required']}")

    # ✅ DEMAND (A)
    demand_score = estimate_demand_score(lat, lon)
    print(f"Demand Score: {demand_score}/100")

    # ✅ COMPETITION
    chargers = fetch_nearby_chargers(lat, lon)
    charger_count = len(chargers)

    competition_score = compute_competition_score(charger_count)
    print(f"Nearby Chargers (1 mile): {charger_count}")
    print(f"Competition Score: {competition_score}/100")

    # ✅ PARKING & ZONING (E)
    parking_info = analyze_parking(lat, lon)
    zoning_info = analyze_zoning(lat, lon)
    print(f"Parking Score: {parking_info['parking_score']}/100 (count={parking_info['parking_count']})")
    print(f"Zoning: {zoning_info['zoning_label']}")

    # ✅ USER INPUT (D)
    user_inputs = prompt_user_inputs()
    charger_type = user_inputs["charger_type"]
    price_per_kwh = user_inputs["price_per_kwh"]
    electricity_cost = user_inputs["electricity_cost"]
    kwh_per_session = user_inputs["kwh_per_session"]
    install_cost = user_inputs["install_cost"]

    # ✅ USAGE ESTIMATE
    sessions_low, sessions_high, utilization = estimate_sessions_range(
        demand_score=demand_score,
        competition_score=competition_score,
        parking_score=parking_info['parking_score'],
        charger_type=charger_type,
        traffic_score=traffic_score,
        ev_share_score=ev_share_score,
    )
    print(f"Utilization Index: {utilization:.1f}")
    print(f"Estimated Sessions/Day: {sessions_low} – {sessions_high}")

    # ✅ ROI (BASE FINANCIAL ENGINE)
    roi_results = roi_model(
        sessions_low,
        sessions_high,
        price_per_kwh,
        electricity_cost,
        kwh_per_session,
        install_cost
    )

    monthly_profit = roi_results["monthly_profit"]
    payback = roi_results["payback_years"]

    verdict = "✅ BUILD" if payback < 4 else "⚠️ MARGINAL / DO NOT BUILD"

    print("\n--- Financial Summary ---")
    print(f"Charger Type: {charger_type}")
    print(f"Avg Sessions/Day: {roi_results['avg_sessions_per_day']:.1f}")
    print(f"Daily Revenue: ${roi_results['daily_revenue']:.2f}")
    print(f"Daily Cost: ${roi_results['daily_cost']:.2f}")
    print(f"Monthly Profit: ${monthly_profit:,.2f}")
    print(f"Payback Period: {payback:.2f} years")
    print(f"Final Verdict: {verdict}")

    # ✅ 5-YEAR FORECAST
    forecast_5yr = forecast_roi_5yr(
        base_daily_sessions=roi_results["avg_sessions_per_day"],
        price_per_kwh=price_per_kwh,
        electricity_cost=electricity_cost,
        kwh_per_session=kwh_per_session,
        install_cost=install_cost,
    )

    # Reformat forecast for PDF report convenience
    forecast = {
        row["year"]: {
            "annual": row["annual_profit"],
            "cumulative": row["cumulative_profit"],
        }
        for row in forecast_5yr
    }

    print("\n5-Year Income Forecast (Annual / Cumulative):")
    for row in forecast_5yr:
        print(
            f"  Year {row['year']}: "
            f"${row['annual_profit']:,.0f} / ${row['cumulative_profit']:,.0f}"
        )

    roi_curve_path = generate_roi_curve(install_cost, forecast)
    roi_results["chart_path"] = roi_curve_path
    print(f"ROI Curve Generated: {roi_curve_path}")

    # MAP OUTPUT (B)
    map_path = generate_map_html(address, lat, lon, flood_zone=flood_data["zone"])
    print(f"\nInteractive Map Generated: {map_path}")

    # PDF INVESTOR REPORT (C)
    pdf_context = {
        "address": address,
        "lat": lat,
        "lon": lon,
        "demand_score": demand_score,
        "competition_score": competition_score,
        "traffic_score": traffic_score,
        "ev_share_score": ev_share_score,
        "sessions_low": sessions_low,
        "sessions_high": sessions_high,
        "utilization_index": utilization,
        "util_index": utilization,
        "charger_type": charger_type,
        "price_per_kwh": price_per_kwh,
        "electricity_cost": electricity_cost,
        "kwh_per_session": kwh_per_session,
        "install_cost": install_cost,
        "avg_sessions_per_day": roi_results["avg_sessions_per_day"],
        "monthly_profit": monthly_profit,
        "payback_years": payback,
        "verdict": verdict,
        "parking_score": parking_info["parking_score"],
        "parking_count": parking_info["parking_count"],
        "zoning_label": zoning_info["zoning_label"],

        # FLOOD DATA FOR REPORT
        "flood": flood_data,

        # 5-YEAR FORECAST FOR REPORT
        "forecast_5yr": forecast_5yr,
        "forecast": forecast,
        "roi_img_path": roi_results.get("chart_path"),
    }

    pdf_path = generate_pdf_report("reports", pdf_context)
    print(f"PDF Report Generated: {pdf_path}")

    print("---------------------------------\n")


if __name__ == "__main__":
    main()
