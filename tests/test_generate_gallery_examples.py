"""Tests for scripts/generate_gallery_examples.py."""

from __future__ import annotations

import asyncio
import json
import os
from unittest.mock import AsyncMock

import httpx
import pytest

from scripts import generate_gallery_examples as gallery_examples
from scripts.generate_gallery_examples import (
    _build_vegalite_examples,  # noqa: PLC2701
    _fetch_text,  # noqa: PLC2701
    _format_refs,  # noqa: PLC2701
    _raw_github_fallback,  # noqa: PLC2701
    assert_expected_galleries,
    assert_unique_urls,
    build_example_list,
    build_name_map,
    extract_vega_datasets,
    extract_vegalite_datasets,
    load_config,
    normalize_dataset_reference,
    run_pipeline,
)

# Fixture: fake resolved-refs struct matching resolve_refs() return shape.
FAKE_REFS = {
    "vega-lite": {"commit": "abcdef0123456789"},
    "vega": {"commit": "1234567890abcdef"},
    "altair": {"commit": "fedcba9876543210"},
}

# Fixture: minimal name map matching real datapackage.json structure
NAME_MAP = {
    "data/cars.json": "cars",
    "data/movies.json": "movies",
    "data/us-state-capitals.json": "us_state_capitals",
    "data/world-110m.json": "world_110m",
    "data/flights-200k.arrow": "flights_200k_arrow",
    "data/ffox.png": "ffox",
    "data/gimp.png": "gimp",
    "data/7zip.png": "icon_7zip",
}
VALID_NAMES = set(NAME_MAP.values())


def _altair_index(*records):
    return {
        "gallery": {
            "name": "altair",
            "repository": "https://github.com/vega/altair",
            "docs_url": "https://altair-viz.github.io/",
        },
        "examples": list(records),
    }


def _altair_record(**overrides):
    record = {
        "name": "scatter_plot",
        "title": "Scatter Plot",
        "url": "https://altair-viz.github.io/gallery/scatter_plot.html",
        "path": "tests/examples_arguments_syntax/scatter_plot.py",
        "description": "A scatter plot example.",
        "categories": ["scatter plots"],
        "datasets": ["cars"],
        "related_docs": {"explicit": [], "inferred": []},
    }
    record.update(overrides)
    return record


def test_normalize_relative_path():
    assert normalize_dataset_reference("data/cars.json", NAME_MAP) == "cars"


def test_normalize_cdn_url():
    url = "https://cdn.jsdelivr.net/npm/vega-datasets@2.11.0/data/cars.json"
    assert normalize_dataset_reference(url, NAME_MAP) == "cars"


def test_normalize_unversioned_cdn_url():
    url = "https://cdn.jsdelivr.net/npm/vega-datasets/data/cars.json"
    assert normalize_dataset_reference(url, NAME_MAP) == "cars"


def test_normalize_github_url():
    url = "https://raw.githubusercontent.com/vega/vega-datasets/main/data/cars.json"
    assert normalize_dataset_reference(url, NAME_MAP) == "cars"


def test_normalize_github_pages_url():
    url = "https://vega.github.io/vega-datasets/data/cars.json"
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


def test_extract_vegalite_inline_asset_references():
    """Image paths nested in inline values are dataset references too."""
    spec = {
        "data": {
            "values": [
                {
                    "name": "Firefox",
                    "image": "data/ffox.png",
                    "metadata": {
                        "icon": (
                            "https://cdn.jsdelivr.net/npm/vega-datasets@2.11.0/"
                            "data/gimp.png"
                        ),
                        "homepage": "https://example.com/data/not-a-dataset.png",
                        "note": "data is embedded inline",
                    },
                },
                {"name": "7-Zip", "image": "data/7zip.png"},
            ]
        }
    }

    assert extract_vegalite_datasets(spec, NAME_MAP) == [
        "ffox",
        "gimp",
        "icon_7zip",
    ]


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


