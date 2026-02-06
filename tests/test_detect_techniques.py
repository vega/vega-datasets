"""Tests for detect_techniques function in generate_gallery_examples.py."""

import sys
from pathlib import Path

# Add scripts directory to path for import
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_gallery_examples import detect_techniques


class TestVegaTransforms:
    """Test Vega-specific transform detection."""

    def test_detects_vega_bin_transform(self):
        """Vega uses {"type": "bin"} for binning transforms."""
        spec = {
            "data": [
                {
                    "name": "binned",
                    "source": "source",
                    "transform": [{"type": "bin", "field": "IMDB_Rating"}],
                }
            ]
        }
        techniques = detect_techniques(spec, "vega")
        assert "transform:bin" in techniques

    def test_detects_vega_extent_transform(self):
        """Vega uses {"type": "extent"} to compute data extent."""
        spec = {
            "data": [
                {
                    "name": "source",
                    "transform": [
                        {"type": "extent", "field": "Horsepower", "signal": "hp_extent"}
                    ],
                }
            ]
        }
        techniques = detect_techniques(spec, "vega")
        assert "transform:extent" in techniques

    def test_detects_vega_crossfilter_transform(self):
        """Vega uses {"type": "crossfilter"} for multi-dimensional filtering."""
        spec = {
            "data": [
                {
                    "name": "flights",
                    "transform": [
                        {
                            "type": "crossfilter",
                            "signal": "vgx_xfilter",
                            "fields": ["delay", "time", "distance"],
                        }
                    ],
                }
            ]
        }
        techniques = detect_techniques(spec, "vega")
        assert "transform:crossfilter" in techniques

    def test_detects_vega_resolvefilter_transform(self):
        """Vega uses {"type": "resolvefilter"} to resolve crossfilter."""
        spec = {
            "data": [
                {
                    "name": "filtered",
                    "source": "flights",
                    "transform": [{"type": "resolvefilter", "filter": {"signal": "..."}}],
                }
            ]
        }
        techniques = detect_techniques(spec, "vega")
        assert "transform:crossfilter" in techniques  # resolvefilter implies crossfilter


class TestVegaLiteTransforms:
    """Test Vega-Lite transform detection."""

    def test_detects_vegalite_bin_in_transform(self):
        """Vega-Lite uses {"bin": true} or {"bin": {...}} in transforms."""
        spec = {"transform": [{"bin": True, "field": "IMDB_Rating", "as": "binned"}]}
        techniques = detect_techniques(spec, "vega-lite")
        assert "transform:bin" in techniques

    def test_detects_vegalite_bin_object(self):
        """Vega-Lite uses {"bin": {maxbins: 10}} for detailed bin config."""
        spec = {
            "transform": [{"bin": {"maxbins": 10}, "field": "IMDB_Rating", "as": "binned"}]
        }
        techniques = detect_techniques(spec, "vega-lite")
        assert "transform:bin" in techniques


class TestAltairTransforms:
    """Test Altair code detection."""

    def test_detects_altair_transform_bin(self):
        """Altair uses transform_bin() method."""
        code = """
import altair as alt
chart = alt.Chart(data).transform_bin(
    'binned_field', 'field', bin=alt.Bin(maxbins=20)
).mark_bar()
"""
        techniques = detect_techniques(code, "altair")
        assert "transform:bin" in techniques


class TestExistingPatterns:
    """Verify existing patterns still work after changes."""

    def test_detects_window_transform_vegalite(self):
        """Window transforms should still be detected."""
        spec = {
            "transform": [
                {"window": [{"op": "rank", "as": "rank"}], "sort": [{"field": "x"}]}
            ]
        }
        techniques = detect_techniques(spec, "vega-lite")
        assert "transform:window" in techniques

    def test_detects_selection_altair(self):
        """Altair selections should still be detected."""
        code = "brush = alt.selection_interval()"
        techniques = detect_techniques(code, "altair")
        assert "interaction:selection" in techniques

    def test_detects_geoshape(self):
        """Geoshape marks should still be detected."""
        spec = {"mark": "geoshape", "projection": {"type": "albersUsa"}}
        techniques = detect_techniques(spec, "vega-lite")
        assert "geo:shape" in techniques
        assert "geo:projection" in techniques


