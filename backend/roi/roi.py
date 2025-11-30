# backend/roi/roi.py

"""
ROI and Payback Model for EV Charger Sites

This module converts:
- Estimated sessions/day
- Charging price ($/kWh)
- Electricity cost ($/kWh)
- kWh per session
- Install cost

Into:
- Daily revenue
- Daily operating cost
- Monthly profit
- Payback period (years)
"""

def roi_model(
    sessions_low: float,
    sessions_high: float,
    price_per_kwh: float,
    electricity_cost: float,
    kwh_per_session: float,
    install_cost: float,
):
    """
    Returns a dictionary with full financial outputs.
    """

    avg_sessions = (sessions_low + sessions_high) / 2.0

    daily_revenue = avg_sessions * kwh_per_session * price_per_kwh
    daily_cost = avg_sessions * kwh_per_session * electricity_cost

    daily_profit = daily_revenue - daily_cost
    monthly_profit = daily_profit * 30.0
    annual_profit = monthly_profit * 12.0

    if annual_profit <= 0:
        payback_years = float("inf")
    else:
        payback_years = install_cost / annual_profit

    return {
        "avg_sessions_per_day": avg_sessions,
        "daily_revenue": daily_revenue,
        "daily_cost": daily_cost,
        "daily_profit": daily_profit,
        "monthly_profit": monthly_profit,
        "annual_profit": annual_profit,
        "payback_years": payback_years,
    }
