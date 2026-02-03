#!/usr/bin/env -S uv run

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

import contextlib
import copy
import datetime as dt
import io
import json
import logging
import os
import re
import subprocess as sp
import tomllib
import warnings
from collections.abc import Mapping, Sequence
from functools import partial
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Concatenate,
    LiteralString,
    NotRequired,
    Required,
    TypedDict,
    Unpack,
    cast,
)

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
from frictionless.formats.markdown import mapper as fl_markdown
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
type PackageMethod[**P] = Callable[Concatenate[Package, P], Any]
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

type OutputFormat = Literal["json", "yaml", "md"]
type OneOrSeq[T] = T | Sequence[T]

ADDITIONS_TOML: LiteralString = "datapackage_additions.toml"
NPM_PACKAGE: Literal["package.json"] = "package.json"
DATAPACKAGE: Literal["datapackage"] = "datapackage"

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


def fmt_date(s: str, /) -> str:
    """
    Reformat `package.created` at a lower resolution.

    Use a friendlier date format for markdown.
    """
    datetime = dt.datetime.fromisoformat(s)
    dt_fmt = datetime.replace(tzinfo=None).isoformat(sep=" ", timespec="seconds")
    if tzname := datetime.tzname():
        return f"{dt_fmt} [{tzname}]"
    return dt_fmt


def render_markdown_patch(path: str, data: dict[str, Any]) -> str:
    """
    Patch to `frictionless.formats.markdown.mapper.render_markdown`_ to support template overrides.

    Declare a template with the same name as a default to override it:

        # Override directory:
        vega-datasets/_data/templates/

        # Default directory:
        frictionless/assets/templates/

    .. _frictionless.formats.markdown.mapper.render_markdown:
        https://github.com/frictionlessdata/frictionless-py/blob/6b72909ee38403df7c0245f408f3881bfa56ad6f/frictionless/formats/markdown/mapper.py#L13-L43

    Original doc
    ------------
    Render any JSON-like object as Markdown, using jinja2 template.
    """
    import jinja2  # noqa: PLC0415

    # Create environ
    default_dir: Path = Path(fl_markdown.__file__).parent / "../../assets/templates"
    override_dir: Path = Path(__file__).parent.parent / "_data" / "templates"
    searchpath = override_dir, default_dir
    loader = jinja2.FileSystemLoader(searchpath)
    environ = jinja2.Environment(loader=loader, lstrip_blocks=True, trim_blocks=True)

    # Render data
    environ.filters["filter_dict"] = fl_markdown.filter_dict
    environ.filters["dict_to_markdown"] = fl_markdown.dict_to_markdown
    environ.filters["tabulate"] = fl_markdown.dicts_to_markdown_table
    environ.filters["fmt_date"] = fmt_date
    template = environ.get_template(path)
    return template.render(**data)


fl_markdown.render_markdown = render_markdown_patch


def identify_multi_format_datasets(data_root: Path) -> set[str]:
    """
    Identify dataset base names that have multiple format variants.

    Returns a set of base names (without extensions) that exist in multiple formats.
    """
    base_names: dict[str, list[str]] = {}

    for fp in data_root.iterdir():
        if fp.is_file() and ResourceAdapter.is_supported(fp):
            base = fp.stem
            base_names.setdefault(base, []).append(fp.suffix)

    # Return base names that have multiple formats
    return {base for base, suffixes in base_names.items() if len(suffixes) > 1}