def test_extract_vega_inline_asset_references():
    """Vega inline values receive the same recursive asset handling."""
    spec = {
        "data": [
            {
                "name": "icons",
                "values": [{"image": "data/ffox.png"}, ["data/gimp.png"]],
            }
        ]
    }

    assert extract_vega_datasets(spec, NAME_MAP) == ["ffox", "gimp"]


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


def test_extract_vega_nested_group_data():
    """Group marks can load data and contain further group scopes."""
    spec = {
        "data": [],
        "marks": [
            {
                "type": "group",
                "data": [{"name": "cars", "url": "data/cars.json"}],
                "marks": [
                    {
                        "type": "group",
                        "signals": [{"name": "dataset", "value": "data/movies.json"}],
                        "data": [{"name": "movies", "url": {"signal": "dataset"}}],
                    }
                ],
            }
        ],
    }

    assert extract_vega_datasets(spec, NAME_MAP) == ["cars", "movies"]


# ---------------------------------------------------------------------------
# _build_vegalite_examples
# ---------------------------------------------------------------------------


_VL_SHA = "abcdef0123456789"


def test_build_vegalite_examples_empty_subcategory_fallback():
    """When a subcategory key is empty string, fall back to section name."""
    vl_index = {
        "Single-View Plots": {
            "": [{"name": "bar_simple", "title": "Simple Bar"}],
        }
    }
    examples = _build_vegalite_examples(vl_index, _VL_SHA)
    assert len(examples) == 1
    assert examples[0]["categories"] == ["Single-View Plots"]


def test_build_vegalite_examples_longest_title_wins():
    """When the same slug appears twice with different titles, longest wins."""
    vl_index = {
        "Layered Plots": {
            "Bar Charts": [
                {"name": "layer_bar_labels", "title": "Bar Chart with Labels"}
            ],
        },
        "Examples": {
            "Layered": [
                {
                    "name": "layer_bar_labels",
                    "title": "Simple Bar Chart with Labels",
                }
            ],
        },
    }
    examples = _build_vegalite_examples(vl_index, _VL_SHA)
    assert len(examples) == 1
    assert examples[0]["example_name"] == "Simple Bar Chart with Labels"
    assert examples[0]["categories"] == ["Bar Charts", "Layered"]


def test_build_vegalite_examples_dedupe_categories():
    """Duplicate (section, category) pairs don't produce repeated entries."""
    vl_index = {
        "A": {"Bar Charts": [{"name": "foo", "title": "Foo"}]},
        "B": {"Bar Charts": [{"name": "foo", "title": "Foo"}]},
    }
    examples = _build_vegalite_examples(vl_index, _VL_SHA)
    assert len(examples) == 1
    assert examples[0]["categories"] == ["Bar Charts"]


def test_build_vegalite_examples_spec_url_uses_jsdelivr_with_sha():
    """Spec URL must embed the vega-lite commit SHA, not `main`."""
    vl_index = {"Single-View Plots": {"": [{"name": "bar_simple"}]}}
    examples = _build_vegalite_examples(vl_index, _VL_SHA)
    assert (
        examples[0]["spec_url"]
        == f"https://cdn.jsdelivr.net/gh/vega/vega-lite@{_VL_SHA}/examples/specs/bar_simple.vl.json"
    )


def test_build_vegalite_examples_skips_non_dict_items():
    """Non-dict entries in an items list are skipped, matching the vega parser."""
    vl_index = {
        "Single-View Plots": {
            "Bar Charts": [
                "stray_string",
                None,
                ["nested", "list"],
                {"name": "bar_simple", "title": "Simple Bar"},
            ],
        }
    }
    examples = _build_vegalite_examples(vl_index, _VL_SHA)
    assert [e["example_name"] for e in examples] == ["Simple Bar"]


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
# assert_unique_urls
# ---------------------------------------------------------------------------


def test_assert_unique_urls_passes_on_unique():
    assert_unique_urls([
        {"example_url": "https://g/a.html", "spec_url": "https://example.com/a"},
        {"example_url": "https://g/b.html", "spec_url": "https://example.com/b"},
    ])


