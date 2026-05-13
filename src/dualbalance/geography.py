"""Census geography metadata.

The DualBalance algorithm is geography-agnostic. This module just records which
census geographies the CLI recognizes and the conventional column / data-source
information for each.
"""

from __future__ import annotations

from enum import Enum
from typing import NamedTuple


class _GeographySpec(NamedTuple):
    label: str
    default_id_column: str
    tiger_url_template: str


class Geography(Enum):
    VTD = _GeographySpec(
        label="Voting Tabulation District (2020)",
        default_id_column="GEOID20",
        tiger_url_template=(
            "https://www2.census.gov/geo/tiger/TIGER2020/VTD/tl_2020_{fips}_vtd20.zip"
        ),
    )
    BLOCK = _GeographySpec(
        label="Census block (2020)",
        default_id_column="GEOID20",
        tiger_url_template=(
            "https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/"
            "tl_2020_{fips}_tabblock20.zip"
        ),
    )
    BLOCK_GROUP = _GeographySpec(
        label="Census block group (2020)",
        default_id_column="GEOID",
        tiger_url_template=(
            "https://www2.census.gov/geo/tiger/TIGER2020/BG/tl_2020_{fips}_bg20.zip"
        ),
    )

    @property
    def label(self) -> str:
        return self.value.label

    @property
    def default_id_column(self) -> str:
        return self.value.default_id_column

    @property
    def tiger_url_template(self) -> str:
        return self.value.tiger_url_template

    @property
    def cli_name(self) -> str:
        return self.name.lower()

    @classmethod
    def from_cli_name(cls, name: str) -> Geography:
        key = name.strip().upper().replace("-", "_")
        if key not in cls.__members__:
            valid = sorted(m.cli_name for m in cls)
            raise ValueError(f"unknown geography {name!r}; valid: {valid}")
        return cls[key]