def to_snake_case(name: str) -> str:
    """Converts a string from camelCase to snake_case."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower()


def make_uax31_name(path: Path, multi_format_bases: set[str]) -> str:
    """
    Generate UAX-31 compliant and snake_cased identifier from file path.

    Ensures the name is a valid Python identifier by:
    - Converting the name to snake_case (e.g., 'londonBoroughs' -> 'london_boroughs')
    - Removing file extensions
    - Replacing hyphens with underscores
    - Adding prefixes for names starting with digits
    - Appending format suffixes when multiple formats exist for the same dataset

    Parameters
    ----------
    path : Path
        The file path to convert to a UAX-31 compliant name
    multi_format_bases : set[str]
        Set of base names that exist in multiple formats.

    Returns
    -------
    str
        A valid, snake_cased Python identifier derived from the file path
    """
    # Remove extension
    base_name = path.stem

    # Convert to snake_case (handles camelCase) and replace hyphens
    name = to_snake_case(base_name)
    name = name.replace("-", "_")

    # Handle names starting with digits
    if name and name[0].isdigit():
        # Add appropriate prefix based on file type
        name = f"icon_{name}" if path.suffix in {".png", ".jpg"} else f"data_{name}"

    # If multiple formats exist for this dataset, append format suffix to all
    if base_name in multi_format_bases:
        name = f"{name}_{path.suffix[1:].lower()}"

    # Validate the name is a valid identifier
    assert name.isidentifier(), f"Generated name '{name}' is not a valid identifier"

    return name


class ResourceAdapter:
    mediatype: ClassVar[Mapping[str, str]] = {
        ".arrow": "application/vnd.apache.arrow.file"
    }
    """https://www.iana.org/assignments/media-types/application/vnd.apache.arrow.file"""

    multi_format_bases: ClassVar[set[str]] = set()
    """Base names that exist in multiple formats."""

    @classmethod
    def is_supported(cls, source: Path, /) -> bool:
        return source.suffix in {
            ".csv",
            ".tsv",
            ".json",
            ".parquet",
            ".png",
            ".jpg",
            ".arrow",
        }

    @classmethod
    def from_path(cls, source: Path, /) -> Resource:
        match source.suffix:
            case ".csv" | ".tsv" | ".parquet":
                return cls.from_tabular_safe(source)
            case ".json":
                return cls.from_json(source)
            case ".png" | ".jpg":
                return cls.from_image(source)
            case ".arrow":
                return cls.from_arrow(source)
            case _:
                raise TypeError(source.suffix)

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
    def _extract_file_parts(cls, source: Path, /) -> PathMeta:
        """Metadata that can be inferred from the file path *alone*."""
        parts = PathMeta(
            name=make_uax31_name(source, cls.multi_format_bases),
            path=source.name,
            scheme="file",
            bytes=source.stat().st_size,
        )
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


class PathMeta(TypedDict):
    name: str
    path: str
    scheme: Literal["file"]
    bytes: int
    mediatype: NotRequired[str]


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
    description: NotRequired[str]
    licenses: NotRequired[Sequence[License]]
    contributors: Sequence[Contributor]
    sources: NotRequired[Sequence[Source]]
    created: str


def frame_to_schema(frame: pl.LazyFrame | pl.DataFrame, /) -> fl.Schema:
    py_schema = frame.lazy().collect_schema().to_python()
    return fl.Schema(
        fields=[POLARS_PY_TO_FL_FIELD[tp](name=name) for name, tp in py_schema.items()]
    )


def _extract_npm_metadata(m: Mapping[str, Any], /) -> PackageMeta:
    """
    Repurpose `package.json`_ for the `Data Package`_ standard.

    .. _package.json:
        https://github.com/vega/vega-datasets/blob/main/package.json
    .. _Data Package:
        https://datapackage.org/standard/data-package/#properties
    """
    return PackageMeta(
        name=m["name"],
        version=m["version"],
        homepage=m["repository"]["url"],
        contributors=[Contributor(title=m["author"]["name"], path=m["author"]["url"])],
        created=dt.datetime.now(dt.UTC).isoformat(),
    )


