import sys
import requests
from math import radians, sin, cos, sqrt, atan2

# -----------------------------
# CONFIG
# -----------------------------
AFDC_API_URL = "https://developer.nrel.gov/api/alt-fuel-stations/v1.json"
AFDC_API_KEY = "DEMO_KEY"  # works for development/testing

# -----------------------------
# UTILITY FUNCTIONS
# -----------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c * 0.621371  # miles


def geocode_address(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json"}
    headers = {"User-Agent": "ev-charger-analytics"}
    response = requests.get(url, params=params, headers=headers).json()

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
    data = requests.get(AFDC_API_URL, params=params).json()
    return data.get("fuel_stations", [])


# -----------------------------
# SCORING ENGINE (V1)
# -----------------------------
def compute_competition_score(charger_count):
    if charger_count == 0:
        return 90
    elif charger_count < 5:
        return 70
    elif charger_count < 10:
        return 45
    else:
        return 20


def estimate_sessions_per_day(competition_score):
    if competition_score > 70:
        return 12, 18
    elif competition_score > 50:
        return 8, 14
    elif competition_score > 30:
        return 4, 9
    else:
        return 1, 4


# -----------------------------
# ROI MODEL
# -----------------------------
def roi_model(sessions_low, sessions_high, price_per_kwh, kwh_per_session, electricity_cost, install_cost):
    avg_sessions = (sessions_low + sessions_high) / 2

    daily_revenue = avg_sessions * kwh_per_session * price_per_kwh
    daily_cost = avg_sessions * kwh_per_session * electricity_cost
    monthly_profit = (daily_revenue - daily_cost) * 30

    if monthly_profit <= 0:
        payback_years = float("inf")
    else:
        payback_years = install_cost / (monthly_profit * 12)

    return monthly_profit, payback_years


# -----------------------------
# MAIN EXECUTION
# -----------------------------
def main():
    if len(sys.argv) < 2:
        print('Usage: python backend/main.py "FULL ADDRESS"')
        return

    address = sys.argv[1]

    print("\nEV CHARGER SITE FEASIBILITY CHECK")
    print("--------------------------------")
    print(f"Address: {address}")

    lat, lon = geocode_address(address)
    print(f"Coordinates: {lat:.5f}, {lon:.5f}")

    chargers = fetch_nearby_chargers(lat, lon)
    charger_count = len(chargers)

    competition_score = compute_competition_score(charger_count)
    sessions_low, sessions_high = estimate_sessions_per_day(competition_score)

    # Default financial assumptions (you can make these user inputs later)
    price_per_kwh = 0.45
    electricity_cost = 0.15
    kwh_per_session = 25
    install_cost = 9000

    monthly_profit, payback = roi_model(
        sessions_low, sessions_high,
        price_per_kwh, kwh_per_session,
        electricity_cost, install_cost
    )

    verdict = "✅ BUILD" if payback < 4 else "⚠️ MARGINAL / DO NOT BUILD"

    print(f"\nNearby Chargers (1 mile): {charger_count}")
    print(f"Competition Score: {competition_score}/100")
    print(f"Estimated Sessions/Day: {sessions_low}–{sessions_high}")
    print(f"Estimated Monthly Profit: ${monthly_profit:,.2f}")
    print(f"Estimated Payback Period: {payback:.2f} years")
    print(f"Final Verdict: {verdict}")
    print("--------------------------------\n")


if __name__ == "__main__":
    main()
