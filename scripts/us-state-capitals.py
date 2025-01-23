"""
Retrieves and saves U.S. state capital locations with their coordinates from the National Map API.

This script fetches data from the USGS National Map Structures Database API to generate a JSON file
containing the latitude, longitude, state, and city of U.S. state capitals. State capitol building
locations are used as a practical representation of state capital city points.

It relies on a local JSON file `_data/us-state-codes.json` for mapping state abbreviations to full names.
"""

from __future__ import annotations

import json
import typing
import warnings
from functools import partial
from operator import itemgetter
from pathlib import Path
from typing import TYPE_CHECKING, Literal, TypedDict

import niquests

if TYPE_CHECKING:
    import sys
    from collections.abc import Iterator, Mapping, Sequence
    from typing import Any, LiteralString

    if sys.version_info >= (3, 13):
        from typing import TypeIs
    else:
        from typing_extensions import TypeIs

type Features = Sequence[Feature[Any, Any, Any]]
"""Represents the ``features`` property of capitol building data, before validation."""

type FieldName = Literal["NAME", "STATE", "CITY"]

REPO_ROOT: Path = Path(__file__).parent.parent
INPUT_DIR: Path = REPO_ROOT / "_data"
OUTPUT_DIR: Path = REPO_ROOT / "data"

INPUT_FILE: Path = INPUT_DIR / "us-state-codes.json"
"""
State abbreviation to full name mappings (from JSON "states").

Used for name lookup and territory filtering.

Example:

    {"states": {"AL": "Alabama", "WY": "Wyoming"}, "territories": {}}
"""

OUTPUT_FILE: Path = OUTPUT_DIR / "us-state-capitals.json"
URL_ARCGIS = "https://carto.nationalmap.gov/arcgis/rest"
URL_MAP_SERVER = f"{URL_ARCGIS}services/structures/MapServer/"
URL_STATE_CAPITOLS = f"{URL_MAP_SERVER}6/query"
FEATURE_STATE_CAPITOLS = "FCODE = 83006"
TERRITORIES = "STATE IN ('AS', 'GU', 'MP', 'PR', 'VI')"
WHERE_CLAUSE = f"{FEATURE_STATE_CAPITOLS} AND NOT ({TERRITORIES})"
WKID_WGS84: Literal[4326] = 4326
"""
`Well-known ID`_ for `WGS 84`_, used as a `spatial reference`_.

.. _Well-known ID: https://support.esri.com/en-us/gis-dictionary/wkid
.. _WGS 84: https://en.wikipedia.org/wiki/World_Geodetic_System#WGS_84
.. _spatial reference: https://carto.nationalmap.gov/arcgis/help/en/rest/services-reference/enterprise/geometry-objects/#spatial-reference
"""


class MapServiceLayerResponse(TypedDict, total=False):
    """
    Response from `National Map Structures Database`_.

    .. _National Map Structures Database: https://carto.nationalmap.gov/arcgis/help/en/rest/services-reference/enterprise/query-map-service-layer/
    """

    features: Features


class Point(TypedDict):
    x: float
    y: float


class Feature[A_KT: LiteralString, A_VT: str | float | bool, G: Mapping[str, Any]](
    TypedDict
):
    """
    A generic `GeoJSON feature object`_.

    .. _GeoJSON feature object: https://carto.nationalmap.gov/arcgis/help/en/rest/services-reference/enterprise/feature-object/
    """

    attributes: Mapping[A_KT, A_VT]
    geometry: G


class CapitolFeature(Feature[FieldName, str, Point]):
    """Validated state capitol feature, **prior** to any processing."""


class StateCapitol(TypedDict):
    """State capitol feature, **after** processing."""

    lon: float
    lat: float
    state: str
    city: str


def read_json(source: str | Path, /) -> Any:
    return json.loads(Path(source).read_text("utf-8"))


def get_state_capitols() -> Features:
    """Fetches state capitol building coordinates from the National Map Structures Database."""
    params = {
        "f": "json",
        "where": WHERE_CLAUSE,
        "outFields": ",".join((*_get_args(FieldName), "SHAPE")),
        "geometryPrecision": 7,
        "outSR": WKID_WGS84,
        "returnGeometry": True,
    }
    response = niquests.get(URL_STATE_CAPITOLS, params=params)
    response.raise_for_status()
    content: MapServiceLayerResponse = response.json()
    if features := content.get("features"):
        return features
    msg = f"Expected a features mapping but got:\n\n{content!r}"
    raise TypeError(msg)


def is_capitol_feature(feat: Feature, states: dict[str, str]) -> TypeIs[CapitolFeature]:
    """Ensure feature describes only capitols of states and not territories."""
    return bool(
        (attrs := feat.get("attributes"))
        and attrs.get("STATE") in states
        and "CITY" in attrs
        and (geom := feat.get("geometry"))
        and geom.keys() == {"x", "y"}
    )


def into_state_capitol(feat: CapitolFeature, states: dict[str, str]) -> StateCapitol:
    """Convert feature response into a clean format with full state names."""
    geom, attrs = feat["geometry"], feat["attributes"]
    return StateCapitol(
        lon=geom["x"], lat=geom["y"], state=states[attrs["STATE"]], city=attrs["CITY"]
    )


def iter_state_capitols(
    features: Features, states: dict[str, str]
) -> Iterator[StateCapitol]:
    for feat in features:
        if is_capitol_feature(feat, states):
            yield into_state_capitol(feat, states)
        else:
            msg = f"Unexpected territory:\n{feat!r}"
            warnings.warn(msg, stacklevel=2)


def write_json(data: Sequence[StateCapitol], output: Path) -> None:
    """Saves ``data`` to ``output`` with consistent formatting."""
    INDENT, OB, CB, NL = "  ", "[", "]", "\n"
    to_str = partial(json.dumps, separators=(", ", ":"))
    with output.open("w", encoding="utf-8") as f:
        f.write(f"{OB}{NL}")
        for record in data[:-1]:
            f.write(f"{INDENT}{to_str(record)},{NL}")
        f.write(f"{INDENT}{to_str(data[-1])}{NL}{CB}{NL}")


def _get_args(tp: Any, /) -> tuple[Any, ...]:
    return typing.get_args(getattr(tp, "__value__", tp))


def main() -> None:
    it = iter_state_capitols(get_state_capitols(), read_json(INPUT_FILE)["states"])
    by_state = sorted(it, key=itemgetter("state"))
    print(f"Found {len(by_state)} state capitals")
    OUTPUT_FILE.touch()
    write_json(by_state, OUTPUT_FILE)
    print(f"Data written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
