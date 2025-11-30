# backend/scoring/competition.py

def compute_competition_score(charger_count: int) -> int:
    """
    Simple heuristic:
    - 0 chargers nearby  -> great opportunity (90)
    - 1–4 chargers       -> good (70)
    - 5–9 chargers       -> fair (45)
    - 10+ chargers       -> saturated (20)
    """
    if charger_count == 0:
        return 90
    elif charger_count < 5:
        return 70
    elif charger_count < 10:
        return 45
    else:
        return 20


def estimate_sessions_per_day(demand_score: float, competition_score: float):
    """
    Combines demand & competition into a rough sessions/day band.
    This is a placeholder model that we will refine later.
    """

    demand_factor = demand_score / 100.0
    comp_factor = competition_score / 100.0

    # Base sessions for an average site
    base_low, base_high = 4.0, 9.0

    # Demand & competition adjust this range
    low = base_low * (0.5 + demand_factor) * (0.5 + comp_factor)
    high = base_high * (0.5 + demand_factor) * (0.5 + comp_factor)

    low = max(1.0, low)
    high = max(low + 1.0, high)

    return round(low), round(high)
