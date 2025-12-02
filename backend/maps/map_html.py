# backend/maps/map_html.py

import os
from pathlib import Path


HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>EV Charger Site Map</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ height: 100vh; width: 100%; }}

        /* ✅ Flood Risk Legend Styling */
        .flood-legend {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 9999;
            background-color: white;
            padding: 10px 14px;
            border: 2px solid black;
            border-radius: 6px;
            font-size: 12px;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
        }}

        .legend-title {{
            font-weight: bold;
            margin-bottom: 6px;
            text-align: center;
        }}

        .legend-item {{
            margin: 3px 0;
        }}

        .legend-box {{
            display: inline-block;
            width: 12px;
            height: 12px;
            margin-right: 6px;
            vertical-align: middle;
        }}
    </style>
</head>
<body>

<div id="map"></div>

<!-- ✅ Flood Risk Legend -->
<div class="flood-legend">
    <div class="legend-title">Flood Risk Legend</div>
    <div class="legend-item">
        <span class="legend-box" style="background:#3498db;"></span>
        Zone X — Minimal Risk
    </div>
    <div class="legend-item">
        <span class="legend-box" style="background:#f1c40f;"></span>
        Zone AE — 100-Year Floodplain
    </div>
    <div class="legend-item">
        <span class="legend-box" style="background:#e74c3c;"></span>
        Zone VE — Coastal High Risk
    </div>
</div>

<script>
    var map = L.map('map').setView([{lat}, {lon}], 14);

    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        maxZoom: 19
    }}).addTo(map);

    var floodZone = "{flood_zone}";
    var poiScore = {poi_score};

    var zoneColor = "green";
    if (floodZone === "AE" || floodZone === "A") {{
        zoneColor = "orange";
    }} else if (floodZone === "VE" || floodZone === "V") {{
        zoneColor = "red";
    }}

    var marker = L.circleMarker([{lat}, {lon}], {{
        radius: 10,
        color: zoneColor,
        fillColor: zoneColor,
        fillOpacity: 0.9
    }}).addTo(map);

    // POI density indicator (ring around the main marker)
    var poiColor = "gray";
    if (!isNaN(poiScore)) {{
        if (poiScore > 70) {{
            poiColor = "green";
        }} else if (poiScore >= 40) {{
            poiColor = "orange";
        }} else {{
            poiColor = "red";
        }}
    }}

    var poiCircle = L.circle([{lat}, {lon}], {{
        radius: {radius_m} / 2,
        color: poiColor,
        fillColor: poiColor,
        fillOpacity: 0.15,
        weight: 3
    }}).addTo(map);

    marker.bindPopup("<b>EV Charger Site</b><br>{address}<br>Flood Zone: " + floodZone + "<br>POI Score: " + poiScore + "/100").openPopup();
</script>

<div style="
position: absolute;
bottom: 20px;
right: 20px;
background: white;
padding: 10px;
border: 1px solid #999;
font-size: 12px;
z-index: 999;
">
<b>Flood Risk Legend</b><br>
<span style="color: green;">●</span> Low Risk (Zone X)<br>
<span style="color: orange;">●</span> Moderate Risk (Zone AE)<br>
<span style="color: red;">●</span> High Risk (Zone VE)
</div>

</body>
</html>
"""


def generate_map_html(address, lat, lon, flood_zone=None, poi_score=50.0, radius_m=1609, output_dir="reports"):
    """Generate an interactive Leaflet map for the site.

    Includes:
    - A flood-risk-colored marker at the site
    - A surrounding ring colored by POI density tier (green/orange/red)
    - A static flood risk legend overlay.
    """

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    html_content = HTML_TEMPLATE.format(
        address=address.replace('"', "'"),
        lat=lat,
        lon=lon,
        radius_m=radius_m,
        flood_zone=flood_zone or "X",
        poi_score=poi_score,
    )

    output_path = os.path.join(output_dir, "site_map.html")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path
