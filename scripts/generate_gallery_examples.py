#!/usr/bin/env -S uv run
"""Generate gallery-examples.json from Vega ecosystem galleries."""

from __future__ import annotations

import asyncio
import json
import logging
import operator
import tomllib
from collections import Counter
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final, Literal, NamedTuple, TypedDict

import httpx

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
_CLIENT_TIMEOUT: Final = 30
_ENRICH_CONCURRENCY: Final = 20

# HTTP statuses treated as transient for the jsDelivr → raw.githubusercontent
# mirror retry in _get_checked. 403 is included deliberately: jsDelivr edges
# emit it spuriously under concurrent bursts (and cache it for 60 s).
_TRANSIENT_STATUSES: Final = frozenset({403, 429, 500, 502, 503, 504})


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class Example(TypedDict):
    """
    Intermediate gallery-example record carried through build + enrichment.

    ``example_name`` is ``str | None`` during Vega-Lite construction: an entry
    without a real upstream title in any section gets a slug-humanized fallback
    before output. Altair records arrive fully populated from its published
    examples index.
    """

    gallery_name: Literal["vega", "vega-lite", "altair"]
    example_name: str | None
    example_url: str
    spec_url: str
    categories: list[str]
    description: str | None
    datasets: list[str]


class ResolvedRef(TypedDict):
    commit: str


class Config(TypedDict):
    """
    Parsed _data/gallery-examples.toml.

    TypedDict (not NamedTuple) so callers can keep using ``config["refs"]``
    / ``config["sources"]``.
    """

    refs: dict[str, str]
    sources: dict[str, str]


class FetchedIndexes(NamedTuple):
    vl_index: dict[str, Any]
    vega_index: dict[str, Any]
    altair_index: dict[str, Any]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Per-gallery URL conventions, kept in one table so the URL shapes are
# reviewable side by side. NOTE: adding a gallery is more than an entry
# here — it also touches _format_refs, fetch_indexes, build_example_list,
# _SPEC_EXTRACTORS/enrich_one, and _MIN_EXPECTED_PER_GALLERY. `spec` and the
# Vega/Vega-Lite `example_page` values use str.format placeholders;
# jsDelivr spec URLs pin an immutable commit SHA so the CDN caches with
# 100 % hit rate and zero invalidation risk. See also the TOML read-path
# strategy in _data/gallery-examples.toml.
_GALLERIES: Final[tuple[str, ...]] = ("vega-lite", "vega", "altair")
_GALLERY_URLS: Final[Mapping[str, Mapping[str, str]]] = MappingProxyType({
    "vega-lite": MappingProxyType({
        "repo": "vega/vega-lite",
        "example_page": "https://vega.github.io/vega-lite/examples/{slug}.html",
        "spec": "https://cdn.jsdelivr.net/gh/vega/vega-lite@{sha}/examples/specs/{slug}.vl.json",
    }),
    "vega": MappingProxyType({
        "repo": "vega/vega",
        "example_page": "https://vega.github.io/vega/examples/{slug}/",
        "spec": "https://cdn.jsdelivr.net/gh/vega/vega@{sha}/docs/examples/{slug}.vg.json",
    }),
    "altair": MappingProxyType({
        "repo": "vega/altair",
        "spec": "https://cdn.jsdelivr.net/gh/vega/altair@{sha}/{path}",
    }),
})

# URL prefixes that indicate a vega-datasets reference. Trailing `/` prevents
# false-positive matches against sibling packages like `vega-datasets-extra`.
_VEGA_DATASETS_PREFIXES: Final[tuple[str, ...]] = (
    "https://cdn.jsdelivr.net/npm/vega-datasets/",
    "https://cdn.jsdelivr.net/npm/vega-datasets@",
    "https://raw.githubusercontent.com/vega/vega-datasets/",
    "https://vega.github.io/vega-datasets/",
)


# ---------------------------------------------------------------------------
# Dataset reference normalization + extraction
# ---------------------------------------------------------------------------


