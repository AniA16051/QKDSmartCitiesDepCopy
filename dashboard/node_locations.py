"""
Maps sensor node IDs to fixed lat/lon coordinates for the dashboard map.

Sensors don't publish real GPS data in this simulation, so positions are
assigned here. Add an entry for any node_id you plan to run so it shows up
at a sensible spot; unknown node_ids fall back to a default city-center
cluster so the map never breaks.

Coordinates below are placeholder positions around a generic city center --
replace with your actual city's coordinates if you want a realistic map.
"""

import hashlib

CITY_CENTER = (12.9716, 77.5946)  # Bengaluru, India -- change to your city

NODE_LOCATIONS = {
    "traffic-node-07": (12.9756, 77.6006),
    "water-meter-14": (12.9698, 77.5910),
    "camera-22": (12.9741, 77.5983),
}


def get_location(node_id):
    """Returns (lat, lon) for a node. Unknown nodes get a deterministic
    pseudo-random offset from city center, so the same node_id always lands
    in the same spot across runs, but different unknown nodes don't overlap."""
    if node_id in NODE_LOCATIONS:
        return NODE_LOCATIONS[node_id]

    h = int(hashlib.sha256(node_id.encode()).hexdigest(), 16)
    lat_offset = ((h % 1000) / 1000 - 0.5) * 0.03
    lon_offset = (((h // 1000) % 1000) / 1000 - 0.5) * 0.03
    return (CITY_CENTER[0] + lat_offset, CITY_CENTER[1] + lon_offset)
