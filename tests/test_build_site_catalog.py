"""Offline tests for the website catalog builder (scripts/build_site_catalog.py)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from io import BytesIO
from typing import TYPE_CHECKING

import polars as pl
from PIL import Image

from scripts.build_site_catalog import (
    HIST_BINS,
    build_dataset,
    data_url,
    editor_spec_url,
    example_slug,
    geo_features,
    missing_values,
    parse_dates,
    preview_rows,
    profile_field,
    read_table,
    readme_markdown,
    thumbnail_urls,
    write_thumbnail,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_geo_features_counts_the_shapes_a_map_draws() -> None:
    topo = {
        "type": "Topology",
        "objects": {
            "counties": {
                "type": "GeometryCollection",
                "geometries": [{"type": "Polygon"}] * 3,
            },
            "land": {"type": "MultiPolygon"},
        },
    }
    assert geo_features(topo, "topojson") == {
        "objects": ["counties", "land"],
        "objectFeatures": {"counties": 3, "land": 1},
    }
    geo = {"type": "FeatureCollection", "features": [{"type": "Feature"}] * 5}
    assert geo_features(geo, "geojson") == {"features": 5}
    assert geo_features({"type": "Feature"}, "geojson") == {"features": 1}


def test_example_slug() -> None:
    assert (
        example_slug("https://vega.github.io/vega/examples/bar-chart/") == "bar-chart"
    )
    assert (
        example_slug("https://altair-viz.github.io/gallery/area_chart.html")
        == "area_chart"
    )
    assert example_slug("https://vega.github.io/vega-lite/examples/bar.html") == "bar"


def test_thumbnail_urls_follow_the_registry_commit() -> None:
    vl = "https://cdn.jsdelivr.net/gh/vega/vega-lite@abc123/examples/specs/bar.vl.json"
    assert thumbnail_urls("vega-lite", "bar", vl) == [
        "https://raw.githubusercontent.com/vega/vega-lite/abc123/examples/compiled/bar.png"
    ]
    vg = "https://cdn.jsdelivr.net/gh/vega/vega@def456/docs/examples/bar-chart.vg.json"
    assert thumbnail_urls("vega", "bar-chart", vg) == [
        "https://raw.githubusercontent.com/vega/vega/def456/docs/examples/img/bar-chart.png"
    ]
    raw_vg = "https://raw.githubusercontent.com/vega/vega/def456/docs/examples/bar-chart.vg.json"
    assert thumbnail_urls("vega", "bar-chart", raw_vg) == thumbnail_urls(
        "vega", "bar-chart", vg
    )
    py = "https://cdn.jsdelivr.net/gh/vega/altair@0a1b2c/tests/examples_arguments_syntax/x.py"
    assert thumbnail_urls("altair", "x", py) == [
        "https://altair-viz.github.io/_static/x-thumb.png",
        "https://altair-viz.github.io/_static/x-thumb.svg",
    ]


def test_editor_spec_url() -> None:
    assert editor_spec_url("vega", "bar-chart") == (
        "https://vega.github.io/editor/spec/vega/bar-chart.vg.json"
    )
    assert editor_spec_url("vega-lite", "bar") == (
        "https://vega.github.io/editor/spec/vega-lite/bar.vl.json"
    )
    assert editor_spec_url("altair", "bar") is None


def test_data_url_prefers_the_released_cdn_file() -> None:
    released = {"cars.json"}
    assert data_url("cars.json", "3", released) == (
        "https://cdn.jsdelivr.net/npm/vega-datasets@3/data/cars.json"
    )
    assert data_url("new.json", "3", released) == (
        "https://vega.github.io/vega-datasets/data/new.json"
    )


def test_profile_quantitative() -> None:
    s = pl.Series("x", ["1", "2", "2", "10", None, "n/a"])
    p = profile_field(s, "number")
    assert p["kind"] == "quantitative"
    assert (p["min"], p["max"], p["missing"]) == (1.0, 10.0, 2)
    assert len(p["bins"]) == HIST_BINS
    assert sum(p["bins"]) == 4
    assert p["bins"][0] == 1
    assert p["bins"][-1] == 1


def test_profile_constant_and_empty_numbers() -> None:
    assert profile_field(pl.Series("x", ["5", "5"]), "integer")["bins"] == [2]
    assert profile_field(pl.Series("x", [None, "?"]), "number") == {
        "kind": "empty",
        "missing": 2,
    }


def test_profile_temporal_mixed_formats() -> None:
    s = pl.Series("d", ["2020-01-01", "2020-06-30", None])
    p = profile_field(s, "date")
    assert p["kind"] == "temporal"
    assert p["min"].startswith("2020-01-01")
    assert p["max"].startswith("2020-06-30")
    assert p["missing"] == 1
    assert sum(p["bins"]) == 2


def test_parse_dates_picks_the_best_format() -> None:
    parsed = parse_dates(pl.Series("d", ["Jan 05 2001", "Feb 11 2002", "Mar 30 2003"]))
    assert parsed.null_count() == 0


def test_profile_nominal() -> None:
    s = pl.Series("c", ["a", "b", "a", "", None, "c"])
    p = profile_field(s, "string")
    assert (p["kind"], p["distinct"], p["missing"]) == ("nominal", 3, 2)
    assert p["top"][0] == ["a", 2]
    assert sorted(p["top"][1:]) == [["b", 1], ["c", 1]]


def test_read_table_json(tmp_path: Path) -> None:
    rows = tmp_path / "rows.json"
    rows.write_text(json.dumps([{"a": 1, "b": [1, 2]}, {"a": 2, "c": "x"}]), "utf-8")
    df = read_table(rows, "json")
    assert df is not None
    assert df.columns == ["a", "b", "c"]
    assert df["b"].to_list() == ["[1, 2]", None]
    other = tmp_path / "tree.json"
    other.write_text(json.dumps({"name": "root"}), "utf-8")
    assert read_table(other, "json") is None


def test_preview_rows_truncates_long_cells() -> None:
    df = pl.DataFrame({"a": ["x" * 100], "b": [None]})
    [[a, b]] = preview_rows(df, ["a", "b"])
    assert len(a) == 48
    assert a.endswith("…")
    assert not b


def test_write_thumbnail_png(tmp_path: Path) -> None:
    buf = BytesIO()
    Image.new("RGBA", (960, 480), (0, 0, 0, 0)).save(buf, "PNG")
    name, size = write_thumbnail(buf.getvalue(), ".png", tmp_path / "thumbs" / "bar")
    assert name == "bar.webp"
    assert size == [480, 240]
    with Image.open(tmp_path / "thumbs" / name) as im:
        # Transparent pixels are flattened onto white, so thumbnails read on dark cards.
        assert im.convert("RGB").getpixel((0, 0)) == (255, 255, 255)


def test_write_thumbnail_svg_is_kept(tmp_path: Path) -> None:
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>'
    name, size = write_thumbnail(svg, ".svg", tmp_path / "emoji")
    assert (name, size) == ("emoji.svg", None)
    assert (tmp_path / name).read_bytes() == svg


def test_profile_nominal_ties_are_ordered_by_value() -> None:
    # A column named "count" must not collide with the tally column.
    p = profile_field(pl.Series("count", ["b", "a", "c", "b", "a"]), "string")
    assert p["top"] == [["a", 2], ["b", 2], ["c", 1]]


def test_profile_native_datetimes() -> None:
    s = pl.Series("d", ["2020-01-01", "2021-01-01"]).str.to_datetime(time_zone="UTC")
    p = profile_field(s, "datetime")
    assert p["kind"] == "temporal"
    assert p["min"].startswith("2020-01-01")


def test_profile_temporal_names_its_zone() -> None:
    # Browsers read a date-time without a zone as local time: a day early east of UTC.
    p = profile_field(pl.Series("d", ["2012-01-01", "2015-12-31"]), "date")
    assert (p["min"], p["max"]) == ("2012-01-01T00:00:00Z", "2015-12-31T00:00:00Z")
    aware = pl.Series("d", ["2000-01-01T08:00:00"]).str.to_datetime(time_zone="UTC")
    value = profile_field(aware, "datetime")["min"]
    assert value.endswith(("Z", "+00:00"))
    assert datetime.fromisoformat(value) == datetime(2000, 1, 1, 8, tzinfo=UTC)


def test_readme_markdown() -> None:
    lines = [
        "# Vega Datasets",
        "[![npm](https://img.shields.io/npm/v/vega-datasets.svg)](https://npmjs.com)",
        "Intro with [cars](datapackage.md#carsjson) and [rules](CONTRIBUTING.md).",
        "Browse the [dataset catalog](https://vega.github.io/vega-datasets/).",
        "> [!IMPORTANT]",
        "> **Licensing**: see [the metadata](datapackage.md).",
        "Unknown anchor: [x](datapackage.md#nopejson), external [y](https://x.org/a.md).",
        "```js",
        "const [a](b) = 1;",
        "```",
    ]
    out = readme_markdown("\n".join(lines), {"cars.json": "cars"})
    assert out.splitlines() == [
        "Intro with [cars](datasets/cars/) and [rules](https://github.com/vega/vega-datasets/blob/main/CONTRIBUTING.md).",
        "Browse the [dataset catalog](./).",
        "> **Licensing**: see [the metadata](https://github.com/vega/vega-datasets/blob/main/datapackage.md).",
        "Unknown anchor: [x](https://github.com/vega/vega-datasets/blob/main/datapackage.md#nopejson), external [y](https://x.org/a.md).",
        "```js",
        "const [a](b) = 1;",
        "```",
    ]


# ---------------------------------------------------------------------------
# Standard Data Package properties: copied through when present, absent otherwise
# ---------------------------------------------------------------------------

FIXTURE_CSV = "id,parent,hp,grade,when\n1,,100,low,2020/01/02 10:00\n2,1,-99,high,2020/01/03 11:00\n3,1,NA,,\n"


def _resource(path: Path, **extra: object) -> dict[str, object]:
    return {
        "name": "fixture",
        "path": str(path),
        "format": ".csv",
        "type": "table",
        "bytes": path.stat().st_size,
        **extra,
    }


def _fixture(tmp_path: Path) -> Path:
    path = tmp_path / "fixture.csv"
    path.write_text(FIXTURE_CSV, "utf-8")
    return path


BARE_FIELDS = [
    {"name": "id", "type": "integer"},
    {"name": "parent", "type": "integer"},
    {"name": "hp", "type": "number"},
    {"name": "grade", "type": "string"},
    {"name": "when", "type": "datetime"},
]


def test_build_dataset_without_metadata_adds_no_keys(tmp_path: Path) -> None:
    entry = build_dataset(
        _resource(_fixture(tmp_path), schema={"fields": BARE_FIELDS}),
        [],
        "https://example.invalid/fixture.csv",
        tmp_path,
    )
    assert list(entry) == [
        "name",
        "file",
        "url",
        "format",
        "kind",
        "bytes",
        "description",
        "licenses",
        "sources",
        "usedBy",
        "fields",
        "rows",
        "preview",
    ]
    for field in entry["fields"]:
        assert list(field) == ["name", "type", "description", "profile"]
    # Without missingValues only nulls (and text that isn't a number) are missing.
    hp = next(f for f in entry["fields"] if f["name"] == "hp")
    assert (hp["profile"]["min"], hp["profile"]["missing"]) == (-99.0, 1)


def test_build_dataset_passes_standard_properties_through(tmp_path: Path) -> None:
    categories = [{"value": "low", "label": "Low"}, {"value": "high", "label": "High"}]
    foreign_keys = [
        {"fields": ["parent"], "reference": {"resource": "", "fields": ["id"]}},
        {"fields": "grade", "reference": {"resource": "grades", "fields": "name"}},
    ]
    fields = [
        {
            "name": "id",
            "type": "integer",
            "title": "Identifier",
            "constraints": {"required": True, "unique": True},
        },
        {"name": "parent", "type": "integer"},
        {
            "name": "hp",
            "type": "number",
            "title": "Horsepower (hp)",
            "description": "Engine power.",
            "constraints": {"minimum": 0, "maximum": 500},
            "missingValues": ["-99", "NA"],
        },
        {
            "name": "grade",
            "type": "string",
            "categories": categories,
            "categoriesOrdered": True,
        },
        {"name": "when", "type": "datetime", "format": "%Y/%m/%d %H:%M"},
    ]
    entry = build_dataset(
        _resource(
            _fixture(tmp_path),
            title="A fully described fixture",
            schema={
                "fields": fields,
                "primaryKey": ["id"],
                "foreignKeys": foreign_keys,
                "missingValues": ["", "NA"],
            },
        ),
        [],
        "https://example.invalid/fixture.csv",
        tmp_path,
    )
    assert entry["title"] == "A fully described fixture"
    assert entry["primaryKey"] == ["id"]
    assert entry["foreignKeys"] == foreign_keys
    assert entry["missingValues"] == ["", "NA"]
    by_name = {f["name"]: f for f in entry["fields"]}
    assert by_name["id"]["title"] == "Identifier"
    assert by_name["id"]["constraints"] == {"required": True, "unique": True}
    assert by_name["hp"]["title"] == "Horsepower (hp)"
    assert by_name["hp"]["constraints"] == {"minimum": 0, "maximum": 500}
    assert by_name["hp"]["missingValues"] == ["-99", "NA"]
    assert by_name["grade"]["categories"] == categories
    assert by_name["grade"]["categoriesOrdered"] is True
    assert by_name["when"]["format"] == "%Y/%m/%d %H:%M"
    assert "missingValues" not in by_name["parent"]
    # The field's own missingValues replace the schema's: -99 and NA are missing,
    # so the range is the one real value.
    assert by_name["hp"]["profile"]["missing"] == 2
    assert (by_name["hp"]["profile"]["min"], by_name["hp"]["profile"]["max"]) == (
        100.0,
        100.0,
    )
    # Every field keeps its order: name, type, description, the new keys, profile.
    assert list(by_name["hp"]) == [
        "name",
        "type",
        "description",
        "title",
        "constraints",
        "missingValues",
        "profile",
    ]


def test_schema_missing_values_apply_to_fields_without_their_own(
    tmp_path: Path,
) -> None:
    path = tmp_path / "codes.csv"
    path.write_text("code,n\nA,1\n-,2\nB,-\nA,3\n", "utf-8")
    entry = build_dataset(
        _resource(
            path,
            schema={
                "fields": [
                    {"name": "code", "type": "string"},
                    {"name": "n", "type": "integer"},
                ],
                "missingValues": [{"value": "-", "label": "Not recorded"}],
            },
        ),
        [],
        "https://example.invalid/codes.csv",
        tmp_path,
    )
    code, n = entry["fields"]
    assert (code["profile"]["missing"], code["profile"]["distinct"]) == (1, 2)
    assert n["profile"]["missing"] == 1


def test_missing_values_accepts_strings_and_labelled_values() -> None:
    assert missing_values(None) == []
    assert missing_values(["", "NA"]) == ["", "NA"]
    assert missing_values([{"value": "-99", "label": "Not asked"}, "x"]) == ["-99", "x"]


def test_profile_counts_documented_missing_values() -> None:
    s = pl.Series("x", ["1", "-999", "3", "", None])
    assert profile_field(s, "number")["missing"] == 2
    p = profile_field(s, "number", ["-999"])
    assert (p["missing"], p["min"]) == (3, 1.0)
    # Nominal fields: the documented value leaves the most common values too.
    s = pl.Series("c", ["a", "n/a", "n/a", "b"])
    p = profile_field(s, "string", ["n/a"])
    assert (p["missing"], p["distinct"]) == (2, 2)
    # Typed columns (Parquet, Arrow) keep their type.
    typed = pl.Series("t", [1, -1, 5], dtype=pl.Int64)
    assert profile_field(typed, "integer", ["-1"])["min"] == 1.0


def test_field_missing_values_replace_the_schema_list_not_extend_it(
    tmp_path: Path,
) -> None:
    # Replacing leaves "NA" a value of `code` (2 distinct, 1 missing); a union of the
    # field's and the schema's markers would count it missing too (1 distinct, 2 missing).
    path = tmp_path / "codes.csv"
    path.write_text("code\nA\n-\nNA\n", "utf-8")
    entry = build_dataset(
        _resource(
            path,
            schema={
                "fields": [{"name": "code", "type": "string", "missingValues": ["-"]}],
                "missingValues": ["NA"],
            },
        ),
        [],
        "https://example.invalid/codes.csv",
        tmp_path,
    )
    profile = entry["fields"][0]["profile"]
    assert (profile["missing"], profile["distinct"]) == (1, 2)
    assert profile["top"] == [["A", 1], ["NA", 1]]


def test_an_explicit_missing_values_list_replaces_the_empty_string_default(
    tmp_path: Path,
) -> None:
    # Table Schema: missingValues defaults to [""]; an explicit list replaces it, so
    # with [] an empty string is a value. Without a list, empty text stays missing.
    path = tmp_path / "rows.json"
    path.write_text(json.dumps([{"c": ""}, {"c": "A"}]), "utf-8")

    def profile(**field: object) -> dict[str, object]:
        entry = build_dataset(
            _resource(
                path,
                format=".json",
                schema={"fields": [{"name": "c", "type": "string", **field}]},
            ),
            [],
            "https://example.invalid/rows.json",
            tmp_path,
        )
        return entry["fields"][0]["profile"]

    assert (profile()["missing"], profile()["distinct"]) == (1, 1)
    explicit = profile(missingValues=[])
    assert (explicit["missing"], explicit["distinct"]) == (0, 2)
    assert profile(missingValues=["A"])["top"] == [["", 1]]
    both = profile(missingValues=["", "A"])
    assert (both["missing"], both["distinct"]) == (2, 0)


def test_an_explicit_empty_list_keeps_empty_csv_cells_as_values(tmp_path: Path) -> None:
    # CSV and TSV readers turn an empty cell into null unless told otherwise; with an
    # explicit list that lacks "", the cell is a value. Without a list, it stays missing.
    path = tmp_path / "rows.csv"
    path.write_text("c,n\n,1\nA,2\n", "utf-8")

    def profiles(**schema: object) -> list[dict[str, object]]:
        fields = [{"name": "c", "type": "string"}, {"name": "n", "type": "integer"}]
        entry = build_dataset(
            _resource(path, schema={"fields": fields, **schema}),
            [],
            "https://example.invalid/rows.csv",
            tmp_path,
        )
        return [f["profile"] for f in entry["fields"]]

    c, n = profiles()
    assert (c["missing"], c["distinct"], n["missing"]) == (1, 1, 0)
    c, n = profiles(missingValues=[])
    assert (c["missing"], c["distinct"], n["missing"]) == (0, 2, 0)
    c, _ = profiles(missingValues=["A"])
    assert (c["missing"], c["top"]) == (1, [["", 1]])


def test_build_dataset_marks_fields_read_from_the_data(tmp_path: Path) -> None:
    # A table without a schema: its fields come from the file's columns, not the
    # metadata, so the site doesn't count their missing descriptions as gaps.
    inferred = build_dataset(
        _resource(_fixture(tmp_path)), [], "https://example.invalid/f.csv", tmp_path
    )
    assert inferred["fieldsInferred"] is True
    assert [f["name"] for f in inferred["fields"]] == [
        "id",
        "parent",
        "hp",
        "grade",
        "when",
    ]
    # A declared schema adds no key (today's catalog stays as it was).
    declared = build_dataset(
        _resource(_fixture(tmp_path), schema={"fields": BARE_FIELDS}),
        [],
        "https://example.invalid/f.csv",
        tmp_path,
    )
    assert "fieldsInferred" not in declared
