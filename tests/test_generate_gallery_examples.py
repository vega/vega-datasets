"""Tests for scripts/generate_gallery_examples.py."""

from __future__ import annotations

# The script uses inline script metadata (PEP 723), so we import from the file path.
# Add scripts/ to the path so we can import the module.
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import asyncio
import json

from generate_gallery_examples import (
    REPO_ROOT,
    async_main,
    build_name_map,
    extract_altair_datasets,
    extract_vega_datasets,
    extract_vegalite_datasets,
    normalize_dataset_reference,
)

# Fixture: minimal name map matching real datapackage.json structure
NAME_MAP = {
    "data/cars.json": "cars",
    "data/movies.json": "movies",
    "data/us-state-capitals.json": "us_state_capitals",
    "data/world-110m.json": "world_110m",
    "data/flights-200k.arrow": "flights_200k_arrow",
}


def test_normalize_relative_path():
    assert normalize_dataset_reference("data/cars.json", NAME_MAP) == "cars"


def test_normalize_cdn_url():
    url = "https://cdn.jsdelivr.net/npm/vega-datasets@2.11.0/data/cars.json"
    assert normalize_dataset_reference(url, NAME_MAP) == "cars"


def test_normalize_github_url():
    url = "https://raw.githubusercontent.com/vega/vega-datasets/main/data/cars.json"
    assert normalize_dataset_reference(url, NAME_MAP) == "cars"


def test_normalize_kebab_to_snake():
    assert (
        normalize_dataset_reference("data/us-state-capitals.json", NAME_MAP)
        == "us_state_capitals"
    )


def test_normalize_vega_datasets_unresolved():
    url = "https://cdn.jsdelivr.net/npm/vega-datasets@2.11.0/data/nonexistent.json"
    with pytest.raises(ValueError, match="nonexistent"):
        normalize_dataset_reference(url, NAME_MAP)


def test_normalize_external_url():
    url = "https://example.com/other-data/stuff.json"
    result = normalize_dataset_reference(url, NAME_MAP)
    assert result is None


# ---------------------------------------------------------------------------
# extract_vegalite_datasets
# ---------------------------------------------------------------------------


def test_extract_vegalite_simple():
    spec = {"data": {"url": "data/cars.json"}}
    assert extract_vegalite_datasets(spec, NAME_MAP) == ["cars"]


def test_extract_vegalite_layers():
    spec = {
        "data": {"url": "data/cars.json"},
        "layer": [
            {"mark": "point"},
            {"data": {"url": "data/movies.json"}, "mark": "rule"},
        ],
    }
    result = extract_vegalite_datasets(spec, NAME_MAP)
    assert sorted(result) == ["cars", "movies"]


def test_extract_vegalite_hconcat():
    spec = {
        "hconcat": [
            {"data": {"url": "data/cars.json"}, "mark": "bar"},
            {"data": {"url": "data/movies.json"}, "mark": "point"},
        ]
    }
    result = extract_vegalite_datasets(spec, NAME_MAP)
    assert sorted(result) == ["cars", "movies"]


def test_extract_vegalite_vconcat():
    spec = {
        "vconcat": [
            {"data": {"url": "data/cars.json"}, "mark": "bar"},
            {"data": {"url": "data/movies.json"}, "mark": "point"},
        ]
    }
    result = extract_vegalite_datasets(spec, NAME_MAP)
    assert sorted(result) == ["cars", "movies"]


def test_extract_vegalite_lookup():
    spec = {
        "data": {"url": "data/cars.json"},
        "transform": [
            {
                "lookup": "origin",
                "from": {
                    "data": {"url": "data/movies.json"},
                    "key": "Title",
                },
            }
        ],
    }
    result = extract_vegalite_datasets(spec, NAME_MAP)
    assert sorted(result) == ["cars", "movies"]


def test_extract_vegalite_facet():
    spec = {
        "data": {"url": "data/cars.json"},
        "facet": {"field": "Origin"},
        "spec": {
            "data": {"url": "data/movies.json"},
            "mark": "point",
        },
    }
    result = extract_vegalite_datasets(spec, NAME_MAP)
    assert sorted(result) == ["cars", "movies"]


def test_extract_vegalite_repeat():
    spec = {
        "data": {"url": "data/cars.json"},
        "repeat": ["Horsepower", "Miles_per_Gallon"],
        "spec": {
            "data": {"url": "data/movies.json"},
            "mark": "point",
        },
    }
    result = extract_vegalite_datasets(spec, NAME_MAP)
    assert sorted(result) == ["cars", "movies"]


# ---------------------------------------------------------------------------
# extract_vega_datasets
# ---------------------------------------------------------------------------


def test_extract_vega_simple():
    spec = {
        "data": [
            {"name": "source", "url": "data/cars.json"},
        ]
    }
    assert extract_vega_datasets(spec, NAME_MAP) == ["cars"]