class TestMissingVLTransforms:
    """Test Vega-Lite transforms that were previously undetected."""

    # NOTE on stack detection limitations:
    # In Vega-Lite, stacking is IMPLICIT by default for bar/area marks with
    # color encoding — no "stack" key appears in the spec at all. We can only
    # detect EXPLICIT stacking configurations (stack:"zero", stack:"normalize",
    # or the transform array form). This means most simple stacked charts in
    # VL won't be tagged. We accept this tradeoff — explicit stack usage IS
    # a notable technique worth tagging, and Vega specs always use explicit
    # {"type":"stack"} which we catch reliably.
    #
    # Known edge case: "stack":null (disabling stacking) will false-positive.
    # This is rare in gallery examples and acceptable.

    def test_detects_vegalite_stack_explicit(self):
        """VL explicit stack config: {"stack":"zero"} or {"stack":"normalize"}."""
        spec = {
            "mark": "area",
            "encoding": {
                "x": {"field": "date", "type": "temporal"},
                "y": {"field": "count", "type": "quantitative", "stack": "zero"},
                "color": {"field": "category"},
            },
        }
        techniques = detect_techniques(spec, "vega-lite")
        assert "transform:stack" in techniques

    def test_detects_vegalite_stack_transform_array(self):
        """Vega-Lite transform array form: {"stack":"field", ...}."""
        spec = {
            "transform": [
                {"stack": "count", "groupby": ["date"], "as": ["y0", "y1"]}
            ]
        }
        techniques = detect_techniques(spec, "vega-lite")
        assert "transform:stack" in techniques

    def test_vegalite_implicit_stack_not_detected(self):
        """VL implicit stacking (no "stack" key) is NOT detected — known limitation."""
        spec = {
            "mark": "bar",
            "encoding": {
                "x": {"field": "date", "type": "ordinal"},
                "y": {"field": "count", "type": "quantitative"},
                "color": {"field": "category", "type": "nominal"},
            },
        }
        techniques = detect_techniques(spec, "vega-lite")
        # Implicit stacking is invisible in the spec — we accept this gap
        assert "transform:stack" not in techniques

    def test_detects_vega_stack_transform(self):
        """Vega uses {"type":"stack"} in data transforms — always explicit."""
        spec = {
            "data": [
                {
                    "name": "table",
                    "transform": [
                        {"type": "stack", "groupby": ["x"], "field": "y"}
                    ],
                }
            ]
        }
        techniques = detect_techniques(spec, "vega")
        assert "transform:stack" in techniques

    def test_detects_vegalite_timeunit_encoding(self):
        """Vega-Lite uses {"timeUnit":"yearmonth"} in encoding."""
        spec = {
            "mark": "line",
            "encoding": {
                "x": {"timeUnit": "yearmonth", "field": "date", "type": "temporal"},
                "y": {"field": "count", "type": "quantitative"},
            },
        }
        techniques = detect_techniques(spec, "vega-lite")
        assert "transform:timeunit" in techniques

    def test_detects_vegalite_timeunit_transform(self):
        """Vega-Lite uses {"timeUnit":"month", "field":"date", "as":"month"}."""
        spec = {
            "transform": [
                {"timeUnit": "month", "field": "date", "as": "month_date"}
            ]
        }
        techniques = detect_techniques(spec, "vega-lite")
        assert "transform:timeunit" in techniques

    def test_detects_altair_timeunit(self):
        """Altair uses transform_timeunit() method."""
        code = """
import altair as alt
chart = alt.Chart(data).transform_timeunit(
    month='month(date)'
).mark_bar()
"""
        techniques = detect_techniques(code, "altair")
        assert "transform:timeunit" in techniques

    def test_detects_vega_timeunit(self):
        """Vega uses {"type":"timeunit"} transform."""
        spec = {
            "data": [
                {
                    "name": "table",
                    "transform": [
                        {"type": "timeunit", "field": "date", "units": ["year", "month"]}
                    ],
                }
            ]
        }
        techniques = detect_techniques(spec, "vega")
        assert "transform:timeunit" in techniques


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