def _merge_package_metadata(
    pkg_meta: PackageMeta, additions: Mapping[str, Any], /
) -> PackageMeta:
    # defined in frictionless spec
    spec_keys = PackageMeta.__optional_keys__.union(PackageMeta.__required_keys__)

    if unknown_keys := set(additions).difference(spec_keys):
        msg = (
            f"`additions` contains keys that are out of spec:\n"
            f"{sorted(unknown_keys)!r}\n\n"
            f"Try updating {PackageMeta.__name__!r} or remove them from {ADDITIONS_TOML!r}"
        )
        raise TypeError(msg)

    additions = dict(copy.deepcopy(additions))

    # relevant from `datapackage_additions.toml`
    incoming_keys = spec_keys.intersection(additions)

    # In both `package.json` & `datapackage_additions.toml`
    overlapping_keys = incoming_keys.intersection(pkg_meta)

    changes = dict[str, Any](copy.deepcopy(pkg_meta))

    # Extract and handle colliding content
    for k in overlapping_keys:
        item = pkg_meta[k]
        extra = additions.pop(k)
        if type(item) is not type(extra):
            msg = (
                f"Mismatched types for overlapping key {k!r}:\n"
                f"Current   : {type(item).__name__!r}, {item!r}\n"
                f"Incoming  : {type(extra).__name__!r}, {extra!r}"
            )
            raise TypeError(msg)
        if isinstance(item, str) or not isinstance(item, Sequence | Mapping):
            msg = f"Overriding overlapping key {k!r}\nCurrent   : {item!r}\nIncoming  : {extra!r}"
            logger.warning(msg, stacklevel=2)
            changes[k] = extra
        elif isinstance(item, Sequence):
            changes[k] = [*item, *extra]
        else:
            msg = (
                f"Expected only lists of mappings or single values, "
                f"but got:{type(item).__name__!r}\n{item!r}\n\n{extra!r}"
            )
            raise NotImplementedError(msg)

    # Remaining are in-spec and only in `datapackage_additions.toml`
    changes |= additions
    return PackageMeta(**changes)


def extract_package_metadata(
    npm: Mapping[str, Any], sources: Mapping[str, Any], /
) -> PackageMeta:
    pkg_meta = _extract_npm_metadata(npm)
    return _merge_package_metadata(pkg_meta, sources)


def extract_overrides(resources: Any, /) -> dict[str, ResourceMeta]:
    if isinstance(resources, Sequence):
        return dict(iter_parse_resources(resources))
    msg = (
        f"Expected `resources` to be an array of tables, but got:"
        f"\n{type(resources).__name__!r}\n\n{resources!r}"
    )
    raise TypeError(msg)


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
    root: Path, /, overrides: dict[str, ResourceMeta], gh_sha1: Mapping[str, str]
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
        if not ResourceAdapter.is_supported(fp):
            msg = f"Skipping unexpected extension {fp.suffix!r}\n\n{fp!r}"
            warnings.warn(msg, stacklevel=2)
            continue
        resource = ResourceAdapter.from_path(fp)
        name = fp.name
        if name in overrides:
            resource = ResourceAdapter.with_extras(resource, **overrides[name])
        resource.hash = gh_sha1[name]
        yield resource


def run_check[T: (str, bytes)](
    args: OneOrSeq[str | Path], /, into: type[T] = str
) -> sp.CompletedProcess[T]:
    """
    Run a command in a `subprocess`_, capturing its output.

    Parameters
    ----------
    args
        Argument(s) that comprise the command.
    into
        Decode (``str``) stdout or keep encoded (``bytes``).

    .. _subprocess:
        https://docs.python.org/3/library/subprocess.html#subprocess.run
    """
    msg = str(args) if isinstance(args, str | Path) else " ".join(str(c) for c in args)
    msg = f"Running command:\n    >>> {msg}"
    logger.info(msg)
    try:
        return sp.run(args, check=True, capture_output=True, text=into is str)
    except sp.CalledProcessError as err:
        out = err.stderr
        msg = f"{err.returncode}: {out.decode() if into is bytes else out}"
        err.add_note(msg)
        raise


def extract_sha(source: str | Path, /) -> Mapping[str, str]:
    """
    Get dataset hashes for the current branch via `ls-files`_.

    Parameters
    ----------
    source
        Directory containing datasets.

    Returns
    -------
    Mapping from `Resource.path`_ to `Resource.hash`_.

    .. _ls-files:
        https://git-scm.com/docs/git-ls-files
    .. _Resource.path:
        https://datapackage.org/standard/data-resource/#path-or-data
    .. _Resource.hash:
        https://datapackage.org/standard/data-resource/#hash
    """
    COLUMNS = "path", "sha"
    SHA = "sha1:%(objectname)"
    PATH = "%(path)"
    CMD_LS_FILES = ("git", "ls-tree", _current_branch(), f"--format={PATH},{SHA}")
    with contextlib.chdir(Path(source)):
        buf = io.BytesIO(run_check(CMD_LS_FILES, into=bytes).stdout)
    return dict(pl.read_csv(buf, has_header=False, new_columns=COLUMNS).iter_rows())


