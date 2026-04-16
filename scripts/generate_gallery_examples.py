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
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
TIMEOUT = 30

# Spec URL format strings. jsDelivr proxies GitHub raw content with aggressive
# CDN caching; embedding an immutable commit SHA gives 100% cache hits with
# zero invalidation risk. Consumers can verify these URLs match the TOML
# read-path strategy documented in _data/gallery_examples.toml.
_VEGA_LITE_SPEC_URL = (
    "https://cdn.jsdelivr.net/gh/vega/vega-lite@{sha}/examples/specs/{slug}.vl.json"
)
_VEGA_SPEC_URL = (
    "https://cdn.jsdelivr.net/gh/vega/vega@{sha}/docs/examples/{slug}.vg.json"
)
_ALTAIR_SPEC_URL = "https://cdn.jsdelivr.net/gh/vega/altair@{sha}/{path}"

# Internal repo keys match the `gallery_name` field in output. The TOML file
# uses underscore variants (vega_lite) because hyphens aren't str.format-safe
# in placeholder names; we translate at load time.
_GALLERIES = ("vega-lite", "vega", "altair")
_REPO_SLUGS = {
    "vega-lite": "vega/vega-lite",
    "vega": "vega/vega",
    "altair": "vega/altair",
}

# URL prefixes that indicate a vega-datasets reference. Trailing `/` prevents
# false-positive matches against sibling packages like `vega-datasets-extra`.
_VEGA_DATASETS_PREFIXES = (
    "https://cdn.jsdelivr.net/npm/vega-datasets/",
    "https://cdn.jsdelivr.net/npm/vega-datasets@",
    "https://raw.githubusercontent.com/vega/vega-datasets/",
)


def normalize_dataset_reference(ref: str, name_map: dict[str, str]) -> str | None:
    """
    Canonicalize a dataset reference to a datapackage resource name.

    Returns the canonical name, or None if the reference is external
    (not a vega-datasets URL). Raises ValueError if the reference
    looks like a vega-datasets URL but can't be resolved.
    """
    if not isinstance(ref, str):
        return None
    is_vega_datasets = any(ref.startswith(p) for p in _VEGA_DATASETS_PREFIXES)

    path = ref
    for prefix in _VEGA_DATASETS_PREFIXES:
        if path.startswith(prefix):
            idx = path.find("/data/", len(prefix))
            if idx != -1:
                path = "data/" + path[idx + len("/data/") :]
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


def _collect_url_ref(url: str, name_map: dict[str, str]) -> list[str]:
    """Normalize a URL and return a single-element list, or empty list if None."""
    ref = normalize_dataset_reference(url, name_map)
    return [ref] if ref is not None else []


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
            datasets.extend(_collect_url_ref(from_data["url"], name_map))
    return datasets


def extract_vegalite_datasets(
    spec: dict[str, Any], name_map: dict[str, str]
) -> list[str]:
    """Extract dataset references from a Vega-Lite spec by recursive walk."""
    datasets: list[str] = []

    if isinstance(spec.get("data"), dict) and "url" in spec["data"]:
        datasets.extend(_collect_url_ref(spec["data"]["url"], name_map))

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
    datasets: list[str] = []
    for signal in spec.get("signals") or []:
        if signal.get("name") != signal_name:
            continue
        if isinstance(signal.get("value"), str):
            datasets.extend(_collect_url_ref(signal["value"], name_map))
        for opt in (signal.get("bind") or {}).get("options") or []:
            if isinstance(opt, str):
                datasets.extend(_collect_url_ref(opt, name_map))
        break
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
            datasets.extend(_collect_url_ref(from_data["url"], name_map))
    return datasets


def extract_vega_datasets(spec: dict[str, Any], name_map: dict[str, str]) -> list[str]:
    """Extract dataset references from a Vega spec."""
    datasets: list[str] = []

    for data_item in spec.get("data") or []:
        if not isinstance(data_item, dict):
            continue

        url_value = data_item.get("url")
        if isinstance(url_value, str):
            datasets.extend(_collect_url_ref(url_value, name_map))
        elif isinstance(url_value, dict) and "signal" in url_value:
            datasets.extend(_vega_signal_refs(url_value, spec, name_map))

        datasets.extend(_vega_lookup_transform_refs(data_item, name_map))

    return datasets


