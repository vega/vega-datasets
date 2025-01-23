"""
Retrieves and saves U.S. state capital locations with their coordinates from the National Map API.

This script fetches data from the USGS National Map Structures Database API to generate a JSON file
containing the latitude, longitude, state, and city of U.S. state capitals. State capitol building
locations are used as a practical representation of state capital city points.

It relies on a local JSON file `_data/us-state-codes.json` for mapping state abbreviations to full names.
"""

import json
from operator import itemgetter
from pathlib import Path
from typing import Any

import niquests


def load_state_codes(script_dir: Path) -> dict:
    """
    Loads state/territory code mappings from `_data/us-state-codes.json`.

    Required to:
    1. convert API state abbreviations to full names (e.g., 'CA' to 'California').
    2. filter out U.S. territory locations from the API data. (Current script scope: U.S. states).

    Example `us-state-codes.json`:
    ```json
    {
        "states": {
            "AL": "Alabama",
            "WY": "Wyoming"
        },
        "territories": {}
    }
    ```

    Args:
        script_dir: Script directory (for locating `_data/us-state-codes.json`).

    Returns
    -------
        Dictionary: State abbreviation to full name mappings (from JSON "states"),
                    used for name lookup and territory filtering.
    """
    data_dir = script_dir.parent / "_data"
    state_codes_path = data_dir / "us-state-codes.json"

    with state_codes_path.open() as f:
        return json.load(f)


def get_state_capitols() -> dict | None:
    """
    Fetches state capitol building coordinates from the National Map Structures Database.

    Returns
    -------
        JSON response containing capitol building data, or None if request fails
    """
    url = "https://carto.nationalmap.gov/arcgis/rest/services/structures/MapServer/6/query"
    params = {
        "f": "json",
        "where": "FCODE=83006",  # Feature code for state capitol buildings
        "outFields": "NAME,STATE,CITY,SHAPE",
        "geometryPrecision": 7,
        "outSR": 4326,  # WGS84 coordinate system
        "returnGeometry": True,
    }

    try:
        response = niquests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except niquests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None


def format_capitols_data(
    capitols_data: dict[str, Any] | None, state_data: dict
) -> list:
    """
    Processes raw capitol data into a clean format with full state names.

    Args:
        capitols_data: Raw JSON response from the WMS query
        state_data: Dictionary with 'states' and 'territories' mappings

    Returns
    -------
        List of dictionaries containing formatted capitol data
    """
    formatted_data = []
    if capitols_data and "features" in capitols_data:
        for feature in capitols_data["features"]:
            attributes = feature.get("attributes", {})
            geometry = feature.get("geometry", {})

            state_code = attributes.get("STATE")
            city_name = attributes.get("CITY")
            lon = geometry.get("x")
            lat = geometry.get("y")

            # Check if it's a state and we have all required data
            if (
                state_code
                and state_code in state_data["states"]  # Check in states dictionary
                and city_name
                and lon is not None
                and lat is not None
            ):
                formatted_data.append(
                    {
                        "lon": lon,
                        "lat": lat,
                        "state": state_data["states"][
                            state_code
                        ],  # Get name from states dictionary
                        "city": city_name,
                    }
                )
    return formatted_data


def save_json_output(data: list[dict], output_path: Path) -> None:
    """
    Saves formatted capitol data to a JSON file with consistent formatting.

    Args:
        data: List of formatted capitol dictionaries
        output_path: Path where JSON file should be saved
    """
    sorted_data = sorted(data, key=itemgetter("state"))

    with output_path.open("w") as f:
        f.write("[\n")
        for i, capital_data in enumerate(sorted_data):
            ordered_data = {
                "lon": capital_data["lon"],
                "lat": capital_data["lat"],
                "state": capital_data["state"],
                "city": capital_data["city"],
            }
            json_str = json.dumps(ordered_data, separators=(", ", ":"))

            f.write("  " + json_str + ("," if i < len(sorted_data) - 1 else "") + "\n")
        f.write("]\n")


def main() -> None:
    script_dir = Path(__file__).parent
    state_codes = load_state_codes(script_dir)

    capitols_response = get_state_capitols()
    if not capitols_response:
        print("Error: Failed to retrieve state capitals data")
        return

    formatted_data = format_capitols_data(capitols_response, state_codes)
    print(f"Found {len(formatted_data)} state capitals")

    data_dir = script_dir.parent / "data"
    output_path = data_dir / "us-state-capitals.json"
    output_path.touch()
    save_json_output(formatted_data, output_path)
    print(f"Data written to {output_path}")


if __name__ == "__main__":
    main()
