"""Deterministic seat apportionment across states.

Implements the Method of Equal Proportions (current U.S. standard):

    priority(s, n) = population(s) / sqrt(n * (n + 1))

See README.md, section "Representation allocation (apportionment)".
"""

from __future__ import annotations


def apportion_seats(state_populations: dict[str, int], total_seats: int) -> dict[str, int]:
    """Assign `total_seats` across states using the Method of Equal Proportions.

    Each state first receives one seat; remaining seats are assigned iteratively
    to the state with the highest priority value. Ties are broken by the
    deterministic cascade defined in Formalism.md.
    """
    raise NotImplementedError("apportionment is not yet implemented")
