"""
Validate every resource in datapackage.json against its on-disk file.

Two tiers:

* Default — stdlib-only file existence, byte size, and git-blob SHA-1
  against the descriptor. Sub-second across all 70+ resources. Covers
  what frictionless-py doesn't today (byte-count returns ``None`` for
  tabular JSON / arrow / parquet; hash-count supports only md5 and
  sha256, descriptor uses sha1).

* Slow (``pytest --runslow``) — frictionless schema and row validation
  per resource. Multi-minute on flights-3m at full read; opt in via the
  ``--runslow`` flag and pass ``--limit-rows N`` to cap row reads
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
_GALLERY_EXAMPLES = json.loads(
    (DATA / "gallery-examples.json").read_text(encoding="utf-8")
)

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
    """Catch descriptors that point at a missing or relocated data file."""
    assert "path" in resource, (
        f"descriptor regression: resource {resource.get('name')!r} has no 'path'"
    )
    path = DATA / resource["path"]
    assert path.exists(), f"missing data file: {resource['path']}"


@pytest.mark.parametrize("resource", _RESOURCES, ids=_RESOURCE_IDS)
def test_bytes_match(resource: dict) -> None:
    """Catch on-disk edits where `bytes` in the descriptor wasn't regenerated."""
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
    """
    Catch on-disk edits where `hash` in the descriptor wasn't regenerated.

    Uses git's blob SHA-1 so the recorded hash matches `git ls-tree` —
    catches edits that change content without changing file size.
    """
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


def test_gallery_dataset_references_exist() -> None:
    """Ensure gallery dataset names remain valid Data Package join keys."""
    resource_names = {resource["name"] for resource in _RESOURCES}
    referenced_names = {
        dataset for example in _GALLERY_EXAMPLES for dataset in example["datasets"]
    }

    unknown = sorted(referenced_names - resource_names)
    assert not unknown, (
        f"gallery-examples.json references unknown Data Package resources: {unknown}"
    )


def test_gallery_resource_has_documented_table_schema() -> None:
    """Document the registry as tabular JSON in generated Data Package outputs."""
    resource = next(r for r in _RESOURCES if r["name"] == "gallery_examples")
    assert resource["type"] == "table"
    assert resource["format"] == "json"
    schema = resource["schema"]
    fields = {field["name"]: field for field in schema["fields"]}
    assert list(fields) == [
        "gallery_name",
        "example_name",
        "example_url",
        "spec_url",
        "categories",
        "description",
        "datasets",
    ]
    assert schema["$schema"] == "https://datapackage.org/profiles/2.0/tableschema.json"
    assert schema["fieldsMatch"] == "equal"
    assert schema["primaryKey"] == ["example_url"]
    assert fields["spec_url"]["constraints"]["unique"] is True
    for name in ("categories", "datasets"):
        assert fields[name]["arrayItem"] == {"type": "string"}
    assert fields["example_url"]["description"].startswith("Stable, unique URL")
    assert "resources[].name" in fields["datasets"]["description"]


def test_gallery_record_shape() -> None:
    """Keep the generated registry's internal record shape consistent."""
    expected_fields = {
        "gallery_name",
        "example_name",
        "example_url",
        "spec_url",
        "categories",
        "description",
        "datasets",
    }
    assert all(set(example) == expected_fields for example in _GALLERY_EXAMPLES)


@pytest.mark.parametrize("field", ["categories", "datasets"])
def test_gallery_list_fields_contain_strings(field: str) -> None:
    """Ensure list-valued fields contain only their expected string values."""
    for example in _GALLERY_EXAMPLES:
        values = example[field]
        assert isinstance(values, list)
        assert all(isinstance(value, str) for value in values)


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
