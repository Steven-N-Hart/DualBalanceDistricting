"""Scoring harness for evaluating districting plans.

Computes population balance, geographic balance, and the DualBalance Score:

    DualBalance Score = 1 / (1 + population_error + area_error)

Secondary metrics (compactness, contiguity, county/municipal splits) are
reported but not optimized. The harness is intentionally decoupled from the
generator so it can score any plan -- enacted, court-drawn, or third-party.
See README.md, section "Output and evaluation".
"""

from __future__ import annotations


def score_plan(plan, blocks):
    """Score a districting plan against the DualBalance metrics."""
    raise NotImplementedError("scoring is not yet implemented")
