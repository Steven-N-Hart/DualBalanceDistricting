"""Lightweight data types shared across the package."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Targets:
    """Per-district population and area targets."""

    population: float  # P* = P / N
    area: float  # A* = A / N


@dataclass(frozen=True)
class Seed:
    """A district seed point in the working CRS."""

    district_id: int
    x: float
    y: float


@dataclass
class Plan:
    """A district assignment plus run metadata.

    ``assignment`` maps each unit's identifier to its district ID
    (``0..n_districts-1``). ``geography`` is the ``Geography.cli_name`` of the
    base unit type used. ``metadata`` is a free-form bag for the generator to
    record run-specific facts (iteration count, convergence, seeds, etc.).
    """

    assignment: dict[str, int]
    n_districts: int
    geography: str
    metadata: dict[str, Any] = field(default_factory=dict)
