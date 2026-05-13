"""Core DualBalance districting algorithm.

Assigns census blocks to N seeds while minimizing a weighted cost over
geographic distance, population balance, and area balance. See Formalism.md
for the precise objective (§4) and tie-breaking cascade (§5).
"""

from __future__ import annotations


def generate_plan(state, blocks, n_districts: int):
    """Generate a deterministic district plan for a single state.

    Same input always yields the same output.
    """
    raise NotImplementedError("districting is not yet implemented")
