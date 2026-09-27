"""Keep the Python project version in step with the npm package version."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_pyproject_version_matches_package_json() -> None:
    """
    `package.json` is the release source of truth (release-it bumps it).

    The release hook in `.release-it.json` runs `uv version ${version}` so
    `pyproject.toml` and `uv.lock` follow in the same release commit.
    """
    npm = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
    pyproject = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    assert pyproject["project"]["version"] == npm["version"]
