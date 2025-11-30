# backend/scoring/demand.py

"""
Simple demand scoring placeholder.

Later you can plug in:
- Census / WorldPop population density
- Median income
- EV adoption by region
"""

def estimate_demand_score(lat, lon, population_density=None, median_income=None):
    base = 50

    # Population density hook (for real data later)
    if population_density is not None:
        if population_density > 8000:
            base += 20
        elif population_density > 4000:
            base += 10
        elif population_density < 1000:
            base -= 10

    # Income hook (for real data later)
    if median_income is not None:
        if median_income > 90000:
            base += 10
        elif median_income < 40000:
            base -= 10

    # Mild latitude-based urbanization heuristic
    lat_factor = max(0.0, 25.0 - abs(lat)) * 0.5
    score = base + lat_factor

    # Clamp score to a reasonable range
    return max(10, min(95, score))