# Altair dataset reference patterns (convention-based, not mechanical).
# Scoped to three explicit patterns that cover Altair v6+ API usage.
_ALTAIR_PATTERNS = [
    re.compile(r"data\.(\w+)\s*\("),  # data.cars()
    re.compile(r"data\.(\w+)\.url"),  # data.cars.url
    re.compile(
        r"alt\.topo_feature\s*\(\s*data\.(\w+)\.url"
    ),  # alt.topo_feature(data.X.url
]

# Patterns that indicate inline data (not a missing dataset reference)
_INLINE_DATA_PATTERNS = re.compile(
    r"pd\.DataFrame|alt\.InlineData|DataFrame\(|\.from_dict\("
)

# Patterns that indicate an import of vega_datasets data object
_DATA_IMPORT = re.compile(r"from\s+(?:vega_datasets|altair\.datasets)\s+import\s+data")

# Patterns that indicate unrecognized vega_datasets API usage (method call with args)
_UNRECOGNIZED_API_PATTERNS = re.compile(r"data\.\w+\(['\"\w]")


def extract_altair_datasets(code: str, valid_names: set[str]) -> list[str]:
    """
    Extract dataset references from Altair Python source code.

    Convention-based: matches three explicit source-level patterns. Raises
    ValueError when the file imports `data` but yields nothing usable — either
    because no pattern matched (patterns may need updating) or because every
    matched name is unknown to vega-datasets (likely an upstream rename).
    Mixed known/unknown is permitted: unknowns are dropped with a warning.
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
        if extracted and not _UNRECOGNIZED_API_PATTERNS.search(code):
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


def load_config() -> dict[str, Any]:
    """
    Read ref-pinning strategy + source URL templates from the TOML config.

    Returns a dict with two keys:
      - ``refs``: ``{"vega-lite": "main", "vega": "main", "altair": "main"}``
        (keys normalized from underscore → hyphen to match ``gallery_name``)
      - ``sources``: the raw ``[sources]`` table — URL format strings with
        ``{…_ref}`` placeholders still present; substituted later once SHAs
        are resolved.
    """
    config_path = REPO_ROOT / "_data" / "gallery_examples.toml"
    with config_path.open("rb") as f:
        raw = tomllib.load(f)

    # TOML uses underscore keys; normalize to hyphen to match gallery_name.
    ref_toml = raw.get("ref", {})
    refs = {
        "vega-lite": ref_toml["vega_lite"],
        "vega": ref_toml["vega"],
        "altair": ref_toml["altair"],
    }
    return {"refs": refs, "sources": raw["sources"]}


# Docstring delimiter is captured so the description regex can reuse it —
# supports both triple-double and triple-single quote docstrings.
_TITLE_PATTERN = re.compile(
    r'^(?P<q>"""|\'\'\')\s*\n(?P<title>.*?)\n[-=]+\s*\n', re.MULTILINE | re.DOTALL
)
_DESCRIPTION_PATTERN = re.compile(
    r'^(?P<q>"""|\'\'\')\s*\n.*?\n[-=]+\s*\n(?P<body>.*?)(?P=q)',
    re.MULTILINE | re.DOTALL,
)
_CATEGORY_PATTERN = re.compile(r"^#\s*category:\s*(.+)", re.MULTILINE)


def _parse_altair_metadata(code: str, filename: str) -> dict[str, Any]:
    """Extract title, description, and category from Altair source code."""
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


async def _fetch_text(session: httpx.AsyncClient, url: str) -> str:
    # Callers parse JSON manually from text because some endpoints return
    # text/plain or vendor-specific content types that rejected the old
    # niquests `.json()` helper.
    resp = await session.get(url)
    resp.raise_for_status()
    if not resp.text:
        msg = f"Empty response body from {url}"
        raise RuntimeError(msg)
    return resp.text