def normalize_dataset_reference(ref: str, name_map: dict[str, str]) -> str | None:
    """
    Canonicalize a dataset reference to a datapackage resource name.

    Returns the canonical name, or None if the reference is external
    (not a vega-datasets URL). Raises ValueError if the reference
    looks like a vega-datasets URL but can't be resolved.
    """
    if not isinstance(ref, str):
        return None

    # Single pass: identify the vega-datasets prefix and rewrite to a
    # `data/…` path in one scan (was two passes in .v2).
    path = ref
    is_vega_datasets = False
    for prefix in _VEGA_DATASETS_PREFIXES:
        if ref.startswith(prefix):
            is_vega_datasets = True
            idx = ref.find("/data/", len(prefix.rstrip("/")))
            if idx != -1:
                path = "data/" + ref[idx + len("/data/") :]
            break

    # Direct lookup
    if path in name_map:
        return name_map[path]

    # Try with data/ prefix if not already present
    if not path.startswith("data/") and f"data/{path}" in name_map:
        return name_map[f"data/{path}"]

    # Try kebab-case to snake_case conversion
    snake_path = path.replace("-", "_")
    if snake_path in name_map:
        return name_map[snake_path]
    if not snake_path.startswith("data/") and f"data/{snake_path}" in name_map:
        return name_map[f"data/{snake_path}"]

    # Unresolved
    if is_vega_datasets:
        msg = f"Unresolved vega-datasets reference: {ref}"
        raise ValueError(msg)

    return None


def _append_ref(datasets: list[str], url: Any, name_map: dict[str, str]) -> None:
    """
    Resolve ``url`` and append the canonical name to ``datasets`` if it resolves.

    Accepts Any for ``url`` so call sites don't need isinstance-guard
    boilerplate before calling; normalize_dataset_reference returns None
    for non-strings.
    """
    if (ref := normalize_dataset_reference(url, name_map)) is not None:
        datasets.append(ref)


def _inline_value_refs(values: Any, name_map: dict[str, str]) -> list[str]:
    """Extract dataset paths embedded anywhere beneath inline ``data.values``."""
    datasets: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, str):
            if value.startswith(("data/", *_VEGA_DATASETS_PREFIXES)):
                _append_ref(datasets, value, name_map)
        elif isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(values)
    return datasets


def _vegalite_lookup_refs(spec: dict[str, Any], name_map: dict[str, str]) -> list[str]:
    """Extract dataset refs from Vega-Lite transform lookup nodes."""
    datasets: list[str] = []
    for transform in spec.get("transform") or []:
        if not (isinstance(transform, dict) and "lookup" in transform):
            continue
        from_field = transform.get("from")
        if not isinstance(from_field, dict):
            continue
        from_data = from_field.get("data")
        if isinstance(from_data, dict) and "url" in from_data:
            _append_ref(datasets, from_data["url"], name_map)
    return datasets


def extract_vegalite_datasets(
    spec: dict[str, Any], name_map: dict[str, str]
) -> list[str]:
    """Extract dataset references from a Vega-Lite spec by recursive walk."""
    datasets: list[str] = []

    if isinstance(data := spec.get("data"), dict):
        if "url" in data:
            _append_ref(datasets, data["url"], name_map)
        if "values" in data:
            datasets.extend(_inline_value_refs(data["values"], name_map))

    datasets.extend(_vegalite_lookup_refs(spec, name_map))

    for layer in spec.get("layer") or []:
        if isinstance(layer, dict):
            datasets.extend(extract_vegalite_datasets(layer, name_map))

    for key in ("concat", "hconcat", "vconcat"):
        for sub in spec.get(key) or []:
            if isinstance(sub, dict):
                datasets.extend(extract_vegalite_datasets(sub, name_map))

    if isinstance(spec.get("spec"), dict):
        datasets.extend(extract_vegalite_datasets(spec["spec"], name_map))

    return datasets


