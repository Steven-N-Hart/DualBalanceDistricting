"""Deterministic seat apportionment across states.

Implements the Method of Equal Proportions (current U.S. standard):

    priority(s, n) = population(s) / sqrt(n * (n + 1))

See README.md, section "Representation allocation (apportionment)".
"""

from __future__ import annotations

import heapq
import math


def apportion_seats(state_populations: dict[str, int], total_seats: int) -> dict[str, int]:
    """Assign ``total_seats`` across states using the Method of Equal Proportions.

    Each state first receives one seat; remaining seats are assigned iteratively
    to the state with the highest priority value

        priority(s, n) = population(s) / sqrt(n * (n + 1))

    where ``n`` is the state's current seat count. Ties are broken
    deterministically by ascending lexicographic order of the state identifier.

    Raises:
        ValueError: if ``total_seats`` is less than the number of states (every
            state is guaranteed at least one seat), or if any population is
            negative.
    """
    n_states = len(state_populations)
    if total_seats < n_states:
        raise ValueError(
            f"total_seats ({total_seats}) is less than the number of states "
            f"({n_states}); each state must receive at least one seat."
        )
    for state, pop in state_populations.items():
        if pop < 0:
            raise ValueError(f"population for {state!r} is negative: {pop}")

    seats: dict[str, int] = dict.fromkeys(state_populations, 1)

    def priority(state: str, n: int) -> float:
        return state_populations[state] / math.sqrt(n * (n + 1))

    # Max-heap by priority via negation. Tuples (-priority, state) tie-break on
    # state name in ascending order, matching the documented rule.
    heap: list[tuple[float, str]] = [(-priority(state, 1), state) for state in state_populations]
    heapq.heapify(heap)

    for _ in range(total_seats - n_states):
        _, state = heapq.heappop(heap)
        seats[state] += 1
        heapq.heappush(heap, (-priority(state, seats[state]), state))

    return seats
