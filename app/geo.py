"""Geographic helper functions."""

import math

EARTH_RADIUS_KM = 6371.0088  # mean Earth radius (IUGG)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in kilometres between two points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def bounding_box(lat: float, lon: float, distance_km: float) -> tuple[float, float, float, float]:
    """Return (min_lat, max_lat, min_lon, max_lon) enclosing a circle.

    Used to pre-filter rows in SQL with the indexed lat/lon columns before
    computing the exact haversine distance in Python.
    """
    d_lat = math.degrees(distance_km / EARTH_RADIUS_KM)
    min_lat, max_lat = max(lat - d_lat, -90.0), min(lat + d_lat, 90.0)

    # Near the poles (or for huge radii) longitude cannot be bounded.
    cos_lat = math.cos(math.radians(lat))
    if max_lat >= 90 or min_lat <= -90 or cos_lat < 1e-9:
        return min_lat, max_lat, -180.0, 180.0
    d_lon = math.degrees(distance_km / (EARTH_RADIUS_KM * cos_lat))
    if d_lon >= 180:
        return min_lat, max_lat, -180.0, 180.0
    return min_lat, max_lat, lon - d_lon, lon + d_lon
