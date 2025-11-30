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
    </style>
</head>
<body>

<div id="map"></div>

<script>
    var map = L.map('map').setView([{lat}, {lon}], 14);

    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        maxZoom: 19
    }}).addTo(map);

    var marker = L.marker([{lat}, {lon}]).addTo(map);
    marker.bindPopup("<b>EV Charger Site</b><br>{address}").openPopup();

    var circle = L.circle([{lat}, {lon}], {{
        radius: {radius_m},
        color: 'blue',
        fillColor: '#3498db',
        fillOpacity: 0.15
    }}).addTo(map);
</script>

</body>
</html>
"""


def generate_map_html(address, lat, lon, radius_m=1609, output_dir="reports"):
    """
    Generates an interactive Leaflet HTML map for the site.
    """

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    html_content = HTML_TEMPLATE.format(
        address=address.replace('"', "'"),
        lat=lat,
        lon=lon,
        radius_m=radius_m
    )

    output_path = os.path.join(output_dir, "site_map.html")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path