def _vega_signal_refs(
    url_value: dict[str, Any],
    spec: dict[str, Any],
    name_map: dict[str, str],
) -> list[str]:
    """Extract dataset refs from a signal-based Vega data URL."""
    signal_name = url_value["signal"]
    signal = next(
        (s for s in spec.get("signals") or [] if s.get("name") == signal_name),
        None,
    )
    if signal is None:
        return []

    datasets: list[str] = []
    if isinstance(signal.get("value"), str):
        _append_ref(datasets, signal["value"], name_map)
    for opt in (signal.get("bind") or {}).get("options") or []:
        if isinstance(opt, str):
            _append_ref(datasets, opt, name_map)
    return datasets


def _vega_lookup_transform_refs(
    data_item: dict[str, Any], name_map: dict[str, str]
) -> list[str]:
    """Extract dataset refs from Vega lookup transforms within a data item."""
    datasets: list[str] = []
    for transform in data_item.get("transform") or []:
        if not (isinstance(transform, dict) and transform.get("type") == "lookup"):
            continue
        from_field = transform.get("from")
        if not isinstance(from_field, dict):
            continue  # "from" can be a string (named data reference)
        from_data = from_field.get("data")
        if isinstance(from_data, dict) and "url" in from_data:
            _append_ref(datasets, from_data["url"], name_map)
    return datasets


def extract_vega_datasets(spec: dict[str, Any], name_map: dict[str, str]) -> list[str]:
    """Extract dataset references from a Vega spec, including group scopes."""
    datasets: list[str] = []

    for data_item in spec.get("data") or []:
        if not isinstance(data_item, dict):
            continue

        url_value = data_item.get("url")
        if isinstance(url_value, str):
            _append_ref(datasets, url_value, name_map)
        elif isinstance(url_value, dict) and "signal" in url_value:
            datasets.extend(_vega_signal_refs(url_value, spec, name_map))

        if "values" in data_item:
            datasets.extend(_inline_value_refs(data_item["values"], name_map))

        datasets.extend(_vega_lookup_transform_refs(data_item, name_map))

    # Group marks introduce nested scopes that can declare their own signals,
    # data, and marks. Recurse with the group as the current spec so signal-
    # based URLs resolve against the correct local scope.
    for mark in spec.get("marks") or []:
        if isinstance(mark, dict) and mark.get("type") == "group":
            datasets.extend(extract_vega_datasets(mark, name_map))

    return datasets


# ---------------------------------------------------------------------------
# Name map + config
# ---------------------------------------------------------------------------


def build_name_map(datapackage: dict[str, Any]) -> dict[str, str]:
    """
    Build a mapping from file paths to canonical dataset names.

    Maps multiple path variants (with/without data/ prefix, filename only)
    to the canonical resource name from datapackage.json.
    """
    name_map: dict[str, str] = {}
    for resource in datapackage["resources"]:
        name = resource["name"]
        path = resource.get("path", "")
        if not path:
            continue

        # Map the path as given in datapackage.json
        name_map[path] = name

        # Map with data/ prefix: "data/cars.json" -> "cars"
        filename = Path(path).name
        name_map[f"data/{filename}"] = name

        # Map filename only: "cars.json" -> "cars"
        name_map[filename] = name

    return name_map


def load_config() -> Config:
    """
    Read ref-pinning strategy + source URL templates from the TOML config.

    Returns a Config dict with two keys:
      - ``refs``: ``{"vega-lite": "main", "vega": "main", "altair": "main"}``
        (keys normalized from underscore → hyphen to match ``gallery_name``)
      - ``sources``: the raw ``[sources]`` table — URL format strings with
        ``{…_ref}`` placeholders still present; substituted later once SHAs
        are resolved.
    """
    config_path = REPO_ROOT / "_data" / "gallery-examples.toml"
    with config_path.open("rb") as f:
        raw = tomllib.load(f)

    # TOML uses underscore keys; normalize to hyphen to match gallery_name.
    ref_toml = raw.get("ref", {})
    refs = {
        "vega-lite": ref_toml["vega_lite"],
        "vega": ref_toml["vega"],
        "altair": ref_toml["altair"],
    }
    # Surface TOML mistakes here (empty or non-string refs) rather than as
    # opaque 404s from GitHub's /commits/{ref} endpoint later in the run.
    for name, ref in refs.items():
        if not isinstance(ref, str) or not ref.strip():
            msg = (
                f"Empty or non-string ref for gallery '{name}' in gallery-examples.toml"
            )
            raise ValueError(msg)
    return {"refs": refs, "sources": raw["sources"]}


