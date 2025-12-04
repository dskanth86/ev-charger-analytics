"""Input jittering for stability tests in EV-Charger Analytics."""

from __future__ import annotations

import random
from dataclasses import replace
from typing import Any, Dict, List

from .pipeline_harness import PipelineInputs, run_pipeline_for_zip


def run_jitter_stability(zip_sample, base_inputs: PipelineInputs, n: int = 3) -> List[Dict[str, Any]]:
    """Run stability tests by jittering financial inputs around a base.

    We keep all external data (geo, traffic, EV adoption, etc.) as-is and
    only jitter:
    - price_per_kwh +/- 10%
    - electricity_cost +/- 10%
    - kwh_per_session +/- 10%

    Returns a list of pipeline output dicts for each jittered run.
    """

    results: List[Dict[str, Any]] = []
    for _ in range(n):
        factor = lambda: 1.0 + random.uniform(-0.1, 0.1)
        jittered = replace(
            base_inputs,
            price_per_kwh=base_inputs.price_per_kwh * factor(),
            electricity_cost=base_inputs.electricity_cost * factor(),
            kwh_per_session=base_inputs.kwh_per_session * factor(),
        )
        out = run_pipeline_for_zip(zip_sample, inputs=jittered)
        d = out.to_dict()
        d["jitter"] = True
        results.append(d)
    return results
