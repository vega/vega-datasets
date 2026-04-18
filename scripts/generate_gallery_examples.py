#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx>=0.27,<1",
# ]
# ///
"""Generate gallery-examples.json from Vega ecosystem galleries."""

from __future__ import annotations

import asyncio
import json
import logging
import operator
import os
import re
import tomllib
from collections import Counter
from pathlib import Path
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    Literal,
    NamedTuple,
    NotRequired,
    TypedDict,
)

import httpx

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
_CLIENT_TIMEOUT: Final = 30
_ENRICH_CONCURRENCY: Final = 20


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class Example(TypedDict):
    """
    Intermediate gallery-example record carried through build + enrichment.

    ``_filename`` (underscore-prefixed) is an internal back-channel from
    construction to altair enrichment; ``finalize_examples`` strips any
    underscore-prefixed key before output. ``example_name`` is ``str | None``
    during construction — a vega-lite entry without a real upstream title in
    any section falls back to a slug-humanized synthesis before output.
    """

    gallery_name: Literal["vega", "vega-lite", "altair"]
    example_name: str | None
    example_url: str
    spec_url: str
    categories: list[str]
    description: str | None
    datasets: list[str]
    _filename: NotRequired[str]


class ResolvedRef(TypedDict):
    commit: str
    tree: str


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
    altair_files: list[dict[str, str]]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Per-gallery URL conventions. All four URL slots for each gallery live
# here so adding a new gallery is a single-entry edit. `spec` and
# `example_page` use str.format placeholders substituted at build time;
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
        "example_page": "https://altair-viz.github.io/gallery/{stem}.html",
        "spec": "https://cdn.jsdelivr.net/gh/vega/altair@{sha}/{path}",
    }),
})

