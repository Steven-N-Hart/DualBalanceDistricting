import pytest

from dualbalance.cli import build_parser


@pytest.mark.parametrize("cmd", ["generate", "apportion", "score", "compare"])
def test_subcommand_help_parses(cmd: str) -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args([cmd, "--help"])
    assert exc_info.value.code == 0