# ---------------------------------------------------------------------------
# HTTP + ref resolution
# ---------------------------------------------------------------------------


def _raw_github_fallback(url: str) -> str | None:
    """
    Translate a jsDelivr ``/gh/`` URL to its raw.githubusercontent.com twin.

    ``https://cdn.jsdelivr.net/gh/{owner}/{repo}@{ref}/{path}`` and
    ``https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}`` serve
    byte-identical content for the same commit SHA, so the raw host is a
    safe mirror when jsDelivr misbehaves. Returns None for URLs that aren't
    jsDelivr ``/gh/`` (no fallback exists for those hosts).
    """
    prefix = "https://cdn.jsdelivr.net/gh/"
    if not url.startswith(prefix):
        return None
    slug, at, ref_path = url.removeprefix(prefix).partition("@")
    ref, slash, path = ref_path.partition("/")
    if not (at and slash and path):
        return None
    return f"https://raw.githubusercontent.com/{slug}/{ref}/{path}"


async def _get_checked(session: httpx.AsyncClient, url: str) -> httpx.Response:
    """
    GET ``url`` with a raised-for-status response, mirroring around jsDelivr flakes.

    Under a concurrent burst jsDelivr intermittently returns 403 for
    SHA-pinned ``/gh/`` files that are actually available, and it caches
    that 403 at the edge for 60 s (observed 2026-07-08) — so retrying the
    same URL within the run is futile. Instead, transient failures
    (403/429/5xx or a transport error) on a jsDelivr URL are retried once
    against raw.githubusercontent.com, which serves identical bytes for the
    same SHA. Non-jsDelivr URLs and non-transient statuses raise as before.
    """
    try:
        resp = await session.get(url)
        resp.raise_for_status()
    except (httpx.TransportError, httpx.HTTPStatusError) as err:
        transient = isinstance(err, httpx.TransportError) or (
            isinstance(err, httpx.HTTPStatusError)
            and err.response.status_code in _TRANSIENT_STATUSES
        )
        fallback = _raw_github_fallback(url)
        if not (transient and fallback):
            raise
        logger.warning(
            "Transient failure for %s (%s); retrying via %s", url, err, fallback
        )
        resp = await session.get(fallback)
        resp.raise_for_status()
    return resp


async def _fetch_text(session: httpx.AsyncClient, url: str) -> str:
    """
    GET ``url`` and return the response body as text.

    Used for Vega and Vega-Lite specification bodies. For index endpoints use
    ``_fetch_json``. Raises ``RuntimeError`` on an empty body so a truncated
    upstream response does not cascade into an opaque parser error.
    """
    resp = await _get_checked(session, url)
    if not resp.text:
        msg = f"Empty response body from {url}"
        raise RuntimeError(msg)
    return resp.text


async def _fetch_json(session: httpx.AsyncClient, url: str) -> Any:
    """GET ``url`` and return parsed JSON (content-type-agnostic)."""
    resp = await _get_checked(session, url)
    return resp.json()


async def resolve_refs(
    session: httpx.AsyncClient, refs: dict[str, str]
) -> dict[str, ResolvedRef]:
    """
    Resolve each gallery's ref (branch/tag/SHA) to an immutable commit SHA.

    One GitHub API call per repo pins every subsequent index and source URL in
    the run to one immutable upstream snapshot.
    """

    async def one(name: str) -> tuple[str, ResolvedRef]:
        slug = _GALLERY_URLS[name]["repo"]
        ref = refs[name]
        url = f"https://api.github.com/repos/{slug}/commits/{ref}"
        data = await _fetch_json(session, url)
        return name, {"commit": data["sha"]}

    pairs = await asyncio.gather(*(one(name) for name in _GALLERIES))
    return dict(pairs)