def test_assert_unique_urls_raises_on_duplicate_spec_url():
    with pytest.raises(RuntimeError, match=r"spec_url.*uniqueness invariant"):
        assert_unique_urls([
            {"example_url": "https://g/a.html", "spec_url": "https://example.com/a"},
            {"example_url": "https://g/b.html", "spec_url": "https://example.com/b"},
            {"example_url": "https://g/c.html", "spec_url": "https://example.com/a"},
        ])


def test_assert_unique_urls_raises_on_duplicate_example_url():
    """The stable example URL must remain unique within a snapshot."""
    with pytest.raises(RuntimeError, match=r"example_url.*uniqueness invariant"):
        assert_unique_urls([
            {"example_url": "https://g/a.html", "spec_url": "https://example.com/a"},
            {"example_url": "https://g/a.html", "spec_url": "https://example.com/b"},
        ])


def test_committed_registry_satisfies_pipeline_invariants():
    """Keep the checked-in snapshot behind the generator's safety rails."""
    examples = json.loads(
        (gallery_examples.REPO_ROOT / "data" / "gallery-examples.json").read_text(
            encoding="utf-8"
        )
    )

    assert_expected_galleries(examples)
    assert_unique_urls(examples)


# ---------------------------------------------------------------------------
# assert_expected_galleries (per-gallery count floor)
# ---------------------------------------------------------------------------


def _fake_examples(counts: dict[str, int]) -> list[dict[str, str]]:
    """Build a minimal example list with the given per-gallery counts."""
    return [{"gallery_name": name} for name, n in counts.items() for _ in range(n)]


def test_assert_expected_galleries_passes_at_floor():
    """Every gallery exactly at its floor passes."""
    assert_expected_galleries(
        _fake_examples({"altair": 160, "vega": 80, "vega-lite": 160})
    )


def test_assert_expected_galleries_raises_when_one_below_floor():
    """One gallery under its floor trips a detailed error."""
    examples = _fake_examples({"altair": 160, "vega": 10, "vega-lite": 160})
    with pytest.raises(RuntimeError, match=r"vega: got 10, expected >= 80"):
        assert_expected_galleries(examples)


def test_assert_expected_galleries_raises_when_gallery_missing():
    """A missing gallery counts as zero and trips the floor check."""
    examples = _fake_examples({"altair": 160, "vega-lite": 160})
    with pytest.raises(RuntimeError, match=r"vega: got 0, expected >= 80"):
        assert_expected_galleries(examples)


def test_assert_expected_galleries_raises_with_multiple_gaps():
    """Multiple below-floor galleries all appear in the error message."""
    examples = _fake_examples({"altair": 10, "vega": 10, "vega-lite": 160})
    with pytest.raises(
        RuntimeError,
        match=r"altair: got 10.*vega: got 10",
    ):
        assert_expected_galleries(examples)


# ---------------------------------------------------------------------------
# SHA pinning: load_config, _format_refs, build_example_list URL shapes
# ---------------------------------------------------------------------------


def test_load_config_parses_ref_and_sources():
    """Real TOML file must yield both [ref] and [sources] tables with
    underscore→hyphen normalized keys."""
    config = load_config()
    assert set(config["refs"].keys()) == {"vega-lite", "vega", "altair"}
    # Defaults ship as `main`; tag-pinning is a supported override.
    for ref in config["refs"].values():
        assert isinstance(ref, str) and ref
    assert "vega_lite_examples_url" in config["sources"]
    assert "vega_examples_url" in config["sources"]
    assert "altair_examples_url" in config["sources"]


def test_load_config_urls_use_jsdelivr_template():
    """Source URL templates route through jsDelivr, not raw.githubusercontent."""
    config = load_config()
    assert "cdn.jsdelivr.net/gh/" in config["sources"]["vega_lite_examples_url"]
    assert "cdn.jsdelivr.net/gh/" in config["sources"]["vega_examples_url"]
    assert "cdn.jsdelivr.net/gh/" in config["sources"]["altair_examples_url"]
    assert "{vega_lite_ref}" in config["sources"]["vega_lite_examples_url"]
    assert "{vega_ref}" in config["sources"]["vega_examples_url"]
    assert "{altair_ref}" in config["sources"]["altair_examples_url"]


