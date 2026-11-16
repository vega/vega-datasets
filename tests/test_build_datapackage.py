"""Tests for ``scripts/build_datapackage.py``."""

from __future__ import annotations

import json
import subprocess as sp
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pytest
import yaml
from frictionless import Package

from scripts.build_datapackage import (
    ResourceAdapter,
    git_blob_sha1,
    iter_resources,
    write_package,
)

if TYPE_CHECKING:
    from typing import Literal


@pytest.mark.parametrize("filename", ["7zip.png", "ffox.png", "gimp.png"])
@pytest.mark.parametrize("output_format", ["json", "yaml"])
def test_image_descriptor_has_no_resource_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    filename: str,
    output_format: Literal["json", "yaml"],
) -> None:
    """Generic images omit the unsupported v2 resource type in every export."""
    data_dir = Path(__file__).resolve().parent.parent / "data"
    monkeypatch.chdir(data_dir)
    image_path = Path(filename)
    resource = ResourceAdapter.from_path(image_path)
    assert resource.type == "file"
    write_package(Package(resources=[resource]), tmp_path, output_format)
    text = (tmp_path / f"datapackage.{output_format}").read_text(encoding="utf-8")
    package = json.loads(text) if output_format == "json" else yaml.safe_load(text)
    descriptor = package["resources"][0]
    assert "type" not in descriptor
    assert descriptor["path"] == filename
    assert descriptor["format"] == "png"
    assert descriptor["mediatype"] == "image/png"
    assert descriptor["bytes"] == image_path.stat().st_size
    # Omitting descriptor metadata must preserve the image reader and validation.
    assert resource.type == "file"
    assert resource.read_file() == image_path.read_bytes()
    assert resource.validate().valid


@pytest.mark.parametrize("output_format", ["json", "yaml"])
def test_package_export_keeps_table_and_json_types(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    output_format: Literal["json", "yaml"],
) -> None:
    """The binary-resource correction does not change other resource kinds."""
    monkeypatch.chdir(Path(__file__).resolve().parent.parent / "data")
    resources = [
        ResourceAdapter.from_path(Path(f)) for f in ("cars.json", "miserables.json")
    ]
    write_package(Package(resources=resources), tmp_path, output_format)
    text = (tmp_path / f"datapackage.{output_format}").read_text(encoding="utf-8")
    package = json.loads(text) if output_format == "json" else yaml.safe_load(text)
    assert [r["type"] for r in package["resources"]] == ["table", "json"]


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