def test_extract_vega_signal():
    spec = {
        "data": [
            {"name": "source", "url": {"signal": "dataset"}},
        ],
        "signals": [
            {
                "name": "dataset",
                "value": "data/cars.json",
                "bind": {
                    "input": "select",
                    "options": ["data/cars.json", "data/movies.json"],
                },
            }
        ],
    }
    result = extract_vega_datasets(spec, NAME_MAP)
    assert sorted(set(result)) == ["cars", "movies"]


def test_extract_vega_lookup_transform():
    spec = {
        "data": [
            {
                "name": "primary",
                "url": "data/cars.json",
                "transform": [
                    {
                        "type": "lookup",
                        "from": {
                            "data": {"url": "data/movies.json"},
                        },
                    }
                ],
            }
        ]
    }
    result = extract_vega_datasets(spec, NAME_MAP)
    assert sorted(result) == ["cars", "movies"]


# ---------------------------------------------------------------------------
# extract_altair_datasets
# ---------------------------------------------------------------------------

VALID_NAMES = {
    "cars",
    "movies",
    "world_110m",
    "us_state_capitals",
    "flights_200k_arrow",
}


def test_extract_altair_data_call():
    code = """\
from vega_datasets import data
source = data.cars()
"""
    assert extract_altair_datasets(code, VALID_NAMES) == ["cars"]


def test_extract_altair_data_url():
    code = """\
from vega_datasets import data
chart = alt.Chart(data.cars.url)
"""
    assert extract_altair_datasets(code, VALID_NAMES) == ["cars"]


def test_extract_altair_topo():
    code = """\
from vega_datasets import data
source = alt.topo_feature(data.world_110m.url, "countries")
"""
    assert extract_altair_datasets(code, VALID_NAMES) == ["world_110m"]


def test_extract_altair_unknown():
    code = """\
from vega_datasets import data
source = data.unknown_thing()
"""
    assert extract_altair_datasets(code, VALID_NAMES) == []


def test_extract_altair_import_no_match():
    code = """\
from vega_datasets import data
# Uses data in some unrecognized way
chart = alt.Chart(data.get_dataset("cars"))
"""
    with pytest.raises(ValueError, match="no recognized dataset pattern"):
        extract_altair_datasets(code, VALID_NAMES)


def test_extract_altair_inline_data_ok():
    code = """\
from vega_datasets import data
import pandas as pd
source = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
chart = alt.Chart(source)
"""
    assert extract_altair_datasets(code, VALID_NAMES) == []


# ---------------------------------------------------------------------------
# build_name_map
# ---------------------------------------------------------------------------


def test_build_name_map():
    # Real datapackage uses filename-only paths (no data/ prefix)
    datapackage = {
        "resources": [
            {"name": "cars", "path": "cars.json"},
            {"name": "us_state_capitals", "path": "us-state-capitals.json"},
            {"name": "flights_200k_arrow", "path": "flights-200k.arrow"},
        ]
    }
    name_map = build_name_map(datapackage)

    # Original path from datapackage
    assert name_map["cars.json"] == "cars"

    # With data/ prefix (for URL normalization)
    assert name_map["data/cars.json"] == "cars"

    # Kebab-case path with data/ prefix
    assert name_map["data/us-state-capitals.json"] == "us_state_capitals"


# ---------------------------------------------------------------------------
# Integration smoke test (hits network)
# ---------------------------------------------------------------------------


@pytest.mark.network
def test_full_pipeline():
    """Smoke test: run the full pipeline against live upstream galleries."""
    asyncio.run(async_main())

    output_path = REPO_ROOT / "gallery_examples.json"
    assert output_path.exists()

    with output_path.open() as f:
        examples = json.load(f)

    # Basic structure
    assert isinstance(examples, list)
    assert len(examples) > 100

    # Required keys only
    required_keys = {
        "id",
        "gallery_name",
        "example_name",
        "example_url",
        "spec_url",
        "categories",
        "description",
        "datasets",
    }
    for ex in examples:
        assert set(ex.keys()) == required_keys, f"Bad keys in {ex.get('example_name')}"

    # No techniques field
    for ex in examples:
        assert "techniques" not in ex

    # Each gallery represented with > 0 examples
    for gallery in ("vega", "vega-lite", "altair"):
        count = sum(1 for ex in examples if ex["gallery_name"] == gallery)
        assert count > 0, f"Gallery {gallery} has 0 examples"

    # Some examples have datasets
    with_datasets = [ex for ex in examples if ex["datasets"]]
    assert len(with_datasets) > 50

    # IDs are sequential
    ids = [ex["id"] for ex in examples]
    assert ids == list(range(1, len(examples) + 1))
