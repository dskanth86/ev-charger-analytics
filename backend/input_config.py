# backend/input_config.py

"""
Handles all user-configurable inputs for charger & pricing.
This isolates business assumptions from the core engine.
"""

def prompt_user_inputs():
    print("\n--- Charger & Financial Inputs (Press Enter for Defaults) ---")

    charger_type = input("Charger type [L2 / DCFC] (default: L2): ").strip().upper()
    if charger_type not in {"L2", "DCFC"}:
        charger_type = "L2"

    # Defaults based on charger type
    if charger_type == "DCFC":
        default_price_per_kwh = 0.45
        default_kwh_per_session = 35
        default_install_cost = 60000
    else:  # L2
        default_price_per_kwh = 0.35
        default_kwh_per_session = 25
        default_install_cost = 9000

    default_electricity_cost = 0.15

    def get_float(prompt, default):
        val = input(f"{prompt} (default {default}): ").strip()
        return float(val) if val else float(default)

    price_per_kwh = get_float("Price you charge per kWh ($)", default_price_per_kwh)
    electricity_cost = get_float("Your electricity cost per kWh ($)", default_electricity_cost)
    kwh_per_session = get_float("Average kWh per session", default_kwh_per_session)
    install_cost = get_float("Total install cost ($)", default_install_cost)

    return {
        "charger_type": charger_type,
        "price_per_kwh": price_per_kwh,
        "electricity_cost": electricity_cost,
        "kwh_per_session": kwh_per_session,
        "install_cost": install_cost,
    }
