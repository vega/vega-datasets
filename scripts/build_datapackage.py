# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "frictionless[json,parquet]",
#     "polars",
# ]
# ///
"""
Generates machine-readable metadata, describing the contents of `/data/`_.

Usage
-----
1. Install `uv`_.
2. Run this script from the repo root:

    >>> uv run scripts/build_datapackage.py # doctest: +SKIP

Related
-------
- https://docs.astral.sh/uv/guides/scripts/#declaring-script-dependencies
- https://packaging.python.org/en/latest/specifications/inline-script-metadata/#inline-script-metadata
- https://github.com/vega/vega-datasets/issues/629#issuecomment-2498618622
- https://datapackage.org/
- https://docs.pola.rs/


.. _/data/:
    https://github.com/vega/vega-datasets/tree/main/data
.. _uv:
    https://docs.astral.sh/uv/getting-started/installation/
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import warnings
from collections.abc import Mapping
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, NotRequired, Required, TypedDict

import polars as pl
from frictionless.resources import (
    JsonResource,
    MapResource,
    Package,
    Resource,
    TableResource,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from typing import Literal


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

type ResourceConstructor = Callable[..., Resource]

TopoResource: ResourceConstructor = partial(
    MapResource, format="topojson", datatype="map"
)
GeoResource: ResourceConstructor = partial(
    MapResource, format="geojson", datatype="map"
)

SUFFIX_IMAGE: set[str] = {".png"}
SUFFIX_TABULAR_SAFE: set[str] = {".csv", ".tsv", ".parquet"}
SUFFIX_JSON: Literal[".json"] = ".json"
SUFFIX_UNSUPPORTED: set[Literal[".arrow"]] = {".arrow"}


class Source(TypedDict, total=False):
    title: str
    path: Required[str]
    email: str
    version: str


class License(TypedDict):
    name: str
    path: str
    title: NotRequired[str]


class Contributor(TypedDict, total=False):
    title: str
    givenName: str
    familyName: str
    path: str
    email: str
    roles: Sequence[str]
    organization: str


class ResourceMeta(TypedDict, total=False):
    description: str
    sources: Sequence[Source]
    licenses: Sequence[License]


class PackageMeta(TypedDict):
    """
    A subset of the `Data Package`_ standard.

    .. _Data Package:
        https://datapackage.org/standard/data-package/#properties
    """

    name: str
    version: str
    homepage: str
    description: str
    licenses: Sequence[License]
    contributors: Sequence[Contributor]
    sources: Sequence[Source]
    created: str


def extract_package_metadata(repo_root: Path, /) -> PackageMeta:
    """Repurpose `package.json`_ for the `Data Package`_ standard.

    .. _package.json:
        https://github.com/vega/vega-datasets/blob/main/package.json
    .. _Data Package:
        https://datapackage.org/standard/data-package/#properties
    """
    fp: Path = repo_root / "package.json"
    with fp.open(encoding="utf-8") as f:
        m = json.load(f)
    if not isinstance(m, Mapping):
        msg = f"Unexpected type returned from {fp!r}\n{type(m).__name__!r}"
        raise TypeError(msg)
    return PackageMeta(
        name=m["name"],
        version=m["version"],
        homepage=m["repository"]["url"],
        description=m["description"],
        licenses=[
            License(
                name=m["license"],
                path="https://opensource.org/license/bsd-3-clause",
                title="The 3-Clause BSD License",
            )
        ],
        sources=[
            Source(path="https://github.com/vega/vega-datasets/blob/next/SOURCES.md")
        ],
        created=dt.datetime.now(dt.UTC).isoformat(),
    )


def infer_json_constructor(source: Path, /) -> ResourceConstructor:
    """Identifies *non-tabular* files, adds basic tag for spatial data."""
    df: pl.DataFrame = pl.read_json(source)
    if any(tp.is_nested() for tp in df.schema.dtypes()):
        if df.columns[0] == "type":
            return TopoResource if df.item(0, 0) == "Topology" else GeoResource
        return JsonResource
    return TableResource


def iter_resources(data_root: Path, /) -> Iterator[Resource]:
    """Yield all parseable resources, selecting the most appropriate ``Resource`` class."""
    tp: ResourceConstructor
    for fp in data_root.iterdir():
        suffix: str = fp.suffix
        if not fp.is_file():
            continue
        if suffix in SUFFIX_UNSUPPORTED:
            continue
        elif suffix in SUFFIX_IMAGE:
            tp = Resource
        elif suffix in SUFFIX_TABULAR_SAFE:
            tp = TableResource
        elif suffix == SUFFIX_JSON:
            tp = infer_json_constructor(fp)
        else:
            msg = f"Skipping unexpected extension {suffix!r}\n\n{fp!r}"
            warnings.warn(msg, stacklevel=2)
            continue
        yield tp(fp.name)


def main(
    *,
    stem: str = "datapackage",
    output_format: Literal["json", "yaml", "both"] = "both",
) -> None:
    if output_format not in {"json", "yaml", "both"}:
        msg = f"Expected one of {["json", "yaml", "both"]!r} but got {output_format!r}"
        raise TypeError(msg)
    repo_dir: Path = Path(__file__).parent.parent
    data_dir: Path = repo_dir / "data"
    # NOTE: Forcing base directory here
    # - Ensures ``frictionless`` doesn't insert platform-specific path separator(s)
    os.chdir(data_dir)
    pkg_meta = extract_package_metadata(repo_dir)

    logger.info(
        f"Collecting resources for '{pkg_meta['name']}@{pkg_meta['version']}' ..."
    )
    pkg = Package(resources=list(iter_resources(data_dir)), **pkg_meta)
    logger.info(f"Collected {len(pkg.resources)} resources")
    logger.info("Inferring metadata ...")
    pkg.infer()
    if output_format in {"json", "both"}:
        p = (repo_dir / f"{stem}.json").as_posix()
        logger.info(f"Writing {p!r}")
        pkg.to_json(p)
    if output_format in {"yaml", "both"}:
        p = (repo_dir / f"{stem}.yaml").as_posix()
        logger.info(f"Writing {p!r}")
        pkg.to_yaml(p)


if __name__ == "__main__":
    main()
