"""ZIP code sampling system for EV-Charger Analytics tests.

Provides a diverse sample of 500+ ZIP codes across the U.S. covering:
- rural vs dense
- low- vs high-income
- low- vs high-EV-share
- tourist regions.

This module intentionally uses a static curated list and simple
expansion heuristics so that tests are deterministic and do not depend
on external data services.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Set


@dataclass
class ZipSample:
    zip_code: str
    state: str
    city: str
    region_type: str  # e.g. "urban", "suburban", "rural"
    income_band: str  # e.g. "low", "middle", "high"
    ev_share_band: str  # e.g. "low", "medium", "high"
    tag: str  # free-form label like "tourist", "tech_hub", etc.


_BASE_ZIPS: List[ZipSample] = [
    # Dense, high-income, high-EV-share urban cores
    ZipSample("94103", "CA", "San Francisco", "urban", "high", "high", "SF_SOMA_tech_hub"),
    ZipSample("94016", "CA", "Daly City", "urban", "high", "high", "SF_bay_high_ev"),
    ZipSample("10001", "NY", "New York", "urban", "high", "medium", "NYC_Midtown"),
    ZipSample("02108", "MA", "Boston", "urban", "high", "high", "Boston_downtown"),
    ZipSample("98101", "WA", "Seattle", "urban", "high", "high", "Seattle_core"),
    ZipSample("30303", "GA", "Atlanta", "urban", "middle", "medium", "Atlanta_downtown"),
    ZipSample("60601", "IL", "Chicago", "urban", "high", "medium", "Chicago_loop"),
    ZipSample("73301", "TX", "Austin", "urban", "middle", "medium", "Austin_core"),
    ZipSample("80202", "CO", "Denver", "urban", "high", "high", "Denver_core"),
    ZipSample("90012", "CA", "Los Angeles", "urban", "middle", "medium", "LA_downtown"),
    # Suburban high-EV pockets
    ZipSample("94040", "CA", "Mountain View", "suburban", "high", "high", "MountainView"),
    ZipSample("95014", "CA", "Cupertino", "suburban", "high", "high", "Cupertino"),
    ZipSample("98116", "WA", "Seattle", "suburban", "middle", "medium", "WestSeattle"),
    ZipSample("07030", "NJ", "Hoboken", "suburban", "high", "medium", "Hoboken"),
    ZipSample("20852", "MD", "Rockville", "suburban", "high", "medium", "Rockville"),
    # Rural, low-income, low-EV-share
    ZipSample("71601", "AR", "Pine Bluff", "rural", "low", "low", "PineBluff_AR"),
    ZipSample("42301", "KY", "Owensboro", "rural", "low", "low", "Owensboro_KY"),
    ZipSample("59301", "MT", "Miles City", "rural", "low", "low", "MilesCity_MT"),
    ZipSample("86001", "AZ", "Flagstaff", "rural", "middle", "low", "Flagstaff_AZ"),
    ZipSample("83221", "ID", "Blackfoot", "rural", "low", "low", "Blackfoot_ID"),
    # Tourist regions
    ZipSample("89109", "NV", "Las Vegas", "urban", "middle", "medium", "LasVegas_strip"),
    ZipSample("32821", "FL", "Orlando", "suburban", "middle", "medium", "Orlando_parks"),
    ZipSample("96740", "HI", "Kailua-Kona", "rural", "middle", "high", "KailuaKona_HI"),
    ZipSample("81611", "CO", "Aspen", "rural", "high", "high", "Aspen_CO"),
    ZipSample("02657", "MA", "Provincetown", "rural", "middle", "medium", "Provincetown_MA"),
]


def _expand_zip(zip_code: str, offset: int) -> str:
    """Generate a nearby pseudo-ZIP by adding a small offset.

    Keeps within 5-digit numeric range and preserves leading zeros.
    Deterministic and local to the base ZIP.
    """

    base = int(zip_code)
    candidate = max(1, min(99999, base + offset))
    return f"{candidate:05d}"


def generate_zip_samples(target_count: int = 500) -> List[ZipSample]:
    """Return an expanded list of ZipSample entries of at least target_count.

    We start from a curated base list and expand deterministically around
    each base ZIP while tracking already-used ZIP codes to avoid
    duplicates. A hard cap on attempts prevents infinite loops.
    """

    samples: List[ZipSample] = list(_BASE_ZIPS)
    seen: Set[str] = {z.zip_code for z in samples}

    i = 0
    attempts = 0
    max_attempts = target_count * 20  # generous cap to avoid hangs

    while len(samples) < target_count and attempts < max_attempts:
        base = _BASE_ZIPS[i % len(_BASE_ZIPS)]

        # Expand with a growing offset so we explore a wider band of
        # nearby ZIPs instead of a small fixed list of offsets.
        band = (i // len(_BASE_ZIPS)) + 1
        sign = 1 if band % 2 == 1 else -1
        offset = sign * band
        new_zip = _expand_zip(base.zip_code, offset)

        if new_zip not in seen:
            samples.append(
                ZipSample(
                    zip_code=new_zip,
                    state=base.state,
                    city=base.city,
                    region_type=base.region_type,
                    income_band=base.income_band,
                    ev_share_band=base.ev_share_band,
                    tag=base.tag + "_var",
                )
            )
            seen.add(new_zip)

        i += 1
        attempts += 1

    return samples
