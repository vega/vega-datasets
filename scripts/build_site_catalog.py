#!/usr/bin/env -S uv run --group site
"""
Build the website's catalog (``site/generated``) and thumbnails (``site/public/thumbs``).

Everything describing the data comes from this checkout, so the site always
matches the commit it was built from:

- ``datapackage.json``: descriptions, schemas, licenses and sources;
- ``data/``: the files themselves, profiled field by field;
- ``data/gallery-examples.json``: which gallery examples use which dataset.

Three things are fetched, because they live upstream:

- example thumbnails: Vega and Vega-Lite from the commits the registry
  records, Altair from its docs site;
- whether each Vega and Vega-Lite example has a Vega Editor route yet
  (the Editor only carries examples from the latest *release*);
- the file list of the latest vega-datasets release on npm, so a file that
  hasn't been released yet links to GitHub Pages instead of a CDN 404.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import re
import subprocess
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Literal, cast

import httpx
import polars as pl
from PIL import Image

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
DEFAULT_OUT: Final = REPO_ROOT / "site" / "generated"
DEFAULT_THUMBS: Final = REPO_ROOT / "site" / "public" / "thumbs"
DEFAULT_CACHE: Final = REPO_ROOT / "site" / ".cache"

PAGES_BASE: Final = "https://vega.github.io/vega-datasets/"
EDITOR: Final = "https://vega.github.io/editor/"
THUMB_WIDTH: Final = 480
PREVIEW_ROWS: Final = 6
HIST_BINS: Final = 24
TOP_VALUES: Final = 6
MAX_CELL: Final = 48

# jsDelivr edges emit 403 spuriously under bursts; see generate_gallery_examples.py.
_TRANSIENT: Final = frozenset({403, 429, 500, 502, 503, 504})
_ATTEMPTS: Final = 4

Gallery = Literal["vega", "vega-lite", "altair"]


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------


def request(
    client: httpx.Client, method: str, url: str, *, missing_ok: bool = False
) -> httpx.Response | None:
    """
    Fetch ``url``, retrying transient failures.

    Returns ``None`` for a 404 when ``missing_ok``; any other failure raises, so
    a flaky upstream fails the build instead of silently dropping content.
    """
    for attempt in range(_ATTEMPTS):
        try:
            response = client.request(method, url)
        except httpx.TransportError:
            if attempt == _ATTEMPTS - 1:
                raise
        else:
            if response.status_code == 200:
                return response
            if response.status_code == 404 and missing_ok:
                return None
            if response.status_code not in _TRANSIENT or attempt == _ATTEMPTS - 1:
                response.raise_for_status()
                msg = f"Unexpected HTTP {response.status_code} for {url}"
                raise RuntimeError(msg)
        time.sleep(2**attempt)
    msg = f"Could not fetch {url}"
    raise RuntimeError(msg)


def parallel[T, R](fn: Callable[[T], R], items: list[T]) -> list[R]:
    with ThreadPoolExecutor(max_workers=12) as pool:
        return list(pool.map(fn, items))


# ---------------------------------------------------------------------------
# Examples
# ---------------------------------------------------------------------------


def example_slug(example_url: str) -> str:
    return example_url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".html")


def thumbnail_urls(gallery: Gallery, slug: str, spec_url: str) -> list[str]:
    """
    Candidate thumbnail URLs, in the order to try them.

    Vega and Vega-Lite keep thumbnails in their repositories, so they come from
    the same commit as the registry's ``spec_url``. Read the raw GitHub files:
    jsDelivr can cache burst-related 403s, as generate_gallery_examples.py also
    documents. Altair only publishes them on its docs site: a PNG per example,
    except a few drawn as SVG.
    """
    if gallery == "altair":
        base = f"https://altair-viz.github.io/_static/{slug}-thumb"
        return [f"{base}.png", f"{base}.svg"]
    repo = spec_url.split("/examples/", 1)[0].rsplit("/docs", 1)[0]
    repo = repo.replace(
        "https://cdn.jsdelivr.net/gh/", "https://raw.githubusercontent.com/", 1
    ).replace("@", "/", 1)
    folder = "docs/examples/img" if gallery == "vega" else "examples/compiled"
    return [f"{repo}/{folder}/{slug}.png"]


def editor_spec_url(gallery: Gallery, slug: str) -> str | None:
    """The file behind an Editor example route, or ``None`` for Altair (no routes)."""
    ext = {"vega": "vg", "vega-lite": "vl"}.get(gallery)
    return f"{EDITOR}spec/{gallery}/{slug}.{ext}.json" if ext else None


def write_thumbnail(
    raw: bytes, suffix: str, dest_stem: Path
) -> tuple[str, list[int] | None]:
    """
    Write a web-sized thumbnail and return its file name and pixel size.

    PNGs are flattened onto white (they read on dark cards too) and resized to
    WebP. SVGs are kept as they are; they're only ever shown through ``<img>``.
    """
    dest_stem.parent.mkdir(parents=True, exist_ok=True)
    if suffix == ".svg":
        dest = dest_stem.with_suffix(".svg")
        dest.write_bytes(raw)
        return dest.name, None
    with Image.open(BytesIO(raw)) as im:
        rgba = im.convert("RGBA")
    flat = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    flat.alpha_composite(rgba)
    out = flat.convert("RGB")
    if out.width > THUMB_WIDTH:
        height = round(out.height * THUMB_WIDTH / out.width)
        out = out.resize((THUMB_WIDTH, height), Image.Resampling.LANCZOS)
    dest = dest_stem.with_suffix(".webp")
    out.save(dest, "WEBP", quality=78, method=6)
    return dest.name, [out.width, out.height]


def fetch_cached(client: httpx.Client, url: str, cache: Path | None) -> bytes | None:
    """Download ``url`` (``None`` on 404), reusing a local copy when a cache is given."""
    path = (
        cache / re.sub(r"[^A-Za-z0-9._-]", "_", url.split("://", 1)[1])
        if cache
        else None
    )
    if path and path.exists():
        return path.read_bytes()
    response = request(client, "GET", url, missing_ok=True)
    if response is None:
        return None
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(response.content)
    return response.content


def build_examples(
    client: httpx.Client, thumbs: Path, cache: Path | None
) -> list[dict[str, Any]]:
    registry = json.loads(
        (REPO_ROOT / "data" / "gallery-examples.json").read_text("utf-8")
    )

    def one(record: dict[str, Any]) -> dict[str, Any]:
        gallery: Gallery = record["gallery_name"]
        slug = example_slug(record["example_url"])
        thumb = size = None
        for url in thumbnail_urls(gallery, slug, record["spec_url"]):
            raw = fetch_cached(client, url, cache)
            if raw is not None:
                name, size = write_thumbnail(
                    raw, Path(url).suffix, thumbs / gallery / slug
                )
                thumb = f"thumbs/{gallery}/{name}"
                break
        editor = None
        spec = editor_spec_url(gallery, slug)
        if spec and request(client, "HEAD", spec, missing_ok=True) is not None:
            editor = f"{EDITOR}#/examples/{gallery}/{slug}"
        return {
            "id": f"{gallery}/{slug}",
            "gallery": gallery,
            "slug": slug,
            "name": record["example_name"],
            "url": record["example_url"],
            "source": record["spec_url"],
            "categories": record["categories"],
            "description": record["description"],
            "datasets": record["datasets"],
            "thumb": thumb,
            "thumbSize": size,
            "editor": editor,
        }

    examples = parallel(one, registry)
    if missing := [e["id"] for e in examples if not e["thumb"]]:
        logger.warning(
            "No thumbnail upstream for %d examples: %s", len(missing), missing
        )
    if no_route := [
        e["id"] for e in examples if e["gallery"] != "altair" and not e["editor"]
    ]:
        logger.info("Not in the Vega Editor yet (link dropped): %s", no_route)
    examples.sort(key=lambda e: (e["gallery"], e["name"].lower()))
    return examples


# ---------------------------------------------------------------------------
# Dataset profiles
# ---------------------------------------------------------------------------


def _cell(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list | dict):
        return json.dumps(value)
    return str(value)


def read_table(
    path: Path, fmt: str, *, keep_empty: bool = False
) -> pl.DataFrame | None:
    """
    Read a tabular resource. CSV and JSON load as strings; the schema decides types.

    An empty CSV or TSV cell reads as null, unless ``keep_empty`` (a schema that
    declares ``missingValues`` decides for itself whether empty text is missing).
    """
    if fmt in {"csv", "tsv"}:
        return pl.read_csv(
            path,
            separator="\t" if fmt == "tsv" else ",",
            infer_schema=False,
            truncate_ragged_lines=True,
            missing_utf8_is_empty_string=keep_empty,
        )
    if fmt == "parquet":
        return pl.read_parquet(path)
    if fmt == "arrow":
        return pl.read_ipc(path)
    if fmt == "json":
        rows = json.loads(path.read_text("utf-8"))
        if not (isinstance(rows, list) and rows and isinstance(rows[0], dict)):
            return None
        columns = list(dict.fromkeys(k for row in rows for k in row))
        return pl.DataFrame(
            {c: [_cell(row.get(c)) for row in rows] for c in columns},
            schema=dict.fromkeys(columns, pl.String),
        )
    return None


_DATE_FORMATS: Final = (
    "%Y-%m-%d",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y/%m/%d",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%m/%d/%Y",
    "%m/%d/%Y %H:%M",
    "%b %d %Y",
    "%d-%b-%y",
    "%b %d, %Y",
    "%Y-%m",
    "%Y",
)


def parse_dates(s: pl.Series) -> pl.Series:
    """Parse with whichever known format fits the most values (the files mix conventions)."""
    best = pl.Series(s.name, [None] * s.len(), dtype=pl.Datetime)
    for fmt in (None, *_DATE_FORMATS):
        try:
            candidate = s.str.to_datetime(fmt, strict=False)
        except pl.exceptions.ComputeError:
            continue
        if candidate.null_count() < best.null_count():
            best = candidate
    return best


def _nice(x: float) -> float:
    return float(f"{x:.4g}")


def _utc_iso(t: datetime) -> str:
    """
    ISO 8601 with an explicit zone.

    A value without one is the file's own wall-clock time; marking it UTC keeps
    browsers from reading it as the viewer's local time (a day early east of UTC).
    """
    return t.isoformat() if t.tzinfo else f"{t.isoformat()}Z"


def _bins(offsets: pl.Series, span: float) -> list[int]:
    idx = (offsets / (span / HIST_BINS)).floor().clip(0, HIST_BINS - 1).cast(pl.Int32)
    counts = Counter(idx.to_list())
    return [counts.get(i, 0) for i in range(HIST_BINS)]


def missing_values(spec: list[Any] | None) -> list[str]:
    """
    The values a Table Schema ``missingValues`` list marks as missing.

    Items are strings, or ``{value, label}`` objects (Table Schema v2).
    """
    return [str(m["value"] if isinstance(m, dict) else m) for m in spec or []]


def without_missing(s: pl.Series, values: list[str]) -> pl.Series:
    """``s`` with the cells whose text is one of ``values`` set to null (its type kept)."""
    mask = s.cast(pl.String, strict=False).is_in(values).fill_null(value=False)
    return s.zip_with(~mask, pl.Series(s.name, [None] * s.len(), dtype=s.dtype))


def profile_field(
    s: pl.Series, field_type: str, markers: list[str] | None = None
) -> dict[str, Any]:
    """
    Summarize one column for the website.

    Numbers and dates get range and a histogram; everything else (strings,
    booleans, lists) gets its most common values. Nulls count as missing, and
    so do the documented missing-value ``markers``; without a list, Table Schema's
    default (empty text) applies. An explicit list replaces it, so with ``[]``
    empty text is a value.
    """
    if markers:
        s = without_missing(s, markers)
    n = s.len()
    if field_type in {"integer", "number"}:
        num = s.cast(pl.Float64, strict=False)
        num = num.filter(num.is_not_null() & num.is_finite())
        missing = n - num.len()
        if num.len() == 0:
            return {"kind": "empty", "missing": missing}
        lo, hi = cast("float", num.min()), cast("float", num.max())
        return {
            "kind": "quantitative",
            "min": _nice(lo),
            "max": _nice(hi),
            "mean": _nice(cast("float", num.mean())),
            "missing": missing,
            "bins": _bins(num - lo, hi - lo) if hi > lo else [num.len()],
        }
    if field_type in {"date", "datetime"}:
        if s.dtype == pl.Date or isinstance(s.dtype, pl.Datetime):
            dt = s.cast(pl.Datetime)
        else:
            dt = parse_dates(s.cast(pl.String).str.strip_chars())
        valid = dt.drop_nulls()
        missing = n - valid.len()
        if valid.len() == 0:
            return {"kind": "empty", "missing": missing}
        lo, hi = cast("datetime", valid.min()), cast("datetime", valid.max())
        span = (hi - lo).total_seconds()
        profile: dict[str, Any] = {
            "kind": "temporal",
            "min": _utc_iso(lo),
            "max": _utc_iso(hi),
            "missing": missing,
        }
        if span > 0:
            profile["bins"] = _bins((valid - lo).dt.total_seconds(), span)
        return profile
    text = s.cast(pl.String, strict=False).drop_nulls()
    if markers is None:
        text = text.filter(text.str.len_chars() > 0)
    # Break count ties by value so rebuilds produce the same catalog.
    counts = text.value_counts(name="n").sort(
        ["n", text.name], descending=[True, False]
    )
    return {
        "kind": "nominal",
        "distinct": counts.height,
        "top": [[str(v), int(c)] for v, c in counts.head(TOP_VALUES).iter_rows()],
        "missing": n - text.len(),
    }


def preview_rows(df: pl.DataFrame, columns: list[str]) -> list[list[str]]:
    rows = []
    for row in df.head(PREVIEW_ROWS).iter_rows(named=True):
        cells = []
        for column in columns:
            value = row.get(column)
            if value is None:
                text = ""
            elif isinstance(value, date):
                text = value.isoformat()
            else:
                text = str(value)
            cells.append(text if len(text) <= MAX_CELL else f"{text[: MAX_CELL - 1]}…")
        rows.append(cells)
    return rows


def released_files(client: httpx.Client, major: str) -> set[str]:
    """
    Paths under ``data/`` in the release that ``vega-datasets@{major}`` serves.

    Resolving the range through jsDelivr (rather than reading package.json)
    lists exactly what the CDN links point at, even mid-release.
    """
    api = "https://data.jsdelivr.com/v1/packages/npm/vega-datasets"
    resolved = request(client, "GET", f"{api}/resolved?specifier={major}")
    assert resolved is not None
    version = resolved.json()["version"]
    response = request(client, "GET", f"{api}@{version}?structure=flat")
    assert response is not None
    return {
        f["name"].removeprefix("/data/")
        for f in response.json()["files"]
        if f["name"].startswith("/data/")
    }


def data_url(file: str, major: str, released: set[str]) -> str:
    """
    Where people should load a file from.

    jsDelivr with a pinned major version is what the README recommends; a file
    added since the last release is only on GitHub Pages until the next one.
    """
    if file in released:
        return f"https://cdn.jsdelivr.net/npm/vega-datasets@{major}/data/{file}"
    return f"{PAGES_BASE}data/{file}"


def geo_features(doc: dict[str, Any], fmt: str) -> dict[str, Any]:
    """
    How many shapes a geographic file holds, for the site's map rule (heavy maps open on a picture).

    TopoJSON: the object names, and the features each one becomes (a GeometryCollection's
    geometries, else one). GeoJSON: the FeatureCollection's features.
    """
    if fmt == "geojson":
        features = doc.get("features")
        return {"features": len(features) if isinstance(features, list) else 1}
    objects: dict[str, Any] = doc.get("objects", {})
    counts = {
        name: len(obj.get("geometries", []))
        if obj.get("type") == "GeometryCollection"
        else 1
        for name, obj in objects.items()
    }
    return {"objects": list(objects), "objectFeatures": counts}


# Standard Data Package and Table Schema properties the site shows when they are
# filled in. Each is copied only when present, so an undescribed dataset's entry
# stays exactly as it was.
FIELD_PROPERTIES: Final = (
    "title",
    "categories",
    "categoriesOrdered",
    "constraints",
    "format",
    "missingValues",
)
SCHEMA_PROPERTIES: Final = ("primaryKey", "foreignKeys", "missingValues")


def _present(d: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {k: d[k] for k in keys if k in d}


def build_dataset(
    resource: dict[str, Any], used_by: list[str], url: str, thumbs: Path
) -> dict[str, Any]:
    fmt = resource["format"].lstrip(".")
    path = REPO_ROOT / "data" / resource["path"]
    entry: dict[str, Any] = {
        "name": resource["name"],
        **_present(resource, ("title",)),
        "file": resource["path"],
        "url": url,
        "format": fmt,
        "kind": resource["type"],
        "bytes": resource.get("bytes"),
        "description": resource.get("description", ""),
        "licenses": resource.get("licenses", []),
        "sources": resource.get("sources", []),
        "usedBy": used_by,
        "fields": [],
        "rows": None,
        "preview": None,
    }
    if fmt in {"topojson", "geojson"}:
        entry.update(geo_features(json.loads(path.read_text("utf-8")), fmt))
    if fmt == "png":
        name, _ = write_thumbnail(
            path.read_bytes(), ".png", thumbs / "data" / resource["name"]
        )
        entry["image"] = f"thumbs/data/{name}"
    schema = resource.get("schema") or {}
    declared = "missingValues" in schema or any(
        "missingValues" in f for f in schema.get("fields") or []
    )
    df = (
        read_table(path, fmt, keep_empty=declared)
        if resource["type"] == "table"
        else None
    )
    if df is None:
        return entry
    fields = schema.get("fields")
    if not fields:
        # No declared schema: the columns stand in, marked so the site doesn't ask for
        # descriptions of fields the metadata never named (only then: no key otherwise).
        fields = [{"name": c, "type": "string"} for c in df.columns]
        entry["fieldsInferred"] = True
    for field in fields:
        if field["name"] not in df.columns:
            continue
        # A field's own missingValues replace the schema's (Table Schema v2);
        # neither leaves the default (None: empty text is missing).
        spec = field.get("missingValues", schema.get("missingValues"))
        missing = None if spec is None else missing_values(spec)
        entry["fields"].append({
            "name": field["name"],
            "type": field.get("type", "string"),
            "description": field.get("description"),
            **_present(field, FIELD_PROPERTIES),
            "profile": profile_field(
                df[field["name"]], field.get("type", "string"), missing
            ),
        })
    entry.update(_present(schema, SCHEMA_PROPERTIES))
    columns = [f["name"] for f in entry["fields"]]
    entry["rows"] = df.height
    entry["preview"] = {"columns": columns, "rows": preview_rows(df, columns)}
    return entry


# ---------------------------------------------------------------------------
# README (the site's home page)
# ---------------------------------------------------------------------------

REPO_BLOB: Final = "https://github.com/vega/vega-datasets/blob/main/"
_RELATIVE_LINK: Final = re.compile(r"\]\((?!https?:|mailto:|#)([^)\s]+)\)")


def readme_markdown(text: str, resource_paths: dict[str, str]) -> str:
    """
    Adapt README.md for the home page.

    Drops the title and the badge row (the page has its own heading, and its
    CSP only loads same-origin images), turns GitHub's ``[!IMPORTANT]`` marker
    into a plain note, points links to a dataset's ``datapackage.md`` entry at
    that dataset's page (``datasets/<name>/``, relative to the home page, where the
    sections are shown) and links to the site itself at the home page, and sends
    other relative links to GitHub.

    ``resource_paths`` maps each resource's file path to its name.
    """
    # datapackage.md anchors are GitHub's heading slugs of the file paths.
    anchors = {
        re.sub(r"[^a-z0-9_-]", "", p.lower()): n for p, n in resource_paths.items()
    }
    lines = [
        line
        for line in text.splitlines()
        if not line.startswith(("# ", "[![")) and line.strip() != "> [!IMPORTANT]"
    ]

    def link(m: re.Match[str]) -> str:
        target = m.group(1)
        path, _, anchor = target.partition("#")
        if path == "datapackage.md" and anchor in anchors:
            return f"](datasets/{anchors[anchor]}/)"
        return f"]({REPO_BLOB}{target})"

    def prose(part: str) -> str:
        return _RELATIVE_LINK.sub(link, part).replace(f"]({PAGES_BASE})", "](./)")

    # Rewrite prose only: fenced code (odd-numbered parts) is left as written.
    parts = re.split(
        r"(^```.*?^```$)", "\n".join(lines), flags=re.MULTILINE | re.DOTALL
    )
    text = "".join(part if i % 2 else prose(part) for i, part in enumerate(parts))
    return text.strip() + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def build(
    out: Path, cache: Path | None, thumbs: Path = DEFAULT_THUMBS
) -> dict[str, Any]:
    pkg = json.loads((REPO_ROOT / "datapackage.json").read_text("utf-8"))
    version = json.loads((REPO_ROOT / "package.json").read_text("utf-8"))["version"]
    out.mkdir(parents=True, exist_ok=True)
    major = version.split(".", 1)[0]
    headers = {"User-Agent": "vega-datasets-site-build"}
    with httpx.Client(timeout=30, follow_redirects=True, headers=headers) as client:
        examples = build_examples(client, thumbs, cache)
        released = released_files(client, major)
    used_by: dict[str, list[str]] = defaultdict(list)
    for example in examples:
        for name in example["datasets"]:
            used_by[name].append(example["id"])
    datasets = [
        build_dataset(
            r, used_by[r["name"]], data_url(r["path"], major, released), thumbs
        )
        for r in pkg["resources"]
    ]
    readme = readme_markdown(
        (REPO_ROOT / "README.md").read_text("utf-8"),
        {r["path"]: r["name"] for r in pkg["resources"]},
    )
    catalog = {
        "package": {"name": pkg["name"], "version": version, "commit": git_commit()},
        "readme": readme,
        "datasets": datasets,
        "examples": examples,
    }
    text = json.dumps(
        catalog, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    (out / "catalog.json").write_text(text, "utf-8")
    logger.info(
        "%d datasets, %d examples; catalog.json is %d KB",
        len(datasets),
        len(examples),
        math.ceil(len(text.encode()) / 1024),
    )
    return catalog


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the website's catalog and thumbnails."
    )
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT, help="where catalog.json goes"
    )
    parser.add_argument(
        "--thumbs",
        type=Path,
        default=DEFAULT_THUMBS,
        help="where thumbnails go (served as thumbs/ next to the pages)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help=f"always download thumbnails (default: reuse {DEFAULT_CACHE.relative_to(REPO_ROOT)})",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    build(args.out, None if args.no_cache else DEFAULT_CACHE, args.thumbs)


if __name__ == "__main__":
    main()
