# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "geopandas",
#     "pandas",
#     "numpy",
#     "exactextract",
#     "rasterio",
#     "niquests",  # drop-in replacement for requests with better performance
#     "tqdm",
# ]
# ///

"""
Retrieve, extract, transform, and export species habitat data for US counties.

Uses temporary storage for intermediate files and cleans up after processing.

Output:
-------
- species.csv: CSV file with species habitat percentages per county.
"""

from __future__ import annotations

import io
import logging
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
import niquests
import numpy as np
import pandas as pd
from exactextract import exact_extract
from tqdm import tqdm

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)
FILE_DIR = Path(__file__).parent
DATA_DIR = FILE_DIR.parent / "data"
VECTOR_FP = DATA_DIR / "us-10m.json"
OUTPUT_CSV_NAME = "species.csv"

HABITAT_URLS: Sequence[str] = [
    "https://www.sciencebase.gov/catalog/file/get/58fa64ece4b0b7ea545257e3?f=__disk__f3%2F9a%2F10%2Ff39a100ea8eb5293e0ea771795e15792bf24ed00",  # Coyote
    "https://www.sciencebase.gov/catalog/file/get/58fa513ce4b0b7ea5452521a?f=__disk__95%2F9a%2F85%2F959a85f2cc7f9d4c47d07a4edbf3318e89ba1e24",  # cardinal
    "https://www.sciencebase.gov/catalog/file/get/58fe0a6be4b007492829456e?f=__disk__92%2F99%2F2d%2F92992d211f3fc43f68f2d645624295c23eec31ba",  # alligator
    "https://www.sciencebase.gov/catalog/file/get/58fa3f0be4b0b7ea54524859?f=__disk__81%2F26%2F6f%2F81266f6d642fe5a03255f19055afd9d4d169a06d",  # American bullfrog
]


def download_and_extract_tifs(urls: Sequence[str], temp_dir: Path) -> list[Path]:
    """Downloads and extracts TIF files to a temporary directory using niquests."""
    downloaded_files = []

    # Use multiplexed session for better performance
    with niquests.Session(multiplexed=True) as session:
        for url in tqdm(urls, desc="Downloading and extracting TIF files"):
            try:
                # Stream download to handle large files efficiently
                response = session.get(url, stream=True)
                response.raise_for_status()

                # Get content length for progress bar if available
                total_size = int(response.headers.get("content-length", 0))

                # Download with progress bar
                zip_data = io.BytesIO()
                with tqdm(
                    total=total_size, unit="iB", unit_scale=True, desc="Downloading"
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=8192 * 4):
                        size = zip_data.write(chunk)
                        pbar.update(size)

                # Extract TIF files from the zip
                zip_data.seek(0)
                with zipfile.ZipFile(zip_data) as zf:
                    tif_files = [f for f in zf.namelist() if f.lower().endswith(".tif")]
                    for tif_file in tif_files:
                        tif_path = temp_dir / Path(tif_file).name
                        tif_path.write_bytes(zf.read(tif_file))
                        downloaded_files.append(tif_path)

                # Log connection info for debugging/optimization
                logger.debug(
                    "Connection info for %(url)s: Established in %(latency)s, Headers: %(headers)s",
                    {
                        "url": url,
                        "latency": response.conn_info.established_latency,
                        "headers": response.headers,
                    },
                )

            except niquests.RequestException as e:
                logger.error(
                    "Error downloading from %(url)s: %(error)s",
                    {"url": url, "error": str(e)},
                )
                continue
            except zipfile.BadZipFile as e:
                logger.error(
                    "Error extracting zip from %(url)s: %(error)s",
                    {"url": url, "error": str(e)},
                )
                continue

    return sorted(downloaded_files)


def process_habitat_data(
    vector_filepath: Path, raster_filepaths: Sequence[Path]
) -> pd.DataFrame:
    """Processes habitat raster data for US counties."""
    gdf = gpd.read_file(vector_filepath, layer="counties")
    gdf = gdf.set_crs(epsg=4326).to_crs(epsg=5070)
    gdf = gdf[~gdf.is_empty].copy()
    gdf.columns = ["county_id", "geometry"]

    df = exact_extract(
        rast=raster_filepaths,
        vec=gdf,
        ops=["unique(default_value=255)", "frac(default_value=255)"],
        include_cols="county_id",
        output="pandas",
        progress=True,
    )

    all_data = []
    for raster in raster_filepaths:
        stem = Path(raster).name.split(".")[0]
        species = stem.split("_")[0]

        unique_col = f"{stem}_unique"
        frac_col = f"{stem}_frac"

        unique_values = np.array(df[unique_col].to_list(), dtype=object)
        frac_values = np.array(df[frac_col].to_list(), dtype=object)

        county_ids = np.repeat(
            df["county_id"].values, [len(arr) for arr in unique_values]
        )
        unique_flat = np.concatenate(unique_values)
        frac_flat = np.concatenate(frac_values)

        mask = unique_flat == 3
        temp_df = pd.DataFrame({
            "county_id": county_ids[mask],
            "species": species,
            "pct": frac_flat[mask],
        })
        all_data.append(temp_df)

    return pd.concat(all_data, ignore_index=True)


def main() -> None:
    """Main function with cleanup handling."""
    logging.basicConfig(level=logging.INFO)

    if not VECTOR_FP.exists():
        logger.error("Vector file not found at %(path)s", {"path": VECTOR_FP})
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Create temporary directory for intermediate files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        try:
            # Download and process files
            tif_files = download_and_extract_tifs(HABITAT_URLS, temp_path)
            if not tif_files:
                logger.error("No TIF files downloaded and extracted")
                return

            output_df = process_habitat_data(VECTOR_FP, tif_files)
            output_df.to_csv(DATA_DIR / OUTPUT_CSV_NAME, index=False)

            logger.info("Data successfully exported to %s", OUTPUT_CSV_NAME)

        except Exception as e:
            logger.error("Error during processing: %s", str(e))
            raise


if __name__ == "__main__":
    main()
