"""
Session estimation module for EV charger analytics.

This module provides functions to estimate charging session ranges
based on various factors like demand, competition, and parking.
"""

def compute_utilization_index(
    demand_score: float,
    competition_score: float,
    parking_score: float,
    traffic_score: float = 50.0,
    ev_share_score: float = 50.0
) -> float:
    """
    Calculate the utilization index (0-100) based on weighted factors.
    
    Args:
        demand_score: Demand score (0-100)
        competition_score: Competition score (0-100, will be inverted)
        parking_score: Parking score (0-100)
        traffic_score: Traffic score (0-100), defaults to 50
        ev_share_score: EV market share score (0-100), defaults to 50
        
    Returns:
        float: Utilization index from 0 to 100
    """
    # Invert competition score (100 - score)
    inverse_competition = 100.0 - competition_score
    
    # Calculate weighted sum
    utilization = (
        demand_score * 0.35 +
        inverse_competition * 0.30 +
        parking_score * 0.20 +
        traffic_score * 0.10 +
        ev_share_score * 0.05
    )
    
    # Ensure the result is within 0-100 range
    return max(0.0, min(100.0, utilization))

def get_session_range(utilization: float) -> tuple[int, int]:
    """
    Map utilization index to session range.
    
    Args:
        utilization: Utilization index (0-100)
        
    Returns:
        tuple: (low, high) session range
    """
    if utilization < 20:
        return (1, 3)
    elif utilization < 40:
        return (3, 6)
    elif utilization < 60:
        return (6, 10)
    elif utilization < 80:
        return (10, 16)
    else:
        return (16, 24)

def estimate_sessions_range(
    demand_score: float,
    competition_score: float,
    parking_score: float,
    charger_type: str,
    traffic_score: float = 50.0,
    ev_share_score: float = 50.0
) -> tuple[int, int, float]:
    """
    Estimate the range of charging sessions per day.
    
    Args:
        demand_score: Demand score (0-100)
        competition_score: Competition score (0-100)
        parking_score: Parking score (0-100)
        charger_type: Type of charger ('L2' or 'DCFC')
        traffic_score: Traffic score (0-100), defaults to 50
        ev_share_score: EV market share score (0-100), defaults to 50
        
    Returns:
        tuple: (low_sessions, high_sessions, utilization_index)
    """
    # Calculate utilization index
    utilization = compute_utilization_index(
        demand_score=demand_score,
        competition_score=competition_score,
        parking_score=parking_score,
        traffic_score=traffic_score,
        ev_share_score=ev_share_score
    )
    
    # Get base session range
    low, high = get_session_range(utilization)
    
    # Apply DCFC multiplier if applicable
    if charger_type.upper() == 'DCFC':
        low = int(round(low * 1.8))
        high = int(round(high * 1.8))
    
    return low, high, utilization
