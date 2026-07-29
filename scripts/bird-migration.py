"""
Build `data/bird-migration.csv` from the La Sorte & Fink daily centroid deposit.

The source file `centroids.txt` accompanies La Sorte & Fink (2017), "Projected changes
in prevailing winds for transatlantic migratory birds under global warming", Journal of
Animal Ecology, and is archived on Dryad at https://doi.org/10.5061/dryad.5h9c4 under
CC0-1.0. It holds, for each of ten Nearctic-breeding migratory bird species, the daily
geographic center of the species' population, estimated from eBird occurrence records
collected between 1950 and 2015.

Dryad requires an interactive download, so this script takes the already-downloaded
`centroids.txt` as an argument rather than fetching it.

Three things about the source need repair before the data is usable:

1. The source has no day column. Each species occupies exactly 365 consecutive rows in
   chronological order starting at January 1, so this script derives the day from row
   position within each species block. Four checks confirm the ordering: consecutive
   rows sit a median 0.09-0.89 degrees apart against 30.9 degrees for two random rows;
   the distance from row 365 back to row 1 is under half a degree for nine of the ten
   species, closing the annual cycle; latitude peaks between days 155 and 215, the
   boreal breeding season; and day 1 places American Golden-Plover on the Argentine
   pampas and White-rumped Sandpiper in Patagonia, both correct austral-summer ranges.

2. 421 of the 3650 rows (11.5%) carry `NA` coordinates on days when the model produced
   no estimate, concentrated in the non-breeding season when eBird coverage of South
   America and the Caribbean was sparse. This script drops those rows, so a species'
   day values are not contiguous. Connecticut Warbler loses 172 days, Bicknell's Thrush
   104, Bobolink 73, and Buff-breasted Sandpiper 66; the three Calidris sandpipers and
   Solitary Sandpiper lose none.

3. Coordinates carry fifteen significant figures, far past what a population centroid
   estimate supports. This script rounds to four decimal places, roughly 11 m.

The `date` column follows the convention `data/seattle-weather-hourly-normals.csv` uses
for climate normals: because the values average many years, no calendar year applies, so
the dates take a nominal non-leap year. `day` is kept alongside it because day-of-year
arithmetic is far more legible than the millisecond arithmetic a date column would force
on anything comparing offsets between days.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from collections import Counter
from pathlib import Path

DAYS_IN_YEAR = 365
NOMINAL_YEAR = 2015  # last year of the 1950-2015 source window; not a leap year
COORD_PRECISION = 4


def convert(source: Path, dest: Path) -> None:
    with source.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    counts = Counter(row["species"] for row in rows)
    if bad := {s: n for s, n in counts.items() if n != DAYS_IN_YEAR}:
        sys.exit(f"expected {DAYS_IN_YEAR} rows per species, got {bad}")

    blocks = [row["species"] for row in rows]
    if _block_count(blocks) != len(counts):
        sys.exit("each species must occupy one contiguous block of rows")

    jan_1 = dt.date(NOMINAL_YEAR, 1, 1)
    day = 0
    seen = None
    out = []
    for row in rows:
        if row["species"] != seen:
            seen, day = row["species"], 0
        day += 1
        if row["lon"] == "NA" or row["lat"] == "NA":
            continue
        out.append({
            "species": _species_name(row["species"]),
            "day": day,
            "date": (jan_1 + dt.timedelta(days=day - 1)).isoformat(),
            "lon": round(float(row["lon"]), COORD_PRECISION),
            "lat": round(float(row["lat"]), COORD_PRECISION),
        })

    with dest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["species", "day", "date", "lon", "lat"], lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(out)

    dropped = len(rows) - len(out)
    print(
        f"wrote {len(out)} rows to {dest} ({dropped} dropped for missing coordinates)"
    )


def _species_name(raw: str) -> str:
    """Undo the source's filename-safe encoding: `Bicknell_s_Thrush` is possessive."""
    return raw.replace("_s_", "'s ").replace("_", " ")


def _block_count(values: list[str]) -> int:
    return sum(1 for i, v in enumerate(values) if i == 0 or values[i - 1] != v)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="centroids.txt downloaded from Dryad")
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "bird-migration.csv",
    )
    args = parser.parse_args()
    convert(args.source, args.dest)