def _format_refs(refs: dict[str, ResolvedRef]) -> dict[str, str]:
    """Build the ``{…_ref: sha}`` substitution dict for TOML URL templates."""
    return {
        "vega_lite_ref": refs["vega-lite"]["commit"],
        "vega_ref": refs["vega"]["commit"],
        "altair_ref": refs["altair"]["commit"],
    }


async def fetch_indexes(
    session: httpx.AsyncClient,
    sources: dict[str, str],
    refs: dict[str, ResolvedRef],
) -> FetchedIndexes:
    """
    Fetch all three gallery indexes concurrently, pinned to resolved SHAs.

    All three projects publish JSON example indexes. Altair's index uses the
    attribute/arguments-syntax file as the canonical source for each rendered
    gallery page; method-syntax variants are alternate presentations of that
    same page and do not create additional records.
    """
    fmt = _format_refs(refs)
    vl_url = sources["vega_lite_examples_url"].format(**fmt)
    vega_url = sources["vega_examples_url"].format(**fmt)
    altair_url = sources["altair_examples_url"].format(**fmt)

    vl_index, vega_index, altair_index = await asyncio.gather(
        _fetch_json(session, vl_url),
        _fetch_json(session, vega_url),
        _fetch_json(session, altair_url),
    )
    return FetchedIndexes(vl_index, vega_index, altair_index)


# ---------------------------------------------------------------------------
# Example list construction
# ---------------------------------------------------------------------------


def _humanize_slug(slug: str) -> str:
    """Turn a file-ish slug (``stacked_bar-chart``) into a title (``Stacked Bar Chart``)."""
    return slug.replace("_", " ").replace("-", " ").title()


def _longest_wins(current: str | None, candidate: str | None) -> str | None:
    """Return whichever of the two non-empty strings is longer (stable on ties)."""
    if not candidate:
        return current
    if not current:
        return candidate
    if len(candidate) > len(current):
        return candidate
    return current


def _build_vegalite_examples(
    vl_index: dict[str, Any], commit_sha: str
) -> list[Example]:
    """
    Build Vega-Lite example list from the nested index.

    When the same slug appears under multiple sections, categories merge with
    dedup. Titles stay ``None`` until a real upstream title is seen anywhere
    in the index; a slug-humanized fallback is synthesized after the walk so
    a real title in a later section always beats an earlier absence. Between
    real titles, longest wins.
    """
    seen: dict[str, Example] = {}
    for section_name, section in vl_index.items():
        if not isinstance(section, dict):
            continue
        for category, items in section.items():
            if not isinstance(items, list):
                continue
            category = category or section_name
            for item in (raw for raw in items if isinstance(raw, dict)):
                slug = item["name"]
                title = item.get("title")  # None → synthesized after the walk
                description = item.get("description")
                if slug in seen:
                    entry = seen[slug]
                    if category not in entry["categories"]:
                        entry["categories"].append(category)
                    entry["example_name"] = _longest_wins(entry["example_name"], title)
                    entry["description"] = _longest_wins(
                        entry["description"], description
                    )
                else:
                    vl_urls = _GALLERY_URLS["vega-lite"]
                    seen[slug] = {
                        "gallery_name": "vega-lite",
                        "example_name": title,
                        "example_url": vl_urls["example_page"].format(slug=slug),
                        "spec_url": vl_urls["spec"].format(sha=commit_sha, slug=slug),
                        "categories": [category],
                        "description": description,
                        "datasets": [],
                    }

    # Synthesize slug-humanized fallbacks only where no upstream title was
    # ever seen. The `seen` dict is keyed by slug, so no back-channel field
    # is needed on the entry itself.
    for slug, entry in seen.items():
        if not entry["example_name"]:
            entry["example_name"] = _humanize_slug(slug)

    return list(seen.values())


