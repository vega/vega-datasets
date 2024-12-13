#!/usr/bin/env -S uv run

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
from collections.abc import Mapping, Sequence
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, NotRequired, Required, TypedDict, Unpack, cast

import frictionless as fl
import polars as pl
from frictionless.fields import (
    AnyField,
    ArrayField,
    BooleanField,
    DateField,
    DatetimeField,
    DurationField,
    IntegerField,
    NumberField,
    ObjectField,
    StringField,
    TimeField,
)
from frictionless.resources import (
    JsonResource,
    MapResource,
    Package,
    Resource,
    TableResource,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from typing import ClassVar, Literal


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

type ResourceConstructor = Callable[..., Resource]
type PathMeta = Literal["name", "path", "scheme", "mediatype"]
type PythonDataType = (
    type[
        int
        | float
        | bool
        | str
        | dict
        | list
        | tuple
        | dt.date
        | dt.datetime
        | dt.time
        | dt.timedelta
        | object
        | bytes
    ]
    | None
)


POLARS_PY_TO_FL_FIELD: Mapping[PythonDataType, type[fl.Field]] = {
    int: IntegerField,
    float: NumberField,
    bool: BooleanField,
    str: StringField,
    None: AnyField,  # NOTE: Unclear why this isn't represented with a class
    dict: ObjectField,
    list: ArrayField,
    tuple: ArrayField,
    dt.date: DateField,
    dt.datetime: DatetimeField,
    dt.time: TimeField,
    dt.timedelta: DurationField,
    object: AnyField,
    bytes: AnyField,
}
"""
Maps `polars python`_ type repr to ``datapackage`` `Field Types`_.


.. _polars python:
    https://github.com/pola-rs/polars/blob/85d078c066860e012f5e7e611558e6382b811b82/py-polars/polars/datatypes/convert.py#L167-L197
.. _Field Types:
    https://datapackage.org/standard/table-schema/#field-types
"""

TopoResource: ResourceConstructor = partial(
    MapResource, format="topojson", datatype="map"
)
GeoResource: ResourceConstructor = partial(
    MapResource, format="geojson", datatype="map"
)


class ResourceAdapter:
    mediatype: ClassVar[Mapping[str, str]] = {
        ".arrow": "application/vnd.apache.arrow.file"
    }
    """https://www.iana.org/assignments/media-types/application/vnd.apache.arrow.file"""

    @classmethod
    def from_path(cls, source: Path, /) -> Resource | None:
        suffix = source.suffix
        match suffix:
            case ".csv" | ".tsv" | ".parquet":
                return cls.from_tabular_safe(source)
            case ".json":
                return cls.from_json(source)
            case ".png":
                return cls.from_image(source)
            case ".arrow":
                return cls.from_arrow(source)
            case _:
                return None

    @classmethod
    def infer_as(cls, source: Path, tp: ResourceConstructor, /) -> Resource:
        resource = tp(source.name, **cls._extract_file_parts(source))
        resource.infer()
        return resource

    @classmethod
    def from_arrow(cls, source: Path, /) -> Resource:
        file_meta = cls._extract_file_parts(source)
        return TableResource(
            **file_meta, format=".arrow", schema=frame_to_schema(pl.scan_ipc(source))
        )

    @classmethod
    def from_tabular_safe(cls, source: Path, /) -> Resource:
        return cls.infer_as(source, TableResource)

    @classmethod
    def from_image(cls, source: Path, /) -> Resource:
        return cls.infer_as(source, Resource)

    @classmethod
    def from_json(cls, source: Path, /) -> Resource:
        """Identifies *non-tabular* files, adds basic tag for spatial data."""
        df: pl.DataFrame = pl.read_json(source)
        if any(tp.is_nested() for tp in df.schema.dtypes()):
            if df.columns[0] == "type":
                tp = TopoResource if df.item(0, 0) == "Topology" else GeoResource
            else:
                tp = JsonResource
        else:
            tp = TableResource
        return cls.infer_as(source, tp)

    @classmethod
    def _extract_file_parts(cls, source: Path, /) -> dict[PathMeta, str]:
        """Metadata that can be inferred from the file path *alone*."""
        parts: dict[PathMeta, str] = {
            "name": source.name.lower(),
            "path": source.name,
            "scheme": "file",
        }
        if mediatype := cls.mediatype.get(source.suffix):
            parts["mediatype"] = mediatype
        return parts

    @staticmethod
    def with_extras(resource: Resource, /, **extras: Unpack[ResourceMeta]) -> Resource:
        """Supplement inferred metadata with manually defined ``extras``."""
        if "schema" in extras:
            resource.schema = merge_schemas(resource, extra=extras.pop("schema"))
        for name, value in extras.items():
            setattr(resource, name, value)
        return resource


def merge_schemas(resource: Resource, *, extra: Schema) -> fl.Schema:
    if schema := resource.schema:
        inferred = _flatten_schema(cast("Schema", schema.to_dict()))
    else:
        return fl.Schema.from_descriptor(cast("dict[str, Any]", extra))
    overrides = _flatten_schema(extra)
    fields = []
    for name, field in inferred.items():
        if name in overrides:
            field.update(overrides[name])
        fields.append(field)
    return fl.Schema.from_descriptor({"fields": fields})


def _flatten_schema(schema: Schema, /) -> dict[str, Field]:
    return {field["name"]: field for field in schema["fields"]}


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


class Field(TypedDict, total=False):
    """https://datapackage.org/standard/table-schema/#field."""

    name: Required[str]
    type: str
    description: str


class Schema(TypedDict):
    """https://datapackage.org/standard/table-schema/#properties."""

    fields: Sequence[Field]


class ResourceMeta(TypedDict, total=False):
    description: str
    sources: Sequence[Source]
    licenses: Sequence[License]
    schema: Schema


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


def frame_to_schema(frame: pl.LazyFrame | pl.DataFrame, /) -> fl.Schema:
    py_schema = frame.lazy().collect_schema().to_python()
    return fl.Schema(
        fields=[POLARS_PY_TO_FL_FIELD[tp](name=name) for name, tp in py_schema.items()]
    )


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
        contributors=[Contributor(title=m["author"]["name"], path=m["author"]["url"])],
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


def extract_overrides(mapping: Mapping[str, Any], /) -> dict[str, ResourceMeta]:
    if (resources := mapping.get("resources")) and isinstance(resources, Sequence):
        return dict(iter_parse_resources(resources))
    else:
        raise TypeError(resources)


def iter_parse_resources(
    seq: Sequence[ResourceMeta], /
) -> Iterator[tuple[str, ResourceMeta]]:
    for resource in seq:
        if (name := resource.get("path")) and isinstance(name, str):
            m: Any = {k: v for k, v in resource.items() if k != "path"}
            # NOTE: Drops entries that only provide `path`
            if m:
                yield name, m
        else:
            raise TypeError(seq)


def iter_data_dir(data_root: Path, /) -> Iterator[Path]:
    """Yield files in the root of the ``/data/`` directory."""
    for fp in sorted(data_root.iterdir()):
        if fp.is_file():
            yield fp


def iter_resources(
    root: Path, /, overrides: dict[str, ResourceMeta]
) -> Iterator[Resource]:
    """
    Yield all parseable resources, constructing with the most appropriate ``Resource`` class.

    Parameters
    ----------
    root
        Directory storing datasets.
    overrides
        Additional metadata, with a higher precedence than inferred.
    """
    for fp in iter_data_dir(root):
        if resource := ResourceAdapter.from_path(fp):
            name = fp.name
            if name in overrides:
                resource = ResourceAdapter.with_extras(resource, **overrides[name])
            yield resource
        else:
            msg = f"Skipping unexpected extension {fp.suffix!r}\n\n{fp!r}"
            warnings.warn(msg, stacklevel=2)
            continue


def read_toml(fp: Path, /) -> Mapping[str, Any]:
    import tomllib

    return tomllib.loads(fp.read_text("utf-8"))


def main(
    *,
    stem: str = "datapackage",
    output_format: Literal["json", "yaml", "both"] = "json",
) -> None:
    if output_format not in {"json", "yaml", "both"}:
        msg = f"Expected one of {["json", "yaml", "both"]!r} but got {output_format!r}"
        raise TypeError(msg)
    repo_dir: Path = Path(__file__).parent.parent
    data_dir: Path = repo_dir / "data"
    sources_toml: Path = repo_dir / "_data" / "datapackage_additions.toml"

    sources = read_toml(sources_toml)
    # NOTE: Package metadata is expected to be stored in `sources` in the future
    overrides = extract_overrides(sources)
    # NOTE: Forcing base directory here
    # - Ensures ``frictionless`` doesn't insert platform-specific path separator(s)
    os.chdir(data_dir)
    pkg_meta = extract_package_metadata(repo_dir)
    logger.info(
        f"Collecting resources for '{pkg_meta['name']}@{pkg_meta['version']}' ..."
    )
    pkg = Package(resources=list(iter_resources(data_dir, overrides)), **pkg_meta)  # type: ignore[arg-type]
    logger.info(f"Collected {len(pkg.resources)} resources")
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
