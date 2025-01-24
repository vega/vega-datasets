from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

import niquests

# Repository structure
REPO_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = REPO_ROOT / "data"
OUTPUT_FILE = OUTPUT_DIR / "income.json"

# API Configuration
URL_BASE = "https://api.census.gov/data/2013/acs/acs3"
QUERY_FIELDS = "group(B19001)"
URL_QUERY = f"{URL_BASE}?get={QUERY_FIELDS}&for=state:*"


class CensusResponse(TypedDict):
    """Census API response after initial parsing."""

    header: list[str]
    data: list[list[str]]


class BaseIncomeGroup(TypedDict):
    """Base income group with required fields."""

    group: str


class AggregatedIncomeGroup(BaseIncomeGroup, total=False):
    """Income group that may include aggregation variables."""

    sum_vars: list[str]


class StateIncome(TypedDict):
    """Record for each state and income group combination."""

    name: str
    region: str
    id: int
    pct: float
    total: int
    group: str


# Income group order for sorting
INCOME_ORDER = [
    "<10000",
    "10000 to 14999",
    "15000 to 24999",
    "25000 to 34999",
    "35000 to 49999",
    "75000 to 99999",
    "50000 to 74999",
    "100000 to 149999",
    "150000 to 199999",
    "200000+",
]

# Income groupings and variable mappings
INCOME_MAPPING: dict[str, str | BaseIncomeGroup | AggregatedIncomeGroup] = {
    "B19001_001E": "total",
    "B19001_002E": {"group": "<10000"},
    "B19001_003E": {"group": "10000 to 14999"},
    "B19001_004E,B19001_005E": {
        "group": "15000 to 24999",
        "sum_vars": ["B19001_004E", "B19001_005E"],
    },
    "B19001_006E,B19001_007E": {
        "group": "25000 to 34999",
        "sum_vars": ["B19001_006E", "B19001_007E"],
    },
    "B19001_008E,B19001_009E,B19001_010E": {
        "group": "35000 to 49999",
        "sum_vars": ["B19001_008E", "B19001_009E", "B19001_010E"],
    },
    "B19001_011E,B19001_012E": {
        "group": "50000 to 74999",
        "sum_vars": ["B19001_011E", "B19001_012E"],
    },
    "B19001_013E": {"group": "75000 to 99999"},
    "B19001_014E,B19001_015E": {
        "group": "100000 to 149999",
        "sum_vars": ["B19001_014E", "B19001_015E"],
    },
    "B19001_016E": {"group": "150000 to 199999"},
    "B19001_017E": {"group": "200000+"},
}

# Region definitions
REGION_MAPPING: dict[str, str] = {
    "01": "south",
    "02": "west",
    "04": "west",
    "05": "south",
    "06": "west",
    "08": "west",
    "09": "northeast",
    "10": "south",
    "11": "south",
    "12": "south",
    "13": "south",
    "15": "west",
    "16": "west",
    "17": "midwest",
    "18": "midwest",
    "19": "midwest",
    "20": "midwest",
    "21": "south",
    "22": "south",
    "23": "northeast",
    "24": "south",
    "25": "northeast",
    "26": "midwest",
    "27": "midwest",
    "28": "south",
    "29": "midwest",
    "30": "west",
    "31": "midwest",
    "32": "west",
    "33": "northeast",
    "34": "northeast",
    "35": "west",
    "36": "northeast",
    "37": "south",
    "38": "midwest",
    "39": "midwest",
    "40": "south",
    "41": "west",
    "42": "northeast",
    "44": "northeast",
    "45": "south",
    "46": "midwest",
    "47": "south",
    "48": "south",
    "49": "west",
    "50": "northeast",
    "51": "south",
    "53": "west",
    "54": "south",
    "55": "midwest",
    "56": "west",
    "72": "other",
}


def get_census_data() -> CensusResponse:
    """Fetches household income data from Census API."""
    response = niquests.get(URL_QUERY)
    response.raise_for_status()
    data = response.json()

    if not data or len(data) < 2:
        msg = f"Invalid API response format: {data}"
        raise ValueError(msg)

    return CensusResponse(header=data[0], data=data[1:])


def get_state_income_sort_key(record: StateIncome) -> tuple[int, int]:
    """
    Create sort key for state income records.

    Returns tuple of (state_id, income_group_index) for consistent sorting
    by state and then by income group order.
    """
    return (record["id"], INCOME_ORDER.index(record["group"]))


def process_state_records(census_data: CensusResponse) -> list[StateIncome]:
    """Processes census data into state income records."""
    header = census_data["header"]
    records = []

    for row in census_data["data"]:
        state_data = dict(zip(header, row, strict=True))
        state_fips = state_data["state"]

        # Skip if not in region mapping
        if state_fips not in REGION_MAPPING:
            continue

        total = int(state_data["B19001_001E"])

        for code_str, mapping in INCOME_MAPPING.items():
            if isinstance(mapping, dict):
                group = mapping["group"]
                if "sum_vars" in mapping:
                    count = sum(int(state_data[var]) for var in mapping["sum_vars"])
                else:
                    count = int(state_data[code_str])

                pct = round(count / total, 3)

                record = StateIncome(
                    name=state_data["NAME"],
                    region=REGION_MAPPING[state_fips],
                    id=int(state_fips),
                    pct=pct,
                    total=total,
                    group=group,
                )
                records.append(record)

    return sorted(records, key=get_state_income_sort_key)


def write_json(data: list[StateIncome], output: Path) -> None:
    """Writes data to JSON file."""
    output.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    """Generate household income by state dataset."""
    census_data = get_census_data()
    records = process_state_records(census_data)
    print(f"Found {len(records)} state-income group combinations")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    write_json(records, OUTPUT_FILE)
    print(f"Data written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