def _altair_string_list(
    record: dict[str, Any],
    field: str,
    name: str,
    *,
    allow_empty: bool = True,
) -> list[str]:
    """Read a string-array field from one Altair index record."""
    value = record.get(field)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        msg = f"Altair example {name!r} must have a string {field} array"
        raise TypeError(msg)
    if not allow_empty and not value:
        msg = f"Altair example {name!r} must have at least one {field} value"
        raise ValueError(msg)
    return value


def _build_altair_example(
    record: Any,
    position: int,
    commit_sha: str,
    valid_names: set[str],
) -> Example:
    """Validate and normalize one record from Altair's published index."""
    if not isinstance(record, dict):
        msg = f"Altair example at index {position} is not an object"
        raise TypeError(msg)

    string_fields = ("name", "title", "url", "path", "description")
    invalid_strings = [
        field for field in string_fields if not isinstance(record.get(field), str)
    ]
    if invalid_strings:
        msg = (
            f"Altair example at index {position} has invalid string fields: "
            f"{invalid_strings}"
        )
        raise TypeError(msg)

    name = record["name"]
    path = record["path"]
    categories = _altair_string_list(record, "categories", name, allow_empty=False)
    datasets = _altair_string_list(record, "datasets", name)

    canonical_prefix = "tests/examples_arguments_syntax/"
    if not path.startswith(canonical_prefix) or not path.endswith(".py"):
        msg = (
            f"Altair example {name!r} has non-canonical source path {path!r}; "
            "expected an arguments-syntax Python file"
        )
        raise ValueError(msg)
    if Path(path).stem != name:
        msg = f"Altair example name {name!r} does not match source path {path!r}"
        raise ValueError(msg)

    unknown = sorted(set(datasets) - valid_names)
    if unknown:
        msg = f"Altair example {name!r} references unknown datasets: {unknown}"
        raise ValueError(msg)

    spec_template = _GALLERY_URLS["altair"]["spec"]
    return {
        "gallery_name": "altair",
        "example_name": record["title"],
        "example_url": record["url"],
        "spec_url": spec_template.format(sha=commit_sha, path=path),
        "categories": list(categories),
        "description": record["description"] or None,
        "datasets": list(datasets),
    }


def _build_altair_examples(
    altair_index: dict[str, Any], commit_sha: str, valid_names: set[str]
) -> list[Example]:
    """Normalize Altair's published page-level gallery index."""
    gallery = altair_index.get("gallery")
    if not isinstance(gallery, dict):
        msg = "Altair examples index must contain a gallery object"
        raise TypeError(msg)
    if gallery.get("name") != "altair":
        msg = "Altair examples index is missing gallery.name='altair'"
        raise ValueError(msg)
    if gallery.get("repository") != "https://github.com/vega/altair":
        msg = "Altair examples index has an unexpected gallery.repository"
        raise ValueError(msg)

    records = altair_index.get("examples")
    if not isinstance(records, list):
        msg = "Altair examples index must contain an examples array"
        raise TypeError(msg)

    return [
        _build_altair_example(record, position, commit_sha, valid_names)
        for position, record in enumerate(records)
    ]


def build_example_list(
    vl_index: dict[str, Any],
    vega_index: dict[str, Any],
    altair_index: dict[str, Any],
    refs: dict[str, ResolvedRef],
    valid_names: set[str],
) -> list[Example]:
    """Normalize three gallery indexes into a flat example list."""
    examples = _build_vegalite_examples(vl_index, refs["vega-lite"]["commit"])

    vega_sha = refs["vega"]["commit"]
    vega_urls = _GALLERY_URLS["vega"]

    # Vega: index is {category: [list of {name}]}. A slug repeated under
    # multiple categories merges its categories, mirroring the vega-lite
    # walk (no cross-listed slug exists upstream today, but first-wins
    # would silently drop categories if one ever appears).
    seen_vega: dict[str, Example] = {}
    for category, items in vega_index.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            slug = item["name"]
            if slug in seen_vega:
                entry = seen_vega[slug]
                if category not in entry["categories"]:
                    entry["categories"].append(category)
                continue
            seen_vega[slug] = {
                "gallery_name": "vega",
                "example_name": _humanize_slug(slug),
                "example_url": vega_urls["example_page"].format(slug=slug),
                "spec_url": vega_urls["spec"].format(sha=vega_sha, slug=slug),
                "categories": [category],
                "description": None,
                "datasets": [],
            }
    examples.extend(seen_vega.values())
    examples.extend(
        _build_altair_examples(
            altair_index,
            refs["altair"]["commit"],
            valid_names,
        )
    )

    return examples


