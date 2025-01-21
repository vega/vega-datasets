# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
# ]
# ///
"""Lookup and output US state capitals with longitude and latitude."""

import json
from pathlib import Path
from time import sleep

import requests


def get_state_capitals() -> list[dict]:
    """
    List of dictionaries representing US state capitals.

    Each dictionary contains 'state' and 'city' keys.
    """
    return [
        {"state": "Alabama", "city": "Montgomery"},
        {"state": "Alaska", "city": "Juneau"},
        {"state": "Arizona", "city": "Phoenix"},
        {"state": "Arkansas", "city": "Little Rock"},
        {"state": "California", "city": "Sacramento"},
        {"state": "Colorado", "city": "Denver"},
        {"state": "Connecticut", "city": "Hartford"},
        {"state": "Delaware", "city": "Dover"},
        {"state": "Florida", "city": "Tallahassee"},
        {"state": "Georgia", "city": "Atlanta"},
        {"state": "Hawaii", "city": "Honolulu"},
        {"state": "Idaho", "city": "Boise"},
        {"state": "Illinois", "city": "Springfield"},
        {"state": "Indiana", "city": "Indianapolis"},
        {"state": "Iowa", "city": "Des Moines"},
        {"state": "Kansas", "city": "Topeka"},
        {"state": "Kentucky", "city": "Frankfort"},
        {"state": "Louisiana", "city": "Baton Rouge"},
        {"state": "Maine", "city": "Augusta"},
        {"state": "Maryland", "city": "Annapolis"},
        {"state": "Massachusetts", "city": "Boston"},
        {"state": "Michigan", "city": "Lansing"},
        {"state": "Minnesota", "city": "Saint Paul"},
        {"state": "Mississippi", "city": "Jackson"},
        {"state": "Missouri", "city": "Jefferson City"},
        {"state": "Montana", "city": "Helena"},
        {"state": "Nebraska", "city": "Lincoln"},
        {"state": "Nevada", "city": "Carson City"},
        {"state": "New Hampshire", "city": "Concord"},
        {"state": "New Jersey", "city": "Trenton"},
        {"state": "New Mexico", "city": "Santa Fe"},
        {"state": "New York", "city": "Albany"},
        {"state": "North Carolina", "city": "Raleigh"},
        {"state": "North Dakota", "city": "Bismarck"},
        {"state": "Ohio", "city": "Columbus"},
        {"state": "Oklahoma", "city": "Oklahoma City"},
        {"state": "Oregon", "city": "Salem"},
        {"state": "Pennsylvania", "city": "Harrisburg"},
        {"state": "Rhode Island", "city": "Providence"},
        {"state": "South Carolina", "city": "Columbia"},
        {"state": "South Dakota", "city": "Pierre"},
        {"state": "Tennessee", "city": "Nashville"},
        {"state": "Texas", "city": "Austin"},
        {"state": "Utah", "city": "Salt Lake City"},
        {"state": "Vermont", "city": "Montpelier"},
        {"state": "Virginia", "city": "Richmond"},
        {"state": "Washington", "city": "Olympia"},
        {"state": "West Virginia", "city": "Charleston"},
        {"state": "Wisconsin", "city": "Madison"},
        {"state": "Wyoming", "city": "Cheyenne"},
    ]


def lookup_coordinates(capitals: list[dict]) -> list[dict]:
    """
    Lookup coordinates for a list of state capitals.

    Parameters
    ----------
    capitals
      List of dictionaries with 'state' and 'city' keys.

    Returns
    -------
    List of dictionaries with added 'lon' and 'lat' keys.
    """
    updated_capitals = []

    for capital in capitals:
        url = (
            f"https://nominatim.openstreetmap.org/search?city={capital['city']}"
            f"&state={capital['state']}&country=USA&format=json"
        )
        headers = {"User-Agent": "state-capitals-lookup"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(
                f"Request failed for {capital['city']}, {capital['state']} "
                f"with status code {response.status_code}"
            )
            continue

        try:
            data = response.json()
            if data:
                loc = data[0]
                capital_data = {
                    "lon": float(loc["lon"]),
                    "lat": float(loc["lat"]),
                    "state": capital["state"],
                    "city": capital["city"],
                }
                updated_capitals.append(capital_data)
            else:
                print(
                    f"Could not find coordinates for {capital['city']}, {capital['state']}"
                )
        except json.JSONDecodeError:
            print(
                f"Failed to decode JSON response for {capital['city']}, {capital['state']}"
            )
            continue

        sleep(0.25)  # Respect Nominatim's usage policy

    return updated_capitals


def save_json_output(data: list[dict], output_path: Path) -> None:
    """
    Save the capitals data as a JSON file with custom formatting.

    - no spaces after colons
    - spaces after commas
    - fields ordered as lon, lat, state, city.

    Parameters
    ----------
    data
        List of dictionaries containing capital data
    output_path
        Path to the output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as f:
        f.write("[\n")
        for i, capital_data in enumerate(data):
            # Create ordered dictionary with desired field order
            ordered_data = {
                "lon": capital_data["lon"],
                "lat": capital_data["lat"],
                "state": capital_data["state"],
                "city": capital_data["city"],
            }
            # Convert to JSON with custom separators
            json_str = json.dumps(ordered_data, separators=(", ", ":"))

            f.write("  " + json_str + ("," if i < len(data) - 1 else "") + "\n")
        f.write("]\n")


def main() -> None:
    """Main function to lookup and output state capitals with coordinates."""
    # Get the script's directory
    script_dir = Path(__file__).parent
    # Construct path to data directory (one level up + data)
    data_dir = script_dir.parent / "data"
    output_path = data_dir / "us-state-capitals.json"

    capitals = get_state_capitals()
    updated_capitals = lookup_coordinates(capitals)
    save_json_output(updated_capitals, output_path)
    print(f"Saved state capitals data to {output_path}")


if __name__ == "__main__":
    main()
