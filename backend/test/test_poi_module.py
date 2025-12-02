"""backend/test/test_poi_module.py

Simple dry-run test hook for the POI module.

This is not a formal unit test suite; it is a convenience script
that can be invoked to verify that the OSM-based POI scoring
pipeline works end-to-end for a sample coordinate.
"""

from data_sources.poi_osm import get_poi_score


def main() -> None:
    """Run a simple dry-run of get_poi_score using sample coordinates."""
    # Example: downtown San Francisco
    lat, lon = 37.7890, -122.4010

    result = get_poi_score(lat, lon)

    print("POI dry-run test (SF downtown example):")
    print(f"  Input lat/lon: {lat}, {lon}")
    print(f"  POI Count: {result.get('poi_count')}")
    print(f"  POI Density (/km^2): {result.get('poi_density')}")
    print(f"  POI Score: {result.get('poi_score')}/100")


if __name__ == "__main__":
    main()