# ---------------------------------------------------------------------------
# Enrichment
# ---------------------------------------------------------------------------


# Vega-Lite and Vega require spec enrichment. Altair's published index already
# contains its authoritative dataset list and description.
_SPEC_EXTRACTORS: Final = {
    "vega-lite": extract_vegalite_datasets,
    "vega": extract_vega_datasets,
}


async def enrich_with_datasets(
    examples: list[Example],
    session: httpx.AsyncClient,
    name_map: dict[str, str],
) -> None:
    """Fetch Vega and Vega-Lite specs concurrently and fill in datasets."""
    sem = asyncio.Semaphore(_ENRICH_CONCURRENCY)

    async def enrich_one(example: Example) -> None:
        gallery = example["gallery_name"]
        extractor = _SPEC_EXTRACTORS.get(gallery)
        if extractor is None:
            msg = f"Unhandled gallery_name during enrichment: {gallery!r}"
            raise ValueError(msg)

        async with sem:
            text = await _fetch_text(session, example["spec_url"])

        spec = json.loads(text)
        example["datasets"] = extractor(spec, name_map)
        if not example.get("description"):
            example["description"] = spec.get("description")

        # Deduplicate datasets, preserve order
        example["datasets"] = list(dict.fromkeys(example["datasets"]))

    pending = [ex for ex in examples if ex["gallery_name"] != "altair"]
    # asyncio.gather(return_exceptions=True) propagates BaseException subclasses
    # (KeyboardInterrupt, SystemExit) directly and captures only Exception.
    results = await asyncio.gather(
        *(enrich_one(ex) for ex in pending), return_exceptions=True
    )
    errors = [
        (ex, r)
        for ex, r in zip(pending, results, strict=True)
        if isinstance(r, Exception)
    ]
    if errors:
        for ex, err in errors:
            logger.error("Failed: %s (%s): %s", ex["example_name"], ex["spec_url"], err)
        msg = f"{len(errors)} example(s) failed during enrichment"
        raise RuntimeError(msg)


# ---------------------------------------------------------------------------
# Finalize + invariants
# ---------------------------------------------------------------------------


def finalize_examples(examples: list[Example]) -> list[dict[str, Any]]:
    """Sort deterministically and return plain JSON-serializable mappings."""
    examples.sort(key=operator.itemgetter("gallery_name", "example_name"))
    return [dict(ex) for ex in examples]


# Per-gallery count floors. Trip-wires for catastrophic regressions
# (upstream restructuring, parser breakage), not tight estimates. Current
# counts (2026-08): altair=188, vega=93, vega-lite=189. Bump if upstream
# genuinely prunes a gallery; loosen if you want to tolerate more attrition.
_MIN_EXPECTED_PER_GALLERY: Final[Mapping[str, int]] = MappingProxyType({
    "altair": 160,
    "vega": 80,
    "vega-lite": 160,
})


def assert_expected_galleries(examples: list[dict[str, Any]]) -> None:
    """
    Raise if any expected gallery is missing or drops below its count floor.

    Floors are deliberately loose — they catch ~15%+ regressions, not small
    attrition. A missing gallery counts as zero and trips the same check.
    """
    by_gallery = Counter(ex["gallery_name"] for ex in examples)
    parts = ", ".join(f"{count} {name}" for name, count in sorted(by_gallery.items()))
    logger.info("Collected %d examples (%s)", len(examples), parts)

    below_floor = [
        (name, by_gallery.get(name, 0), floor)
        for name, floor in _MIN_EXPECTED_PER_GALLERY.items()
        if by_gallery.get(name, 0) < floor
    ]
    if below_floor:
        details = ", ".join(
            f"{name}: got {got}, expected >= {floor}"
            for name, got, floor in below_floor
        )
        msg = (
            f"Gallery count below expected floor — possible upstream "
            f"format change. {details}"
        )
        raise RuntimeError(msg)


