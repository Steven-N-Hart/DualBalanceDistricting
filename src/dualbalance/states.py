"""Per-state metadata used by the prep scripts and tests.

Add a state by extending :data:`STATE_INFO` with its FIPS code, TIGER
state-name (used in the TIGER VTD URL path), and 119th-Congress
apportioned seat count.
"""

from __future__ import annotations

from typing import Any

STATE_INFO: dict[str, dict[str, Any]] = {
    "MN": {"fips": "27", "tiger_name": "MINNESOTA", "n_seats": 8},
    "IA": {"fips": "19", "tiger_name": "IOWA", "n_seats": 4},
    "MA": {"fips": "25", "tiger_name": "MASSACHUSETTS", "n_seats": 9},
    "TX": {"fips": "48", "tiger_name": "TEXAS", "n_seats": 38},
    "NC": {"fips": "37", "tiger_name": "NORTH_CAROLINA", "n_seats": 14},
    "WI": {"fips": "55", "tiger_name": "WISCONSIN", "n_seats": 8},
}