def test_format_refs_maps_hyphen_keys_to_placeholder_names():
    """_format_refs bridges resolve_refs output → str.format kwargs."""
    fmt = _format_refs(FAKE_REFS)
    assert fmt == {
        "vega_lite_ref": "abcdef0123456789",
        "vega_ref": "1234567890abcdef",
        "altair_ref": "fedcba9876543210",
    }


def test_build_example_list_vega_spec_url_uses_jsdelivr_with_sha():
    """Vega example spec_urls embed the resolved vega SHA via jsDelivr."""
    vl_index: dict[str, dict[str, list[dict[str, str]]]] = {}
    vega_index = {"Basic": [{"name": "bar"}]}
    examples = build_example_list(
        vl_index,
        vega_index,
        _altair_index(),
        FAKE_REFS,
        VALID_NAMES,
    )
    vega_entries = [ex for ex in examples if ex["gallery_name"] == "vega"]
    assert len(vega_entries) == 1
    assert (
        vega_entries[0]["spec_url"]
        == "https://cdn.jsdelivr.net/gh/vega/vega@1234567890abcdef/docs/examples/bar.vg.json"
    )


def test_build_example_list_maps_altair_published_index():
    """Altair metadata is copied while spec_url pins its canonical source."""
    index = _altair_index(_altair_record(description=""))
    examples = build_example_list({}, {}, index, FAKE_REFS, VALID_NAMES)
    altair_entries = [ex for ex in examples if ex["gallery_name"] == "altair"]
    assert len(altair_entries) == 1
    scatter = altair_entries[0]
    assert scatter["spec_url"] == (
        "https://cdn.jsdelivr.net/gh/vega/altair@fedcba9876543210/"
        "tests/examples_arguments_syntax/scatter_plot.py"
    )
    assert scatter["example_name"] == "Scatter Plot"
    assert scatter["example_url"].endswith("/gallery/scatter_plot.html")
    assert scatter["categories"] == ["scatter plots"]
    assert scatter["datasets"] == ["cars"]
    assert scatter["description"] is None


def test_build_example_list_rejects_altair_method_source_as_canonical():
    index = _altair_index(
        _altair_record(path="tests/examples_methods_syntax/scatter_plot.py")
    )
    with pytest.raises(ValueError, match="non-canonical source path"):
        build_example_list({}, {}, index, FAKE_REFS, VALID_NAMES)


def test_build_example_list_rejects_unknown_altair_dataset():
    index = _altair_index(_altair_record(datasets=["unknown_dataset"]))
    with pytest.raises(ValueError, match="unknown datasets"):
        build_example_list({}, {}, index, FAKE_REFS, VALID_NAMES)


# ---------------------------------------------------------------------------
# jsDelivr → raw.githubusercontent mirror fallback
# ---------------------------------------------------------------------------


def test_raw_github_fallback_translates_jsdelivr_gh_url():
    assert (
        _raw_github_fallback(
            "https://cdn.jsdelivr.net/gh/vega/vega-lite@abc123/examples/specs/bar.vl.json"
        )
        == "https://raw.githubusercontent.com/vega/vega-lite/abc123/examples/specs/bar.vl.json"
    )


def test_raw_github_fallback_none_for_other_hosts():
    assert _raw_github_fallback("https://api.github.com/repos/vega/vega") is None
    assert (
        _raw_github_fallback(
            "https://cdn.jsdelivr.net/npm/vega-datasets@2/data/cars.json"
        )
        is None
    )


def test_raw_github_fallback_none_for_malformed_gh_url():
    # No @ref, or no path after the slug — nothing sane to mirror.
    assert (
        _raw_github_fallback("https://cdn.jsdelivr.net/gh/vega/vega-lite/file.json")
        is None
    )
    assert (
        _raw_github_fallback("https://cdn.jsdelivr.net/gh/vega/vega-lite@abc123")
        is None
    )


