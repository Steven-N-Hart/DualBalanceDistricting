import pytest

from dualbalance.geography import Geography


def test_cli_names_are_lowercase_member_names():
    assert Geography.VTD.cli_name == "vtd"
    assert Geography.BLOCK.cli_name == "block"
    assert Geography.BLOCK_GROUP.cli_name == "block_group"


def test_from_cli_name_roundtrip():
    for member in Geography:
        assert Geography.from_cli_name(member.cli_name) is member


def test_from_cli_name_accepts_dashes_and_case():
    assert Geography.from_cli_name("Block-Group") is Geography.BLOCK_GROUP
    assert Geography.from_cli_name("VTD") is Geography.VTD


def test_from_cli_name_rejects_unknown():
    with pytest.raises(ValueError, match="unknown geography"):
        Geography.from_cli_name("precinct")


def test_default_id_columns():
    assert Geography.VTD.default_id_column == "GEOID20"
    assert Geography.BLOCK.default_id_column == "GEOID20"
    assert Geography.BLOCK_GROUP.default_id_column == "GEOID"


def test_tiger_url_template_includes_fips_placeholder():
    for member in Geography:
        assert "{fips}" in member.tiger_url_template
