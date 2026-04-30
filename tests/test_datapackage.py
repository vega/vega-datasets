"""
Validate every resource in datapackage.json against its on-disk file.

Two tiers:

* Default — stdlib-only file existence, byte size, and git-blob SHA-1
  against the descriptor. Sub-second across all 70+ resources. Covers
  what frictionless-py doesn't today (byte-count returns ``None`` for
  tabular JSON / arrow / parquet; hash-count supports only md5 and
  sha256, descriptor uses sha1).

* Slow (``pytest --run-slow``) — frictionless schema and row validation
  per resource. Multi-minute on flights-3m at full read; opt in via the
  ``--run-slow`` flag and pass ``--limit-rows N`` to cap row reads
  during iteration. Default is full read.

Resources whose schema/row check is known-broken upstream (``movies``
documented pedagogy; ``flights_200k_arrow`` no upstream parser) are
listed in ``_data/validate_datapackage.toml`` and marked
``xfail(strict=True)`` at parametrize time. Removing an entry
re-enables strict checking; if the upstream issue resolves, the run
flips XFAIL → XPASS and fails, prompting allowlist removal.
"""

from __future__ import annotations

import hashlib
import json
import tomllib
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from frictionless import Checklist, Package

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
DESCRIPTOR_PATH = REPO / "datapackage.json"
ALLOWLIST_PATH = REPO / "_data" / "validate_datapackage.toml"


def _load_resources() -> list[dict]:
    return json.loads(DESCRIPTOR_PATH.read_text(encoding="utf-8"))["resources"]


def _load_xfail_reasons() -> dict[str, str]:
    """Read the allowlist; xfail reason is the first non-empty line of `reason`."""
    if not ALLOWLIST_PATH.exists():
        return {}
    cfg = tomllib.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    return {
        entry["resource"]: entry["reason"].strip().splitlines()[0]
        for entry in cfg.get("expected_failures", [])
    }


_RESOURCES = _load_resources()
_RESOURCE_IDS = [r["name"] for r in _RESOURCES]
_XFAIL = _load_xfail_reasons()

# Sanity-check the allowlist against the live descriptor at import time.
# A stale entry in validate_datapackage.toml is a silent maintenance hazard
# otherwise — the xfail mark would never attach and a real regression
# could slip past.
_unknown_xfail = set(_XFAIL) - set(_RESOURCE_IDS)
if _unknown_xfail:
    msg = (
        f"_data/validate_datapackage.toml lists resources not in datapackage.json: "
        f"{sorted(_unknown_xfail)}"
    )
    raise RuntimeError(msg)


def git_blob_sha1(path: Path) -> str:
    r"""Compute git's blob SHA-1: ``sha1(b"blob {len}\0" + content)``."""
    content = path.read_bytes()
    return hashlib.sha1(b"blob %d\0%b" % (len(content), content)).hexdigest()


@pytest.mark.parametrize("resource", _RESOURCES, ids=_RESOURCE_IDS)
def test_file_exists(resource: dict) -> None:
    assert "path" in resource, (
        f"descriptor regression: resource {resource.get('name')!r} has no 'path'"
    )
    path = DATA / resource["path"]
    assert path.exists(), f"missing data file: {resource['path']}"


@pytest.mark.parametrize("resource", _RESOURCES, ids=_RESOURCE_IDS)
def test_bytes_match(resource: dict) -> None:
    assert "bytes" in resource, (
        f"descriptor regression: 'bytes' missing for {resource['name']!r}"
    )
    path = DATA / resource["path"]
    if not path.exists():
        pytest.skip(f"file missing — see test_file_exists[{resource['name']}]")
    declared = resource["bytes"]
    actual = path.stat().st_size
    assert declared == actual, f"declared={declared} disk={actual}"


@pytest.mark.parametrize("resource", _RESOURCES, ids=_RESOURCE_IDS)
def test_sha1_matches_git_blob(resource: dict) -> None:
    declared = resource.get("hash", "")
    assert declared, f"descriptor regression: 'hash' missing for {resource['name']!r}"
    assert declared.startswith("sha1:"), (
        f"descriptor regression: hash format not sha1 for {resource['name']!r}: "
        f"{declared!r}"
    )
    path = DATA / resource["path"]
    if not path.exists():
        pytest.skip(f"file missing — see test_file_exists[{resource['name']}]")
    expected = declared.removeprefix("sha1:")
    actual = git_blob_sha1(path)
    assert expected == actual, f"declared={expected[:10]}... disk={actual[:10]}..."


def _slow_param(resource: dict) -> Any:  # pytest.ParameterSet; not in public API
    """Build the parametrize entry for the slow tier; attach xfail strict if allowlisted."""
    name = resource["name"]
    marks = []
    if name in _XFAIL:
        marks = [pytest.mark.xfail(reason=_XFAIL[name], strict=True)]
    return pytest.param(resource, id=name, marks=marks)


@pytest.mark.slow
@pytest.mark.parametrize("resource", [_slow_param(r) for r in _RESOURCES])
def test_schema_and_rows(resource: dict, schema_limit_rows: int | None) -> None:
    """Validate column types and row content via frictionless."""
    # parallel=False is load-bearing: frictionless's parallel code path silently
    # ignores Checklist.skip_errors, which would re-surface byte-count and
    # hash-count errors that phase 1 already covers more completely. Don't
    # flip without verifying upstream.
    checklist = Checklist(skip_errors=["byte-count", "hash-count"])
    # basepath workaround: descriptor paths are bare filenames under data/ (see #758).
    package = Package({"resources": [deepcopy(resource)]}, basepath=str(DATA))
    report = package.validate(
        checklist=checklist, limit_rows=schema_limit_rows, parallel=False
    )
    if report.valid:
        return

    # Failure rendering — guarded against empty tasks (frictionless can return
    # package-level errors without per-task entries).
    lines: list[str] = []
    if report.tasks:
        task_errors = report.tasks[0].errors
        for err in task_errors[:5]:
            field = getattr(err, "field_name", None)
            lines.append(f"{err.type} field={field!r}: {err.note}")
        if len(task_errors) > 5:
            lines.append(f"  (+{len(task_errors) - 5} more)")
    for err in list(getattr(report, "errors", []) or [])[:5]:
        lines.append(f"package-level {err.type}: {err.note}")
    pytest.fail("\n".join(lines) or f"validation failed (no error details): {report!r}")
