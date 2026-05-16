"""Per-state metadata used by the prep scripts and tests.

Each entry holds the state's 2-digit FIPS code, the TIGER state-name
component used in the TIGER VTD URL path, and the 119th-Congress
apportioned seat count. Add a state by extending :data:`STATE_INFO`.
"""

from __future__ import annotations

from typing import Any

STATE_INFO: dict[str, dict[str, Any]] = {
    "AL": {"fips": "01", "tiger_name": "ALABAMA",        "n_seats":  7},
    "AK": {"fips": "02", "tiger_name": "ALASKA",         "n_seats":  1},
    "AZ": {"fips": "04", "tiger_name": "ARIZONA",        "n_seats":  9},
    "AR": {"fips": "05", "tiger_name": "ARKANSAS",       "n_seats":  4},
    "CA": {"fips": "06", "tiger_name": "CALIFORNIA",     "n_seats": 52},
    "CO": {"fips": "08", "tiger_name": "COLORADO",       "n_seats":  8},
    "CT": {"fips": "09", "tiger_name": "CONNECTICUT",    "n_seats":  5},
    "DE": {"fips": "10", "tiger_name": "DELAWARE",       "n_seats":  1},
    "FL": {"fips": "12", "tiger_name": "FLORIDA",        "n_seats": 28},
    "GA": {"fips": "13", "tiger_name": "GEORGIA",        "n_seats": 14},
    "HI": {"fips": "15", "tiger_name": "HAWAII",         "n_seats":  2},
    "ID": {"fips": "16", "tiger_name": "IDAHO",          "n_seats":  2},
    "IL": {"fips": "17", "tiger_name": "ILLINOIS",       "n_seats": 17},
    "IN": {"fips": "18", "tiger_name": "INDIANA",        "n_seats":  9},
    "IA": {"fips": "19", "tiger_name": "IOWA",           "n_seats":  4},
    "KS": {"fips": "20", "tiger_name": "KANSAS",         "n_seats":  4},
    "KY": {"fips": "21", "tiger_name": "KENTUCKY",       "n_seats":  6},
    "LA": {"fips": "22", "tiger_name": "LOUISIANA",      "n_seats":  6},
    "ME": {"fips": "23", "tiger_name": "MAINE",          "n_seats":  2},
    "MD": {"fips": "24", "tiger_name": "MARYLAND",       "n_seats":  8},
    "MA": {"fips": "25", "tiger_name": "MASSACHUSETTS",  "n_seats":  9},
    "MI": {"fips": "26", "tiger_name": "MICHIGAN",       "n_seats": 13},
    "MN": {"fips": "27", "tiger_name": "MINNESOTA",      "n_seats":  8},
    "MS": {"fips": "28", "tiger_name": "MISSISSIPPI",    "n_seats":  4},
    "MO": {"fips": "29", "tiger_name": "MISSOURI",       "n_seats":  8},
    "MT": {"fips": "30", "tiger_name": "MONTANA",        "n_seats":  2},
    "NE": {"fips": "31", "tiger_name": "NEBRASKA",       "n_seats":  3},
    "NV": {"fips": "32", "tiger_name": "NEVADA",         "n_seats":  4},
    "NH": {"fips": "33", "tiger_name": "NEW_HAMPSHIRE",  "n_seats":  2},
    "NJ": {"fips": "34", "tiger_name": "NEW_JERSEY",     "n_seats": 12},
    "NM": {"fips": "35", "tiger_name": "NEW_MEXICO",     "n_seats":  3},
    "NY": {"fips": "36", "tiger_name": "NEW_YORK",       "n_seats": 26},
    "NC": {"fips": "37", "tiger_name": "NORTH_CAROLINA", "n_seats": 14},
    "ND": {"fips": "38", "tiger_name": "NORTH_DAKOTA",   "n_seats":  1},
    "OH": {"fips": "39", "tiger_name": "OHIO",           "n_seats": 15},
    "OK": {"fips": "40", "tiger_name": "OKLAHOMA",       "n_seats":  5},
    "OR": {"fips": "41", "tiger_name": "OREGON",         "n_seats":  6},
    "PA": {"fips": "42", "tiger_name": "PENNSYLVANIA",   "n_seats": 17},
    "RI": {"fips": "44", "tiger_name": "RHODE_ISLAND",   "n_seats":  2},
    "SC": {"fips": "45", "tiger_name": "SOUTH_CAROLINA", "n_seats":  7},
    "SD": {"fips": "46", "tiger_name": "SOUTH_DAKOTA",   "n_seats":  1},
    "TN": {"fips": "47", "tiger_name": "TENNESSEE",      "n_seats":  9},
    "TX": {"fips": "48", "tiger_name": "TEXAS",          "n_seats": 38},
    "UT": {"fips": "49", "tiger_name": "UTAH",           "n_seats":  4},
    "VT": {"fips": "50", "tiger_name": "VERMONT",        "n_seats":  1},
    "VA": {"fips": "51", "tiger_name": "VIRGINIA",       "n_seats": 11},
    "WA": {"fips": "53", "tiger_name": "WASHINGTON",     "n_seats": 10},
    "WV": {"fips": "54", "tiger_name": "WEST_VIRGINIA",  "n_seats":  2},
    "WI": {"fips": "55", "tiger_name": "WISCONSIN",      "n_seats":  8},
    "WY": {"fips": "56", "tiger_name": "WYOMING",        "n_seats":  1},
}
