"""Tests for ``scripts/build_datapackage.py``."""

from __future__ import annotations

import subprocess as sp
from typing import TYPE_CHECKING, Any, cast

import pytest

from scripts.build_datapackage import ResourceAdapter, git_blob_sha1, iter_resources

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"a,b\n1,x\n",
        b"a,b\r\n1,x\r\n",
        bytes(range(256)),
    ],
    ids=["empty", "lf", "crlf", "binary"],
)
def test_git_blob_sha1_matches_git(tmp_path: Path, content: bytes) -> None:
    """The hash is git's object name for the file's bytes, whatever they are."""
    fp = tmp_path / "blob"
    fp.write_bytes(content)
    expected = sp.run(
        ["git", "hash-object", "--no-filters", fp],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert git_blob_sha1(fp) == f"sha1:{expected}"


def test_iter_resources_hashes_working_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    A dataset that git has never seen gets a hash of its current contents.

    Regression: hashes used to come from ``git ls-tree``, so building before
    committing crashed on a new file and recorded a stale hash for an edited one.
    """
    fp = tmp_path / "untracked.csv"
    fp.write_bytes(b"a,b\n1,x\n2,y\n")
    monkeypatch.chdir(tmp_path)
    (resource,) = iter_resources(tmp_path, {})
    assert resource.bytes == fp.stat().st_size
    assert resource.hash == git_blob_sha1(fp)


def test_with_extras_keeps_standard_table_schema_properties(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TOML overrides preserve every standard Table Schema property the site shows."""
    # Resources are inferred from paths relative to the data directory.
    monkeypatch.chdir(tmp_path)
    (tmp_path / "fixture.csv").write_text(
        "id,parent,hp,grade,when\n1,,100,low,2020/01/02 10:00\n2,1,-99,high,2020/01/03 11:00\n",
        "utf-8",
    )
    categories = [{"value": "low", "label": "Low"}, {"value": "high", "label": "High"}]
    extras: dict[str, Any] = {
        "title": "A fully described fixture",
        "schema": {
            "primaryKey": ["id"],
            "foreignKeys": [
                {"fields": "parent", "reference": {"resource": "", "fields": "id"}},
                {"fields": ["grade"], "reference": {"resource": "g", "fields": ["n"]}},
            ],
            "missingValues": ["", "-99"],
            "fields": [
                {
                    "name": "id",
                    "title": "Identifier",
                    "constraints": {"required": True, "unique": True},
                },
                {
                    "name": "hp",
                    "type": "number",
                    "title": "Horsepower (hp)",
                    "constraints": {"minimum": 0, "maximum": 500},
                    "missingValues": ["-99", "NA"],
                },
                {
                    "name": "grade",
                    "type": "string",
                    "categories": categories,
                    "categoriesOrdered": True,
                    "constraints": {"enum": ["low", "high"]},
                },
                {"name": "when", "type": "datetime", "format": "%Y/%m/%d %H:%M"},
            ],
        },
    }
    resource = ResourceAdapter.from_path(tmp_path / "fixture.csv")
    resource = ResourceAdapter.with_extras(resource, **cast("Any", extras))
    out = resource.to_dict()
    assert out["title"] == "A fully described fixture"
    schema = out["schema"]
    assert schema["primaryKey"] == ["id"]
    assert schema["missingValues"] == ["", "-99"]
    # frictionless writes the string forms of foreign keys as arrays.
    assert schema["foreignKeys"] == [
        {"fields": ["parent"], "reference": {"resource": "", "fields": ["id"]}},
        {"fields": ["grade"], "reference": {"resource": "g", "fields": ["n"]}},
    ]
    fields = {f["name"]: f for f in schema["fields"]}
    assert fields["id"]["title"] == "Identifier"
    assert fields["id"]["constraints"] == {"required": True, "unique": True}
    assert fields["hp"]["title"] == "Horsepower (hp)"
    assert fields["hp"]["constraints"] == {"minimum": 0, "maximum": 500}
    assert fields["hp"]["missingValues"] == ["-99", "NA"]
    assert fields["grade"]["categories"] == categories
    assert fields["grade"]["categoriesOrdered"] is True
    assert fields["grade"]["constraints"] == {"enum": ["low", "high"]}
    assert fields["when"]["format"] == "%Y/%m/%d %H:%M"