def _current_branch(*, ci_env_var: str = "GITHUB_SHA") -> str:
    """Uses ``ci_env_var`` when run in a GitHub Action."""
    CMD = "git", "branch", "--show-current"
    return os.environ.get(ci_env_var) or run_check(CMD).stdout.rstrip()


def read_toml(fp: Path, /) -> dict[str, Any]:
    return tomllib.loads(fp.read_text("utf-8"))


def read_json(fp: Path, /) -> Any:
    with fp.open(encoding="utf-8") as f:
        return json.load(f)


def write_package(pkg: Package, repo_dir: Path, *formats: OutputFormat) -> None:
    """Write the final datapackage in one or more formats."""
    configs: dict[OutputFormat, tuple[str, PackageMethod[str]]] = {
        "json": (".json", partial(Package.to_json)),
        "yaml": (".yaml", partial(Package.to_yaml)),
        "md": (".md", partial(Package.to_markdown, table=True)),
    }
    for fmt in formats:
        postfix, fn = configs[fmt]
        p = (repo_dir / f"{DATAPACKAGE}{postfix}").as_posix()
        msg = f"Writing {p!r}"
        logger.info(msg)
        fn(pkg, p)


def write_string_overrides_ts(pkg: Package, repo_dir: Path) -> None:
    """Generate src/stringOverrides.ts listing fields that should remain strings."""
    string_fields_by_csv: dict[str, list[str]] = {}

    for resource in pkg.resources:
        if resource.path.endswith(".csv") and resource.schema:
            string_fields = [
                f.name for f in resource.schema.fields if f.type == "string"
            ]
            if string_fields:
                string_fields_by_csv[resource.path] = string_fields

    ts_path = repo_dir / "src" / "stringOverrides.ts"
    with ts_path.open("w", encoding="utf-8") as f:
        f.write(
            f"export default {json.dumps(string_fields_by_csv, indent=2)} as Record<string, string[]>;\n"
        )

    logger.info("Wrote string overrides to %s", ts_path)


def main(
    *,
    output_format: Literal["json", "yaml"] = "json",
) -> None:
    if output_format not in {"json", "yaml"}:
        msg = f"Expected one of {['json', 'yaml']!r} but got {output_format!r}"
        raise TypeError(msg)
    repo_dir: Path = Path(__file__).parent.parent
    data_dir: Path = repo_dir / "data"
    sources_toml: Path = repo_dir / "_data" / ADDITIONS_TOML
    npm_json = repo_dir / NPM_PACKAGE

    npm_package = read_json(npm_json)
    sources = read_toml(sources_toml)
    overrides = extract_overrides(sources.pop("resources"))
    # NOTE: Forcing base directory here
    # - Ensures ``frictionless`` doesn't insert platform-specific path separator(s)
    os.chdir(data_dir)

    # Identify datasets with multiple formats
    ResourceAdapter.multi_format_bases = identify_multi_format_datasets(data_dir)

    pkg_meta = extract_package_metadata(npm_package, sources)
    gh_sha1 = extract_sha(data_dir)
    msg = f"Collecting resources for '{pkg_meta['name']}@{pkg_meta['version']}' ..."
    logger.info(msg)
    pkg = Package(
        resources=list(iter_resources(data_dir, overrides, gh_sha1)),
        **pkg_meta,  # type: ignore[arg-type]
    )
    msg = f"Collected {len(pkg.resources)} resources"
    logger.info(msg)
    DEBUG_MARKDOWN = ("md",)
    write_package(pkg, repo_dir, output_format, *DEBUG_MARKDOWN)
    write_string_overrides_ts(pkg, repo_dir)


if __name__ == "__main__":
    main()