async def resolve_refs(
    session: httpx.AsyncClient, refs: dict[str, str]
) -> dict[str, dict[str, str]]:
    """
    Resolve each gallery's ref (branch/tag/SHA) to the commit + tree SHAs.

    Returns ``{"vega-lite": {"commit": "<sha>", "tree": "<sha>"}, ...}``.
    One GitHub API call per repo (three total) — fetches
    ``/repos/{owner}/{repo}/commits/{ref}`` which returns both the commit
    SHA and ``commit.tree.sha`` in the same payload. This pins every
    subsequent URL in the run to one immutable snapshot per upstream repo
    and gives us the tree SHA the altair Trees API call needs, for free.
    """

    async def one(name: str) -> tuple[str, dict[str, str]]:
        slug = _REPO_SLUGS[name]
        ref = refs[name]
        url = f"https://api.github.com/repos/{slug}/commits/{ref}"
        resp = await session.get(url)
        resp.raise_for_status()
        data = json.loads(resp.text)
        return name, {"commit": data["sha"], "tree": data["commit"]["tree"]["sha"]}

    pairs = await asyncio.gather(*(one(name) for name in _GALLERIES))
    return dict(pairs)


def _format_refs(refs: dict[str, dict[str, str]]) -> dict[str, str]:
    """Build the ``{…_ref: sha}`` substitution dict for TOML URL templates."""
    return {
        "vega_lite_ref": refs["vega-lite"]["commit"],
        "vega_ref": refs["vega"]["commit"],
        "altair_ref": refs["altair"]["commit"],
    }