def _run_fetch_with_transport(handler, url):
    """Run _fetch_text against a mock transport; returns the body text."""

    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as session:
            return await _fetch_text(session, url)

    return asyncio.run(go())


def test_fetch_falls_back_to_raw_github_on_jsdelivr_403():
    jsd = "https://cdn.jsdelivr.net/gh/vega/vega@abc123/docs/examples/pie-chart.vg.json"
    raw = "https://raw.githubusercontent.com/vega/vega/abc123/docs/examples/pie-chart.vg.json"
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        if str(request.url) == jsd:
            return httpx.Response(403, text="Forbidden")
        assert str(request.url) == raw
        return httpx.Response(200, text='{"ok": true}')

    assert _run_fetch_with_transport(handler, jsd) == '{"ok": true}'
    assert seen == [jsd, raw]


def test_fetch_does_not_fall_back_on_404():
    """404 is a real miss, not a CDN flake — must propagate, not mask."""
    jsd = "https://cdn.jsdelivr.net/gh/vega/vega@abc123/docs/examples/gone.vg.json"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="Not found")

    with pytest.raises(httpx.HTTPStatusError):
        _run_fetch_with_transport(handler, jsd)


def test_fetch_no_fallback_host_reraises():
    """Transient status on a non-jsDelivr host has no mirror — propagate."""
    url = "https://api.github.com/repos/vega/vega/commits/main"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="rate limited")

    with pytest.raises(httpx.HTTPStatusError):
        _run_fetch_with_transport(handler, url)


def test_build_example_list_vega_merges_categories_for_repeated_slug():
    """A vega slug listed under two categories merges them (mirrors vega-lite)."""
    vega_index = {
        "Basic": [{"name": "bar"}],
        "Advanced": [{"name": "bar"}, {"name": "pie"}],
    }
    examples = build_example_list(
        {},
        vega_index,
        _altair_index(),
        FAKE_REFS,
        VALID_NAMES,
    )
    bar = next(ex for ex in examples if ex["example_url"].endswith("/bar/"))
    assert bar["categories"] == ["Basic", "Advanced"]
    assert sum(ex["gallery_name"] == "vega" for ex in examples) == 2


# ---------------------------------------------------------------------------
# Output serialization
# ---------------------------------------------------------------------------


def test_async_main_writes_utf8(tmp_path, monkeypatch):
    (tmp_path / "data").mkdir()
    monkeypatch.setattr(gallery_examples, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        gallery_examples,
        "run_pipeline",
        AsyncMock(return_value=[{"description": "Estimating π via random sampling."}]),
    )

    asyncio.run(gallery_examples.async_main())

    output = tmp_path / "data" / "gallery-examples.json"
    assert "π" in output.read_text(encoding="utf-8")
    assert b"\r\n" not in output.read_bytes()


# ---------------------------------------------------------------------------
# Opt-in end-to-end integration test (hits live GitHub API + CDNs)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not os.environ.get("GALLERY_INTEGRATION"),
    reason="live-network pipeline test; opt in with GALLERY_INTEGRATION=1",
)
def test_run_pipeline_integration():
    """
    Full pipeline against live upstream galleries.

    The unit tests cover the pure layer only; this is the one check that
    exercises ref resolution, index fetching, and enrichment for real —
    the layer where upstream restructuring or CDN behavior changes surface.
    The pipeline's own invariants (count floors, URL uniqueness) run inside
    run_pipeline; here we assert the output shape on top.
    """
    examples = asyncio.run(run_pipeline())
    expected_fields = {
        "gallery_name",
        "example_name",
        "example_url",
        "spec_url",
        "categories",
        "description",
        "datasets",
    }
    assert all(set(ex) == expected_fields for ex in examples)
    referenced = {name for ex in examples for name in ex["datasets"]}
    assert "cars" in referenced  # canary: the most-used dataset must appear
