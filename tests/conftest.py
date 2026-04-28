"""
Pytest config: ``--run-slow`` and ``--limit-rows`` CLI options.

The ``slow`` marker is registered in ``pyproject.toml``
(``[tool.pytest.ini_options].markers``), matching the convention used in
vega/altair. The expected-failures allowlist is read at parametrize time
inside ``test_datapackage.py`` (so xfail marks attach by resource-dict
lookup, not by ID-string parsing of pytest's test names) — that logic
does not live here either.
"""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run @pytest.mark.slow tests (frictionless schema/row validation).",
    )
    parser.addoption(
        "--limit-rows",
        type=int,
        default=None,
        help=(
            "Cap row reads in --run-slow tests at N rows per resource. "
            "Default is unlimited (full read). Use a small N for quick "
            "iteration; flights-3m takes minutes at full read."
        ),
    )


@pytest.fixture(scope="session")
def schema_limit_rows(request: pytest.FixtureRequest) -> int | None:
    return request.config.getoption("--limit-rows")


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip ``slow`` items unless ``--run-slow`` was passed."""
    if config.getoption("--run-slow"):
        return
    skip_slow = pytest.mark.skip(reason="opt in with --run-slow")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