def assert_unique_urls(examples: list[dict[str, Any]]) -> None:
    """
    Enforce the registry's URL uniqueness invariants.

    ``example_url`` is stable across regenerations, while ``spec_url`` embeds
    the pinned commit SHA and therefore changes as upstream galleries change.
    Both must be unique within a snapshot; this generator-side check catches
    scraper bugs that would otherwise silently emit duplicates.
    """
    for field in ("example_url", "spec_url"):
        counts = Counter(ex[field] for ex in examples)
        duplicates = sorted(u for u, n in counts.items() if n > 1)
        if duplicates:
            msg = (
                f"duplicate {field} in gallery_examples — uniqueness invariant "
                f"violated: {duplicates}"
            )
            raise RuntimeError(msg)


# ---------------------------------------------------------------------------
# Pipeline entrypoints
# ---------------------------------------------------------------------------


async def run_pipeline() -> list[dict[str, Any]]:
    """
    Run the full pipeline without I/O side effects.

    Returns the finalized, validated example list. Callers are responsible
    for serializing it (see ``async_main``).
    """
    config = load_config()
    sources = config["sources"]
    requested_refs = config["refs"]
    logger.info(
        "Loaded config: %d source URLs, refs=%s",
        len(sources),
        requested_refs,
    )

    datapackage_path = REPO_ROOT / "datapackage.json"
    with datapackage_path.open() as f:
        datapackage = json.load(f)
    name_map = build_name_map(datapackage)
    valid_names = set(name_map.values())
    logger.info("Built name map: %d datasets", len(valid_names))

    # httpx default: HTTP/1.1 only, no multiplexing — avoids the
    # concurrent-body-swapping bug we hit with niquests when fetching
    # across multiple hosts (jsDelivr + api.github.com) under asyncio
    # concurrency. Timeout is set client-wide so per-call argument isn't
    # needed.
    async with httpx.AsyncClient(
        timeout=_CLIENT_TIMEOUT,
        follow_redirects=True,
    ) as session:
        resolved_refs = await resolve_refs(session, requested_refs)
        for name in _GALLERIES:
            logger.info(
                "Resolved %s@%s → %s",
                name,
                requested_refs[name],
                resolved_refs[name]["commit"],
            )
        logger.info(
            "Upstream provenance: vega-lite=%s vega=%s altair=%s",
            resolved_refs["vega-lite"]["commit"][:12],
            resolved_refs["vega"]["commit"][:12],
            resolved_refs["altair"]["commit"][:12],
        )

        indexes = await fetch_indexes(session, sources, resolved_refs)

        examples = build_example_list(
            indexes.vl_index,
            indexes.vega_index,
            indexes.altair_index,
            resolved_refs,
            valid_names,
        )
        logger.info("Built example list: %d examples", len(examples))

        await enrich_with_datasets(examples, session, name_map)

    finalized = finalize_examples(examples)
    assert_expected_galleries(finalized)
    assert_unique_urls(finalized)
    return finalized


async def async_main() -> None:
    """Run the pipeline and write output to data/gallery-examples.json."""
    examples = await run_pipeline()
    output_path = REPO_ROOT / "data" / "gallery-examples.json"
    tmp_path = output_path.with_suffix(".json.tmp")
    tmp_path.write_text(
        json.dumps(examples, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    # Atomic replace: a mid-write crash cannot leave the tracked file
    # half-written (which git would notice as a phantom change).
    Path(tmp_path).replace(output_path)
    logger.info("Wrote %s", output_path)


def main() -> None:
    """Entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    # httpx emits one INFO line per request (~400 requests in this run),
    # which drowns out the pipeline's own progress and provenance lines.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
