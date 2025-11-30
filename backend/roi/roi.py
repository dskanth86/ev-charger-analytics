# backend/roi/roi.py

"""
ROI & profitability models for EV charger sites.
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
    Base ROI model for a single charger/card:

    - sessions_low / sessions_high: range of expected daily sessions
    - price_per_kwh: what you charge drivers
    - electricity_cost: what you pay the utility
    - kwh_per_session: average energy per session
    - install_cost: one-time installed cost of the asset
    """

    avg_sessions_per_day = (sessions_low + sessions_high) / 2.0

    daily_energy_kwh = avg_sessions_per_day * kwh_per_session
    daily_revenue = daily_energy_kwh * price_per_kwh
    daily_cost = daily_energy_kwh * electricity_cost
    daily_profit = daily_revenue - daily_cost

    monthly_profit = daily_profit * 30.0
    annual_profit = daily_profit * 365.0

    if annual_profit <= 0:
        payback_years = float("inf")
    else:
        payback_years = install_cost / annual_profit

    return {
        "avg_sessions_per_day": avg_sessions_per_day,
        "daily_revenue": daily_revenue,
        "daily_cost": daily_cost,
        "daily_profit": daily_profit,
        "monthly_profit": monthly_profit,
        "annual_profit": annual_profit,
        "payback_years": payback_years,
    }


def forecast_roi_5yr(
    base_daily_sessions: float,
    price_per_kwh: float,
    electricity_cost: float,
    kwh_per_session: float,
    install_cost: float,
    sessions_growth_rate: float = 0.08,   # 8% more sessions per year
    price_growth_rate: float = 0.02,      # 2% higher pricing per year
    cost_growth_rate: float = 0.03,       # 3% higher energy cost per year
    years: int = 5,
):
    """
    Simple 5-year forecast model.

    Assumes:
    - Daily sessions grow by sessions_growth_rate each year
    - Price and cost per kWh grow by their respective growth rates
    - Returns a list of yearly snapshots with annual & cumulative profit and ROI.
    """

    results = []
    cumulative_profit = 0.0

    for year in range(1, years + 1):
        # Growth factors
        sessions = base_daily_sessions * ((1.0 + sessions_growth_rate) ** (year - 1))
        price_y = price_per_kwh * ((1.0 + price_growth_rate) ** (year - 1))
        cost_y = electricity_cost * ((1.0 + cost_growth_rate) ** (year - 1))

        daily_energy_kwh = sessions * kwh_per_session
        daily_revenue = daily_energy_kwh * price_y
        daily_cost = daily_energy_kwh * cost_y
        daily_profit = daily_revenue - daily_cost

        annual_profit = daily_profit * 365.0
        cumulative_profit += annual_profit

        cumulative_roi = None
        if install_cost > 0:
            cumulative_roi = cumulative_profit / install_cost

        results.append(
            {
                "year": year,
                "avg_sessions_per_day": sessions,
                "price_per_kwh": price_y,
                "electricity_cost": cost_y,
                "annual_profit": annual_profit,
                "cumulative_profit": cumulative_profit,
                "cumulative_roi": cumulative_roi,
            }
        )

    return results