async def fetch_indexes(
    session: httpx.AsyncClient,
    sources: dict[str, str],
    refs: dict[str, dict[str, str]],
) -> tuple[Any, Any, list[dict[str, Any]]]:
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

    async def fetch_json(url: str) -> Any:
        return json.loads(await _fetch_text(session, url))

    vl_index, vega_index, altair_tree = await asyncio.gather(
        fetch_json(vl_url),
        fetch_json(vega_url),
        fetch_json(altair_tree_url),
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
    return vl_index, vega_index, altair_files


def _longest_wins(current: str | None, candidate: str | None) -> str | None:
    """Return whichever of the two non-empty strings is longer (stable on ties)."""
    if not candidate:
        return current
    if not current:
        return candidate
    if len(candidate) > len(current):
        return candidate
    return current


def _build_vegalite_examples(vl_index: Any, commit_sha: str) -> list[dict[str, Any]]:
    """
    Build Vega-Lite example list from nested index.

    When the same slug appears under multiple sections, longest-wins for
    title and description, and categories are merged with dedup.
    """
    examples: list[dict[str, Any]] = []
    seen: dict[str, dict[str, Any]] = {}
    for section_name, section in vl_index.items():
        if not isinstance(section, dict):
            continue
        for category, items in section.items():
            if not isinstance(items, list):
                continue
            category = category or section_name
            for item in items:
                slug = item["name"]
                title = (
                    item.get("title")
                    or slug.replace("_", " ").replace("-", " ").title()
                )
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
                    entry = {
                        "gallery_name": "vega-lite",
                        "example_name": title,
                        "example_url": f"https://vega.github.io/vega-lite/examples/{slug}.html",
                        "spec_url": _VEGA_LITE_SPEC_URL.format(
                            sha=commit_sha, slug=slug
                        ),
                        "categories": [category],
                        "description": description,
                        "datasets": [],
                    }
                    seen[slug] = entry
                    examples.append(entry)
    return examples


def build_example_list(
    vl_index: Any,
    vega_index: Any,
    altair_files: list[dict[str, Any]],
    refs: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    """Normalize three gallery indexes into a flat example list."""
    examples = _build_vegalite_examples(vl_index, refs["vega-lite"]["commit"])

    vega_sha = refs["vega"]["commit"]
    altair_sha = refs["altair"]["commit"]

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
                "example_url": f"https://vega.github.io/vega/examples/{slug}/",
                "spec_url": _VEGA_SPEC_URL.format(sha=vega_sha, slug=slug),
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
        examples.append({
            "gallery_name": "altair",
            "example_name": name.removesuffix(".py").replace("_", " ").title(),
            "example_url": f"https://altair-viz.github.io/gallery/{name.removesuffix('.py')}.html",
            "spec_url": _ALTAIR_SPEC_URL.format(sha=altair_sha, path=path),
            "categories": [],
            "description": None,
            "datasets": [],
            "_filename": name,  # internal, removed before output
        })

    return examples


async def enrich_with_datasets(
    examples: list[dict[str, Any]],
    session: httpx.AsyncClient,
    name_map: dict[str, str],
    valid_names: set[str],
) -> None:
    """Fetch specs concurrently and fill in datasets (and Altair metadata)."""
    sem = asyncio.Semaphore(20)

    async def enrich_one(example: dict[str, Any]) -> None:
        async with sem:
            text = await _fetch_text(session, example["spec_url"])

        gallery = example["gallery_name"]
        if gallery == "altair":
            if not _DATA_IMPORT.search(text) and not _CATEGORY_PATTERN.search(text):
                msg = f"Altair response has no data import or category marker: {example['spec_url']}"
                raise ValueError(msg)
            meta = _parse_altair_metadata(text, example.get("_filename", ""))
            example["example_name"] = meta["example_name"]
            example["description"] = meta["description"]
            example["categories"] = meta["categories"]
            example["datasets"] = extract_altair_datasets(text, valid_names)
        elif gallery == "vega-lite":
            spec = json.loads(text)
            example["datasets"] = extract_vegalite_datasets(spec, name_map)
            if not example.get("description"):
                example["description"] = spec.get("description")
        elif gallery == "vega":
            spec = json.loads(text)
            example["datasets"] = extract_vega_datasets(spec, name_map)
            if not example.get("description"):
                example["description"] = spec.get("description")

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


def finalize_examples(examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort deterministically and strip internal `_filename` key."""
    examples.sort(key=operator.itemgetter("gallery_name", "example_name"))
    return [{k: v for k, v in ex.items() if k != "_filename"} for ex in examples]


# Per-gallery count floors. Trip-wires for catastrophic regressions
# (upstream restructuring, parser breakage), not tight estimates. Current
# counts (2026-04): altair=117, vega=93, vega-lite=189. Bump if upstream
# genuinely prunes a gallery; loosen if you want to tolerate more attrition.
_MIN_EXPECTED_PER_GALLERY = {
    "altair": 100,
    "vega": 80,
    "vega-lite": 160,
}


def assert_expected_galleries(examples: list[dict[str, Any]]) -> None:
    """
    Raise if any expected gallery is missing or drops below its count floor.

    Floors are deliberately loose — they catch ~15%+ regressions, not small
    attrition. A missing gallery counts as zero and trips the same check.
    """
    by_gallery: dict[str, int] = {}
    for ex in examples:
        by_gallery[ex["gallery_name"]] = by_gallery.get(ex["gallery_name"], 0) + 1
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
    spec_urls = [ex["spec_url"] for ex in examples]
    if len(set(spec_urls)) != len(spec_urls):
        duplicates = sorted({u for u in spec_urls if spec_urls.count(u) > 1})
        msg = f"duplicate spec_url in gallery_examples — primary key invariant violated: {duplicates}"
        raise RuntimeError(msg)


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

    # httpx default: HTTP/1.1 only, no multiplexing — avoids the
    # concurrent-body-swapping bug we hit with niquests when fetching
    # across multiple hosts (jsDelivr + api.github.com) under asyncio
    # concurrency. Timeout is set client-wide so per-call TIMEOUT arg
    # isn't needed.
    async with httpx.AsyncClient(
        headers=headers,
        timeout=TIMEOUT,
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

        vl_index, vega_index, altair_files = await fetch_indexes(
            session, sources, resolved_refs
        )

        if not isinstance(vl_index, dict):
            msg = f"Expected dict for Vega-Lite index, got {type(vl_index).__name__}"
            raise TypeError(msg)
        if not isinstance(vega_index, dict):
            msg = f"Expected dict for Vega index, got {type(vega_index).__name__}"
            raise TypeError(msg)
        if not isinstance(altair_files, list):
            msg = f"Expected list for Altair file listing, got {type(altair_files).__name__}"
            raise TypeError(msg)

        examples = build_example_list(vl_index, vega_index, altair_files, resolved_refs)
        logger.info("Built example list: %d examples", len(examples))

        await enrich_with_datasets(examples, session, name_map, valid_names)

    examples = finalize_examples(examples)
    assert_expected_galleries(examples)
    assert_unique_spec_urls(examples)
    return examples


async def async_main() -> None:
    """Run the pipeline and write output to data/gallery-examples.json."""
    examples = await run_pipeline()
    output_path = REPO_ROOT / "data" / "gallery-examples.json"
    output_path.write_text(json.dumps(examples, indent=2, ensure_ascii=False) + "\n")
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
