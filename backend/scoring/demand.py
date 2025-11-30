# backend/scoring/demand.py

"""
Demand scoring module.

Now combines:
- A base heuristic (fallback / non-US / API failure)
- Optional Census ACS data (population + income) for US locations
"""

from data_sources.census_api import fetch_population_income




def _base_heuristic(lat, lon):
    """
    Your original heuristic baseline.
    Simple latitude-based urbanization proxy.
    """
    base = 50.0
    lat_factor = max(0.0, 25.0 - abs(lat)) * 0.5
    score = base + lat_factor
    return max(10.0, min(95.0, score))


def estimate_demand_score(lat, lon):
    """
    Main entry point for demand score.

    Logic:
    1) Compute baseline heuristic score
    2) Try to fetch Census population + income
    3) Adjust score with gentle boosts based on:
         - population (more people → higher demand)
         - median income (higher income → more EVs, more willingness to pay)
    4) Clamp to [10, 95]
    """
    base = _base_heuristic(lat, lon)

    population, median_income = None, None
    try:
        population, median_income = fetch_population_income(lat, lon)
    except Exception:
        # Fail quietly and just use heuristic
        return round(base, 1)

    score = base

    # Population effect (very rough bands)
    if population is not None:
        if population > 60000:
            score += 12
        elif population > 30000:
            score += 8
        elif population > 15000:
            score += 4
        elif population < 5000:
            score -= 5

    # Income effect (median household income)
    if median_income is not None:
        if median_income > 120000:
            score += 6
        elif median_income > 80000:
            score += 3
        elif median_income < 40000:
            score -= 4

    score = max(10.0, min(95.0, score))
    return round(score, 1)