# URL prefixes that indicate a vega-datasets reference. Trailing `/` prevents
# false-positive matches against sibling packages like `vega-datasets-extra`.
_VEGA_DATASETS_PREFIXES: Final[tuple[str, ...]] = (
    "https://cdn.jsdelivr.net/npm/vega-datasets/",
    "https://cdn.jsdelivr.net/npm/vega-datasets@",
    "https://raw.githubusercontent.com/vega/vega-datasets/",
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
            idx = ref.find("/data/", len(prefix))
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

    if isinstance(spec.get("data"), dict) and "url" in spec["data"]:
        _append_ref(datasets, spec["data"]["url"], name_map)

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
    """Extract dataset references from a Vega spec."""
    datasets: list[str] = []

    for data_item in spec.get("data") or []:
        if not isinstance(data_item, dict):
            continue

        url_value = data_item.get("url")
        if isinstance(url_value, str):
            _append_ref(datasets, url_value, name_map)
        elif isinstance(url_value, dict) and "signal" in url_value:
            datasets.extend(_vega_signal_refs(url_value, spec, name_map))

        datasets.extend(_vega_lookup_transform_refs(data_item, name_map))

    return datasets


# ---------------------------------------------------------------------------
# Altair source-level patterns (convention-based, transitional)
# ---------------------------------------------------------------------------

# Three explicit patterns covering Altair v6+ API usage.
_ALTAIR_PATTERNS: Final = [
    re.compile(r"data\.(\w+)\s*\("),  # data.cars()
    re.compile(r"data\.(\w+)\.url"),  # data.cars.url
    re.compile(r"alt\.topo_feature\s*\(\s*data\.(\w+)\.url"),
]

# Patterns that indicate inline data (not a missing dataset reference).
_INLINE_DATA_PATTERNS: Final = re.compile(
    r"pd\.DataFrame|alt\.InlineData|DataFrame\(|\.from_dict\("
)

# Pattern that indicates an import of the vega_datasets data object.
_DATA_IMPORT: Final = re.compile(
    r"from\s+(?:vega_datasets|altair\.datasets)\s+import\s+data"
)

# Pattern that indicates unrecognized vega_datasets API usage
# (method call with args). Singular because it's a single regex.
_UNRECOGNIZED_DATA_API: Final = re.compile(r"data\.\w+\(['\"\w]")


def extract_altair_datasets(code: str, valid_names: set[str]) -> list[str]:
    """
    Extract dataset references from Altair Python source code.

    Convention-based: matches three explicit source-level patterns. Raises
    ValueError when the file imports `data` but yields nothing usable — either
    because no pattern matched (patterns may need updating) or because every
    matched name is unknown to vega-datasets (likely an upstream rename).
    Mixed known/unknown is permitted: unknowns are dropped with a warning.

    Transitional. Vega + Vega-Lite ship a structured ``examples.json`` and the
    generator walks specs mechanically; altair ships no such index today, so
    this function scrapes source text. If altair begins publishing an index
    with a ``datasets`` field (see vega/altair#4002), this collapses to a
    field read. Note that ``data.cars()`` returns a DataFrame and compiles to
    inline ``values``, losing the filename — only altair itself can recover
    the dataset name, which is why an upstream-published index matters.
    """
    has_data_import = bool(_DATA_IMPORT.search(code))

    extracted: set[str] = set()
    for pattern in _ALTAIR_PATTERNS:
        extracted.update(pattern.findall(code))

    known = sorted(extracted & valid_names)
    unknown = sorted(extracted - valid_names)

    for name in unknown:
        logger.warning("External Altair dataset (not in vega-datasets): %s", name)

    if has_data_import and not known and not _INLINE_DATA_PATTERNS.search(code):
        if extracted and not _UNRECOGNIZED_DATA_API.search(code):
            msg = (
                f"Altair example uses recognized pattern but dataset name(s) "
                f"{unknown} not in vega-datasets. Likely upstream rename — "
                f"update valid_names or the example."
            )
            raise ValueError(msg)
        msg = (
            "Altair example imports `data` but no recognized dataset pattern "
            "was found. Patterns may need updating."
        )
        raise ValueError(msg)

    return known


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
# Altair metadata parsing (transitional — see vega/altair#4002)
# ---------------------------------------------------------------------------

# Docstring delimiter is captured so the description regex can reuse it —
# supports both triple-double and triple-single quote docstrings.
_TITLE_PATTERN: Final = re.compile(
    r'^(?P<q>"""|\'\'\')\s*\n(?P<title>.*?)\n[-=]+\s*\n', re.MULTILINE | re.DOTALL
)
_DESCRIPTION_PATTERN: Final = re.compile(
    r'^(?P<q>"""|\'\'\')\s*\n.*?\n[-=]+\s*\n(?P<body>.*?)(?P=q)',
    re.MULTILINE | re.DOTALL,
)
_CATEGORY_PATTERN: Final = re.compile(r"^#\s*category:\s*(.+)", re.MULTILINE)


def _parse_altair_metadata(code: str, filename: str) -> dict[str, Any]:
    """
    Extract title, description, and category from Altair source code.

    Transitional. Vega-Lite and Vega publish title/description/category
    as fields in their respective ``examples.json``; altair embeds the same
    data in docstrings and ``# category:`` comments, so this function exists
    to recover it from source. If altair publishes an examples index
    (vega/altair#4002), this is replaced by a field read.
    """
    title_match = _TITLE_PATTERN.search(code)
    if title_match:
        # Collapse multi-line titles (rare but upstream permits them).
        title = " ".join(title_match.group("title").split())
    else:
        title = filename.removesuffix(".py").replace("_", " ").title()

    desc_match = _DESCRIPTION_PATTERN.search(code)
    description = desc_match.group("body").strip() if desc_match else None
    if not description:
        description = None

    cat_match = _CATEGORY_PATTERN.search(code)
    categories = [cat_match.group(1).strip()] if cat_match else []

    return {"example_name": title, "description": description, "categories": categories}


# ---------------------------------------------------------------------------
# HTTP + ref resolution
# ---------------------------------------------------------------------------


async def _fetch_text(session: httpx.AsyncClient, url: str) -> str:
    """
    GET ``url`` and return the response body as text.

    Used for altair ``.py`` source, which isn't JSON. For JSON endpoints use
    ``_fetch_json``. Raises ``RuntimeError`` on an empty body so that a
    silently truncated upstream response doesn't cascade into a parser error
    two stages downstream.
    """
    resp = await session.get(url)
    resp.raise_for_status()
    if not resp.text:
        msg = f"Empty response body from {url}"
        raise RuntimeError(msg)
    return resp.text


async def _fetch_json(session: httpx.AsyncClient, url: str) -> Any:
    """GET ``url`` and return parsed JSON (content-type-agnostic)."""
    resp = await session.get(url)
    resp.raise_for_status()
    return resp.json()


async def resolve_refs(
    session: httpx.AsyncClient, refs: dict[str, str]
) -> dict[str, ResolvedRef]:
    """
    Resolve each gallery's ref (branch/tag/SHA) to the commit + tree SHAs.

    Returns ``{"vega-lite": {"commit": "<sha>", "tree": "<sha>"}, ...}``.
    One GitHub API call per repo (three total) — fetches
    ``/repos/{owner}/{repo}/commits/{ref}`` which returns both the commit
    SHA and ``commit.tree.sha`` in the same payload. This pins every
    subsequent URL in the run to one immutable snapshot per upstream repo
    and gives us the tree SHA the altair Trees API call needs, for free.
    """

    async def one(name: str) -> tuple[str, ResolvedRef]:
        slug = _GALLERY_URLS[name]["repo"]
        ref = refs[name]
        url = f"https://api.github.com/repos/{slug}/commits/{ref}"
        data = await _fetch_json(session, url)
        return name, {"commit": data["sha"], "tree": data["commit"]["tree"]["sha"]}

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

    vega-lite and vega indexes come via jsDelivr (URL templates in TOML
    are substituted with commit SHAs). Altair uses the GitHub Trees API
    at the repo's tree SHA, filtered to ``tests/examples_methods_syntax/*.py``.
    The Contents API was dropped in favor of Trees API because the payload
    is ~4x smaller and composes cleanly with SHA pinning.
    """
    fmt = _format_refs(refs)
    vl_url = sources["vega_lite_examples_url"].format(**fmt)
    vega_url = sources["vega_examples_url"].format(**fmt)
    altair_tree_url = (
        f"https://api.github.com/repos/vega/altair/git/trees/"
        f"{refs['altair']['tree']}?recursive=1"
    )

    vl_index, vega_index, altair_tree = await asyncio.gather(
        _fetch_json(session, vl_url),
        _fetch_json(session, vega_url),
        _fetch_json(session, altair_tree_url),
    )

    # Trees API returns {"sha": ..., "tree": [{"path": ..., "type": ...}, ...],
    # "truncated": bool}. Our three repos all fit within the 100k-entry /
    # 7 MB limits (measured 2026-04-12: altair=603, vl=3498, vega=2022).
    if altair_tree.get("truncated"):
        msg = (
            "Altair git tree response was truncated. The repo has grown past "
            "the Trees API single-response limit; switch to a pagination "
            "strategy or a sub-tree fetch."
        )
        raise RuntimeError(msg)

    altair_dir = sources["altair_examples_dir"]
    altair_files = [
        {"path": entry["path"]}
        for entry in altair_tree["tree"]
        if entry.get("type") == "blob"
        and entry["path"].startswith(f"{altair_dir}/")
        and entry["path"].endswith(".py")
        and not Path(entry["path"]).name.startswith("__")
    ]
    return FetchedIndexes(vl_index, vega_index, altair_files)


# ---------------------------------------------------------------------------
# Example list construction
# ---------------------------------------------------------------------------


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
            for item in items:
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
            entry["example_name"] = slug.replace("_", " ").replace("-", " ").title()

    return list(seen.values())


def build_example_list(
    vl_index: dict[str, Any],
    vega_index: dict[str, Any],
    altair_files: list[dict[str, Any]],
    refs: dict[str, ResolvedRef],
) -> list[Example]:
    """Normalize three gallery indexes into a flat example list."""
    examples = _build_vegalite_examples(vl_index, refs["vega-lite"]["commit"])

    vega_sha = refs["vega"]["commit"]
    altair_sha = refs["altair"]["commit"]
    vega_urls = _GALLERY_URLS["vega"]
    altair_urls = _GALLERY_URLS["altair"]

    # Vega: index is {category: [list of {name}]}
    seen_vega: set[str] = set()
    for category, items in vega_index.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            slug = item["name"]
            if slug in seen_vega:
                continue
            seen_vega.add(slug)
            examples.append({
                "gallery_name": "vega",
                "example_name": slug.replace("-", " ").replace("_", " ").title(),
                "example_url": vega_urls["example_page"].format(slug=slug),
                "spec_url": vega_urls["spec"].format(sha=vega_sha, slug=slug),
                "categories": [category],
                "description": None,
                "datasets": [],
            })

    # Altair: Trees API-filtered listing -> stubs (metadata filled during
    # enrichment). Entries have shape {"path": "tests/examples_methods_syntax/foo.py"};
    # fetch_indexes already filtered out non-blob, non-.py, and dunder files.
    for file_info in altair_files:
        path = file_info["path"]
        name = Path(path).name
        stem = name.removesuffix(".py")
        examples.append({
            "gallery_name": "altair",
            "example_name": stem.replace("_", " ").title(),
            "example_url": altair_urls["example_page"].format(stem=stem),
            "spec_url": altair_urls["spec"].format(sha=altair_sha, path=path),
            "categories": [],
            "description": None,
            "datasets": [],
            "_filename": name,  # internal, stripped by finalize_examples
        })

    return examples


# ---------------------------------------------------------------------------
# Enrichment
# ---------------------------------------------------------------------------


# vega-lite and vega enrichment share a shape: parse JSON, run an extractor,
# fall back to the spec-level description. Altair is structurally different
# (text source, needs docstring parsing), so it keeps its own branch.
_SPEC_EXTRACTORS: Final = {
    "vega-lite": extract_vegalite_datasets,
    "vega": extract_vega_datasets,
}


async def enrich_with_datasets(
    examples: list[Example],
    session: httpx.AsyncClient,
    name_map: dict[str, str],
    valid_names: set[str],
) -> None:
    """Fetch specs concurrently and fill in datasets (and Altair metadata)."""
    sem = asyncio.Semaphore(_ENRICH_CONCURRENCY)

    async def enrich_one(example: Example) -> None:
        async with sem:
            text = await _fetch_text(session, example["spec_url"])

        gallery = example["gallery_name"]
        if gallery == "altair":
            # Response-health canary: a file missing BOTH markers is not an
            # altair example file (HTML error page, 404, or misrouted body).
            # `and` is intentional — many legitimate altair examples have
            # only one of the two markers, so `or` would reject valid files.
            if not _DATA_IMPORT.search(text) and not _CATEGORY_PATTERN.search(text):
                msg = (
                    f"Not an altair example file — response missing both "
                    f"`from … import data` and `# category:` markers "
                    f"(likely HTML error page, 404, or misrouted body): "
                    f"{example['spec_url']}"
                )
                raise ValueError(msg)
            # build_example_list always sets _filename on altair entries;
            # assert documents the invariant and narrows the NotRequired type.
            assert "_filename" in example
            meta = _parse_altair_metadata(text, example["_filename"])
            example["example_name"] = meta["example_name"]
            example["description"] = meta["description"]
            example["categories"] = meta["categories"]
            example["datasets"] = extract_altair_datasets(text, valid_names)
        elif gallery in _SPEC_EXTRACTORS:
            spec = json.loads(text)
            example["datasets"] = _SPEC_EXTRACTORS[gallery](spec, name_map)
            if not example.get("description"):
                example["description"] = spec.get("description")
        else:
            # Contract invariant: gallery_name is Literal["vega","vega-lite","altair"]
            # and every value must have a branch above. Fires only if
            # build_example_list introduces a new gallery without updating here.
            msg = f"Unhandled gallery_name during enrichment: {gallery!r}"
            raise ValueError(msg)

        # Deduplicate datasets, preserve order
        example["datasets"] = list(dict.fromkeys(example["datasets"]))

    # asyncio.gather(return_exceptions=True) propagates BaseException subclasses
    # (KeyboardInterrupt, SystemExit) directly and captures only Exception.
    results = await asyncio.gather(
        *(enrich_one(ex) for ex in examples), return_exceptions=True
    )
    errors = [
        (ex, r)
        for ex, r in zip(examples, results, strict=True)
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
    """
    Sort deterministically and strip any underscore-prefixed internal keys.

    Underscore-prefixed keys (``_filename``) are build-time back-channels
    that must not appear in the public dataset.
    """
    examples.sort(key=operator.itemgetter("gallery_name", "example_name"))
    return [{k: v for k, v in ex.items() if not k.startswith("_")} for ex in examples]


# Per-gallery count floors. Trip-wires for catastrophic regressions
# (upstream restructuring, parser breakage), not tight estimates. Current
# counts (2026-04): altair=117, vega=93, vega-lite=189. Bump if upstream
# genuinely prunes a gallery; loosen if you want to tolerate more attrition.
_MIN_EXPECTED_PER_GALLERY: Final[Mapping[str, int]] = MappingProxyType({
    "altair": 100,
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


def assert_unique_spec_urls(examples: list[dict[str, Any]]) -> None:
    """
    Enforce the spec_url primary-key invariant declared in datapackage.json.

    Frictionless `primaryKey` is declarative only in this pipeline — this
    check is the real enforcement and catches scraper bugs that would
    otherwise silently emit duplicates.
    """
    counts = Counter(ex["spec_url"] for ex in examples)
    duplicates = sorted(u for u, n in counts.items() if n > 1)
    if duplicates:
        msg = (
            f"duplicate spec_url in gallery_examples — primary key invariant "
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

    # Opportunistic auth: lifts api.github.com rate limit from 60/hr to
    # 5000/hr when a token is available. No-op when absent. jsDelivr
    # ignores the header, so scoping isn't needed.
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    logger.info(
        "GitHub auth: %s",
        "authenticated (5000/hr)"
        if token
        else "unauthenticated (60/hr — set GITHUB_TOKEN to raise the ceiling)",
    )

    # httpx default: HTTP/1.1 only, no multiplexing — avoids the
    # concurrent-body-swapping bug we hit with niquests when fetching
    # across multiple hosts (jsDelivr + api.github.com) under asyncio
    # concurrency. Timeout is set client-wide so per-call argument isn't
    # needed.
    async with httpx.AsyncClient(
        headers=headers,
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
            indexes.altair_files,
            resolved_refs,
        )
        logger.info("Built example list: %d examples", len(examples))

        await enrich_with_datasets(examples, session, name_map, valid_names)

    finalized = finalize_examples(examples)
    assert_expected_galleries(finalized)
    assert_unique_spec_urls(finalized)
    return finalized


async def async_main() -> None:
    """Run the pipeline and write output to data/gallery-examples.json."""
    examples = await run_pipeline()
    output_path = REPO_ROOT / "data" / "gallery-examples.json"
    tmp_path = output_path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(examples, indent=2, ensure_ascii=False) + "\n")
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
