#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "niquests>=3.11.2",
# ]
# ///
"""Generate gallery_examples.json from Vega ecosystem galleries."""

from __future__ import annotations

import asyncio
import json
import logging
import operator
import re
import tomllib
from pathlib import Path
from typing import Any

import niquests

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
TIMEOUT = 30

# URL prefixes that indicate a vega-datasets reference.
_VEGA_DATASETS_PREFIXES = (
    "https://cdn.jsdelivr.net/npm/vega-datasets",
    "https://raw.githubusercontent.com/vega/vega-datasets",
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

    # Strip known URL prefixes down to a relative path like "data/cars.json"
    path = ref
    for prefix in _VEGA_DATASETS_PREFIXES:
        if path.startswith(prefix):
            # Strip prefix up to and including "/data/"
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

    # Top-level data.url
    if isinstance(spec.get("data"), dict) and "url" in spec["data"]:
        datasets.extend(_collect_url_ref(spec["data"]["url"], name_map))

    # Transform lookups
    datasets.extend(_vegalite_lookup_refs(spec, name_map))

    # Layers
    for layer in spec.get("layer") or []:
        if isinstance(layer, dict):
            datasets.extend(extract_vegalite_datasets(layer, name_map))

    # Concat variants
    for key in ("concat", "hconcat", "vconcat"):
        for sub in spec.get(key) or []:
            if isinstance(sub, dict):
                datasets.extend(extract_vegalite_datasets(sub, name_map))

    # Facet/repeat sub-spec
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

    Convention-based: matches three explicit source-level patterns.
    Raises ValueError if code imports `data` but yields no matches
    and doesn't use inline data.
    """
    has_data_import = bool(_DATA_IMPORT.search(code))

    extracted: set[str] = set()
    for pattern in _ALTAIR_PATTERNS:
        extracted.update(pattern.findall(code))

    datasets: list[str] = []
    for name in extracted:
        if name in valid_names:
            datasets.append(name)
        else:
            logger.warning("External Altair dataset (not in vega-datasets): %s", name)

    # Fail-loud: if code imports data and uses an unrecognized API pattern
    if (
        has_data_import
        and not datasets
        and not _INLINE_DATA_PATTERNS.search(code)
        and (not extracted or _UNRECOGNIZED_API_PATTERNS.search(code))
    ):
        msg = (
            "Altair example imports `data` but no recognized dataset pattern "
            "was found. Patterns may need updating."
        )
        raise ValueError(msg)

    return sorted(datasets)


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


def load_config() -> dict[str, str]:
    """Read source URLs from _data/gallery_examples.toml."""
    config_path = REPO_ROOT / "_data" / "gallery_examples.toml"
    with config_path.open("rb") as f:
        config = tomllib.load(f)
    return config["sources"]


_TITLE_PATTERN = re.compile(r'^"""\s*\n?(.*?)\n[-=]+\s*\n', re.MULTILINE)
_DESCRIPTION_PATTERN = re.compile(
    r'^"""\s*\n.*?\n[-=]+\s*\n(.*?)"""', re.MULTILINE | re.DOTALL
)
_CATEGORY_PATTERN = re.compile(r"^#\s*category:\s*(.+)", re.MULTILINE)


def _parse_altair_metadata(code: str, filename: str) -> dict[str, Any]:
    """Extract title, description, and category from Altair source code."""
    title_match = _TITLE_PATTERN.search(code)
    if title_match:
        title = title_match.group(1).strip()
    else:
        title = filename.removesuffix(".py").replace("_", " ").title()

    desc_match = _DESCRIPTION_PATTERN.search(code)
    description = desc_match.group(1).strip() if desc_match else None
    if not description:
        description = None

    cat_match = _CATEGORY_PATTERN.search(code)
    categories = [cat_match.group(1).strip()] if cat_match else []

    return {"example_name": title, "description": description, "categories": categories}


async def fetch_indexes(
    session: niquests.AsyncSession, config: dict[str, str]
) -> tuple[Any, Any, list[dict[str, Any]]]:
    """Fetch all three gallery indexes concurrently."""
    vl_url = config["vega_lite_examples_url"]
    vega_url = config["vega_examples_url"]
    altair_dir = config["altair_examples_dir"]

    async def fetch_json(url: str) -> Any:
        resp = await session.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()  # raw.githubusercontent.com returns text/plain

    async def fetch_altair_listing(directory: str) -> list[dict[str, Any]]:
        url = f"https://api.github.com/repos/vega/altair/contents/{directory}"
        resp = await session.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    vl_index, vega_index, altair_files = await asyncio.gather(
        fetch_json(vl_url),
        fetch_json(vega_url),
        fetch_altair_listing(altair_dir),
    )
    return vl_index, vega_index, altair_files


def _build_vegalite_examples(vl_index: Any) -> list[dict[str, Any]]:
    """Build Vega-Lite example list from nested index."""
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
                if slug in seen:
                    seen[slug]["categories"].append(category)
                else:
                    entry = {
                        "gallery_name": "vega-lite",
                        "example_name": title,
                        "example_url": f"https://vega.github.io/vega-lite/examples/{slug}.html",
                        "spec_url": f"https://raw.githubusercontent.com/vega/vega-lite/main/examples/specs/{slug}.vl.json",
                        "categories": [category],
                        "description": item.get("description"),
                        "datasets": [],
                    }
                    seen[slug] = entry
                    examples.append(entry)
    return examples


def build_example_list(
    vl_index: Any,
    vega_index: Any,
    altair_files: list[dict[str, Any]],
    altair_dir: str,
) -> list[dict[str, Any]]:
    """Normalize three gallery indexes into a flat example list."""
    examples = _build_vegalite_examples(vl_index)

    # Vega: index is {category: [list of {name}]}
    seen_vega: set[str] = set()
    for category, items in vega_index.items():
        for item in items:
            slug = item["name"]
            if slug in seen_vega:
                continue
            seen_vega.add(slug)
            examples.append({
                "gallery_name": "vega",
                "example_name": slug.replace("-", " ").replace("_", " ").title(),
                "example_url": f"https://vega.github.io/vega/examples/{slug}/",
                "spec_url": f"https://raw.githubusercontent.com/vega/vega/main/docs/examples/{slug}.vg.json",
                "categories": [category],
                "description": None,
                "datasets": [],
            })

    # Altair: directory listing -> stubs (metadata filled during enrichment)
    for file_info in altair_files:
        name = file_info["name"]
        if not name.endswith(".py") or name.startswith("__"):
            continue
        examples.append({
            "gallery_name": "altair",
            "example_name": name.removesuffix(".py").replace("_", " ").title(),
            "example_url": f"https://altair-viz.github.io/gallery/{name.removesuffix('.py')}.html",
            "spec_url": f"https://raw.githubusercontent.com/vega/altair/main/{altair_dir}/{name}",
            "categories": [],
            "description": None,
            "datasets": [],
            "_filename": name,  # internal, removed before output
        })

    return examples


async def enrich_with_datasets(  # noqa: C901
    examples: list[dict[str, Any]],
    session: niquests.AsyncSession,
    name_map: dict[str, str],
    valid_names: set[str],
) -> None:
    """Fetch specs concurrently and fill in datasets (and Altair metadata)."""
    sem = asyncio.Semaphore(20)

    async def enrich_one(example: dict[str, Any]) -> None:
        async with sem:
            resp = await session.get(example["spec_url"], timeout=TIMEOUT)
            resp.raise_for_status()

        gallery = example["gallery_name"]
        if gallery == "altair":
            assert resp.text is not None
            code = resp.text
            if not _DATA_IMPORT.search(code) and not _CATEGORY_PATTERN.search(code):
                msg = f"Altair response has no data import or category marker: {example['spec_url']}"
                raise ValueError(msg)
            meta = _parse_altair_metadata(code, example.get("_filename", ""))
            example["example_name"] = meta["example_name"]
            example["description"] = meta["description"]
            example["categories"] = meta["categories"]
            example["datasets"] = extract_altair_datasets(code, valid_names)
        elif gallery == "vega-lite":
            spec = resp.json()
            example["datasets"] = extract_vegalite_datasets(spec, name_map)
            if not example.get("description"):
                example["description"] = spec.get("description")
        elif gallery == "vega":
            spec = resp.json()
            example["datasets"] = extract_vega_datasets(spec, name_map)

        # Deduplicate datasets, preserve order
        example["datasets"] = list(dict.fromkeys(example["datasets"]))

    results = await asyncio.gather(
        *(enrich_one(ex) for ex in examples), return_exceptions=True
    )
    # Re-raise BaseException subclasses (KeyboardInterrupt, SystemExit)
    # that return_exceptions=True captured as values
    for r in results:
        if isinstance(r, BaseException) and not isinstance(r, Exception):
            raise r
    errors = [
        (ex, r)
        for ex, r in zip(examples, results, strict=True)
        if isinstance(r, Exception)
    ]
    if errors:
        for ex, err in errors[:5]:
            logger.error("Failed: %s (%s): %s", ex["example_name"], ex["spec_url"], err)
        msg = f"{len(errors)} example(s) failed during enrichment"
        raise RuntimeError(msg)


def assign_ids(examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort by (gallery_name, example_name) and assign sequential IDs."""
    examples.sort(key=operator.itemgetter("gallery_name", "example_name"))
    return [
        {"id": i, **{k: v for k, v in ex.items() if k != "_filename"}}
        for i, ex in enumerate(examples, 1)
    ]


async def async_main() -> None:
    """Main pipeline: config -> name map -> indexes -> examples -> enrich -> write."""
    config = load_config()
    logger.info("Loaded config: %d source URLs", len(config))

    # Build name map from local datapackage.json
    datapackage_path = REPO_ROOT / "datapackage.json"
    with datapackage_path.open() as f:
        datapackage = json.load(f)
    name_map = build_name_map(datapackage)
    valid_names = set(name_map.values())
    logger.info("Built name map: %d datasets", len(valid_names))

    async with niquests.AsyncSession(disable_http2=True) as session:
        # Fetch indexes
        vl_index, vega_index, altair_files = await fetch_indexes(session, config)

        if not isinstance(vl_index, dict):
            msg = f"Expected dict for Vega-Lite index, got {type(vl_index).__name__}"
            raise TypeError(msg)
        if not isinstance(vega_index, dict):
            msg = f"Expected dict for Vega index, got {type(vega_index).__name__}"
            raise TypeError(msg)
        if not isinstance(altair_files, list):
            msg = f"Expected list for Altair file listing, got {type(altair_files).__name__}"
            raise TypeError(msg)

        # Build example list
        examples = build_example_list(
            vl_index, vega_index, altair_files, config["altair_examples_dir"]
        )
        logger.info("Built example list: %d examples", len(examples))

        # Enrich with datasets
        await enrich_with_datasets(examples, session, name_map, valid_names)

    # Assign IDs and write
    examples = assign_ids(examples)

    # Summary
    by_gallery: dict[str, int] = {}
    for ex in examples:
        by_gallery[ex["gallery_name"]] = by_gallery.get(ex["gallery_name"], 0) + 1
    parts = ", ".join(f"{count} {name}" for name, count in sorted(by_gallery.items()))
    logger.info("Collected %d examples (%s)", len(examples), parts)

    expected_galleries = {"vega", "vega-lite", "altair"}
    missing = expected_galleries - by_gallery.keys()
    if missing:
        msg = f"Missing galleries: {', '.join(sorted(missing))} — possible upstream format change"
        raise RuntimeError(msg)

    output_path = REPO_ROOT / "gallery_examples.json"
    output_path.write_text(json.dumps(examples, indent=2, ensure_ascii=False) + "\n")
    logger.info("Wrote %s", output_path)


def main() -> None:
    """Entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
