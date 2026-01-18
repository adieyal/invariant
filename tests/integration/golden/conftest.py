"""Pytest configuration for golden tests."""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add --update-golden option to pytest."""
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help="Update golden files with current output",
    )


@pytest.fixture
def update_golden(request: pytest.FixtureRequest) -> bool:
    """Fixture to check if --update-golden flag was passed."""
    return request.config.getoption("--update-golden", default=False)
