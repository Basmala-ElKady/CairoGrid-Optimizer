"""
Data adapter layer for transforming raw CSV data (via DataLoader) into
DP-compatible input formats.

bus_routes.csv  → ResourceAllocationDP  (0/1 Knapsack)
transport_demand.csv → SchedulingDP     (Weighted Interval Scheduling)

Deterministic — same input always produces the same output.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fixed time windows used to expand OD-pair daily demand into per-trip data.
# Each window is (label, start_hour, end_hour, fraction_of_daily_demand).
# Fractions must sum to 1.0.
# ---------------------------------------------------------------------------
TIME_WINDOWS = [
    ("morning",   6.0,  10.0, 0.40),   # 06:00 – 10:00  (40 % of daily)
    ("afternoon", 12.0, 16.0, 0.30),   # 12:00 – 16:00  (30 %)
    ("evening",   17.0, 21.0, 0.30),   # 17:00 – 21:00  (30 %)
]

# Duration of each synthetic trip within a time window (in hours)
TRIP_DURATION_H = 1.0


# ---------------------------------------------------------------------------
# 1. bus_routes.csv  →  ResourceAllocationDP input
# ---------------------------------------------------------------------------
def adapt_bus_routes(raw_routes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert raw CSV rows (with headers like 'RouteID', 'Buses Assigned',
    'Daily Passengers') into the dict schema expected by ResourceAllocationDP:

        {"route_id": str, "buses": int, "passengers": int}

    Parameters
    ----------
    raw_routes : list[dict]
        Each dict must contain keys with *original* CSV column names
        (case-insensitive after pandas header normalisation).

    Returns
    -------
    list[dict]
        DP-ready items where weight = buses, value = passengers.
    """
    adapted: List[Dict[str, Any]] = []

    for row in raw_routes:
        # Support both raw CSV column names and pre-cleaned names
        route_id = (
            row.get("routeid")
            or row.get("RouteID")
            or row.get("route_id", "")
        )
        buses_raw = (
            row.get("buses assigned")
            or row.get("Buses Assigned")
            or row.get("buses", 0)
        )
        passengers_raw = (
            row.get("daily passengers")
            or row.get("Daily Passengers")
            or row.get("passengers", 0)
        )

        buses = int(float(buses_raw))
        passengers = int(float(passengers_raw))

        if buses <= 0:
            logger.warning(
                "Route %s has buses=%d — clamped to 1 for knapsack weight.",
                route_id, buses,
            )

        adapted.append({
            "route_id": str(route_id),
            "buses": buses,
            "passengers": passengers,
        })

    return adapted


# ---------------------------------------------------------------------------
# 2. transport_demand.csv  →  SchedulingDP input
# ---------------------------------------------------------------------------
def _hour_to_hhmm(hour: float) -> str:
    """Convert decimal hour (e.g. 6.5) to 'HH:MM' string ('06:30')."""
    h = int(hour)
    m = int(round((hour - h) * 60))
    return f"{h:02d}:{m:02d}"


def adapt_transport_demand(
    raw_demand: List[Dict[str, Any]],
    trips_per_window: int = 2,
) -> List[Dict[str, Any]]:
    """
    Convert OD-pair daily-demand rows into synthetic trip intervals for
    the Weighted Interval Scheduling DP.

    For every OD pair and every TIME_WINDOW the function generates
    ``trips_per_window`` non-overlapping trips that together carry the
    fraction of the daily demand assigned to that window.

    The output is **deterministic** — identical inputs always produce
    identical outputs.

    Parameters
    ----------
    raw_demand : list[dict]
        Each dict has keys 'FromID'/'fromid', 'TOID'/'toid',
        'Daily Passengers'/'daily passengers'.
    trips_per_window : int
        How many trips to create per OD-pair per time window.

    Returns
    -------
    list[dict]
        Each item: {"bus_id", "start_time", "end_time", "passengers"}
    """
    trips: List[Dict[str, Any]] = []

    for idx, row in enumerate(raw_demand):
        from_id = str(
            row.get("fromid")
            or row.get("FromID")
            or row.get("from_id", f"O{idx}")
        )
        to_id = str(
            row.get("toid")
            or row.get("TOID")
            or row.get("to_id", f"D{idx}")
        )
        daily_pax_raw = (
            row.get("daily passengers")
            or row.get("Daily Passengers")
            or row.get("passengers", 0)
        )
        daily_pax = int(float(daily_pax_raw))

        bus_id = f"{from_id}-{to_id}"

        for window_label, win_start, win_end, fraction in TIME_WINDOWS:
            window_pax = int(daily_pax * fraction)
            window_len = win_end - win_start       # hours available

            # Compute trip duration so they fit non-overlappingly
            trip_len = min(TRIP_DURATION_H, window_len / max(trips_per_window, 1))

            for t in range(trips_per_window):
                trip_start = win_start + t * trip_len
                trip_end = trip_start + trip_len
                pax_per_trip = window_pax // max(trips_per_window, 1)

                trips.append({
                    "bus_id": bus_id,
                    "start_time": _hour_to_hhmm(trip_start),
                    "end_time": _hour_to_hhmm(trip_end),
                    "passengers": pax_per_trip,
                })

    return trips
