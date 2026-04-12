"""Tests for scripts/generate_gallery_examples.py."""

from __future__ import annotations

import asyncio
import json

import pytest

from scripts.generate_gallery_examples import (
    REPO_ROOT,
    _build_vegalite_examples,  # noqa: PLC2701
    _parse_altair_metadata,  # noqa: PLC2701
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


def test_normalize_bare_filename_with_data_prefix_fallback():
    """A bare filename not in name_map resolves via data/ prefix lookup."""
    assert normalize_dataset_reference("cars.json", NAME_MAP) == "cars"


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


def test_extract_vegalite_concat():
    spec = {
        "concat": [
            {"data": {"url": "data/cars.json"}, "mark": "bar"},
            {"data": {"url": "data/movies.json"}, "mark": "point"},
        ]
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
# _parse_altair_metadata
# ---------------------------------------------------------------------------


def test_parse_altair_metadata_title():
    code = '"""\nScatter Plot\n------------\nA scatter plot.\n"""\n# category: basic\n'
    result = _parse_altair_metadata(code, "scatter_plot.py")
    assert result["example_name"] == "Scatter Plot"


def test_parse_altair_metadata_title_fallback():
    """When no docstring title exists, falls back to humanized filename."""
    code = "import altair as alt\n"
    result = _parse_altair_metadata(code, "scatter_plot.py")
    assert result["example_name"] == "Scatter Plot"


def test_parse_altair_metadata_description():
    code = '"""\nScatter Plot\n------------\nA basic scatter plot example.\n"""\n'
    result = _parse_altair_metadata(code, "scatter_plot.py")
    assert result["description"] == "A basic scatter plot example."


def test_parse_altair_metadata_description_null():
    """Description is None when docstring has no body after the underline."""
    code = '"""\nScatter Plot\n------------\n"""\n'
    result = _parse_altair_metadata(code, "scatter_plot.py")
    assert result["description"] is None


def test_parse_altair_metadata_category():
    code = '"""\nTitle\n-----\n"""\n# category: interactive charts\n'
    result = _parse_altair_metadata(code, "example.py")
    assert result["categories"] == ["interactive charts"]


def test_parse_altair_metadata_no_category():
    code = '"""\nTitle\n-----\n"""\nimport altair\n'
    result = _parse_altair_metadata(code, "example.py")
    assert result["categories"] == []


# ---------------------------------------------------------------------------
# _build_vegalite_examples
# ---------------------------------------------------------------------------


def test_build_vegalite_examples_empty_subcategory_fallback():
    """When a subcategory key is empty string, fall back to section name."""
    vl_index = {
        "Single-View Plots": {
            "": [{"name": "bar_simple", "title": "Simple Bar"}],
        }
    }
    examples = _build_vegalite_examples(vl_index)
    assert len(examples) == 1
    assert examples[0]["categories"] == ["Single-View Plots"]


# ---------------------------------------------------------------------------
# build_name_map
# ---------------------------------------------------------------------------


def test_build_name_map():
    datapackage = {
        "resources": [
            {"name": "cars", "path": "cars.json"},
            {"name": "us_state_capitals", "path": "us-state-capitals.json"},
        ]
    }
    name_map = build_name_map(datapackage)

    # Each resource produces 2-3 entries: path, data/filename, filename
    # (bare filenames like "cars.json" collide with the path, producing 2)
    assert name_map == {
        "cars.json": "cars",
        "data/cars.json": "cars",
        "us-state-capitals.json": "us_state_capitals",
        "data/us-state-capitals.json": "us_state_capitals",
    }


def test_build_name_map_skips_empty_path():
    datapackage = {"resources": [{"name": "x", "path": ""}, {"name": "y"}]}
    assert build_name_map(datapackage) == {}


# ---------------------------------------------------------------------------
# Integration smoke test (hits network)
# ---------------------------------------------------------------------------


@pytest.mark.network
def test_full_pipeline():
    """Smoke test: run the full pipeline against live upstream galleries."""
    asyncio.run(async_main())

    output_path = REPO_ROOT / "data" / "gallery_examples.json"
    assert output_path.exists()

    with output_path.open() as f:
        examples = json.load(f)

    # Basic structure
    assert isinstance(examples, list)
    assert len(examples) > 100

    # Required keys only
    required_keys = {
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

    # No legacy id field (dropped in favor of spec_url as primary key)
    for ex in examples:
        assert "id" not in ex

    # Each gallery represented with > 0 examples
    for gallery in ("vega", "vega-lite", "altair"):
        count = sum(1 for ex in examples if ex["gallery_name"] == gallery)
        assert count > 0, f"Gallery {gallery} has 0 examples"

    # Some examples have datasets
    with_datasets = [ex for ex in examples if ex["datasets"]]
    assert len(with_datasets) > 50

    # spec_url is the declared primary key — must be unique across all entries
    spec_urls = [ex["spec_url"] for ex in examples]
    assert len(set(spec_urls)) == len(spec_urls), "duplicate spec_url in output"

    # Output is sorted deterministically by (gallery_name, example_name)
    sort_keys = [(ex["gallery_name"], ex["example_name"]) for ex in examples]
    assert sort_keys == sorted(sort_keys), "output is not deterministically sorted"
