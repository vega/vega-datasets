# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "geopandas",
#     "pandas",
#     "numpy",
#     "exactextract",
#     "rasterio",
#     "setuptools",
#     "sciencebasepy", # provides functionality for interacting with the USGS ScienceBase platform
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

import logging
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
import numpy as np
import pandas as pd
from exactextract import exact_extract
from sciencebasepy import SbSession
from tqdm import tqdm

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)
FILE_DIR = Path(__file__).parent
DATA_DIR = FILE_DIR.parent / "data"
VECTOR_FP = DATA_DIR / "us-10m.json"
OUTPUT_CSV_NAME = "species.csv"

HABITAT_ITEM_IDS: Sequence[str] = [
    "58fa64ece4b0b7ea545257e3",  # Coyote
    "58fa513ce4b0b7ea5452521a",  # Cardinal
    "58fe0a6be4b007492829456e",  # Alligator
    "58fa3f0be4b0b7ea54524859",  # American bullfrog
]


# def download_and_extract_tifs(item_ids: Sequence[str], temp_dir: Path) -> list[Path]:
#     """Downloads and extracts TIF files to a temporary directory using sciencebasepy."""
#     downloaded_files = []
#     sb = SbSession()

#     for item_id in tqdm(item_ids, desc="Downloading TIF files from ScienceBase"):
#         try:
#             item_json = sb.get_item(item_id)
#             files_info = sb.get_item_file_info(item_json)

#             for file_info in files_info:
#                 if file_info["name"].lower().endswith(".tif"):
#                     file_path = temp_dir / file_info["name"]
#                     sb.download_file(file_info["url"], str(file_path))
#                     downloaded_files.append(file_path)

#         except Exception as e:
#             logger.error(f"Error downloading files from item {item_id}: {e}")
#             continue

#     return sorted(downloaded_files)


def download_and_extract_tifs(item_ids: Sequence[str], temp_dir: Path) -> list[Path]:
    """Downloads and extracts TIF files from ZIP archives to a temporary directory."""
    downloaded_files = []
    sb = SbSession()

    for item_id in tqdm(item_ids, desc="Downloading TIF files from ScienceBase"):
        try:
            item_json = sb.get_item(item_id)
            files_info = sb.get_item_file_info(item_json)

            logger.info("Found %d files for item %s", len(files_info), item_id)

            # Look for ZIP files containing habitat maps
            for file_info in files_info:
                if "HabMap" in file_info["name"] and file_info["name"].endswith(".zip"):
                    zip_path = temp_dir / file_info["name"]
                    logger.info("Downloading ZIP file to: %s", zip_path)

                    # Download the ZIP file
                    sb.download_file(file_info["url"], str(zip_path))

                    # Extract TIF files from the ZIP
                    with zipfile.ZipFile(zip_path) as zf:
                        for zip_info in zf.filelist:
                            if zip_info.filename.lower().endswith(".tif"):
                                logger.info(
                                    "Extracting TIF file: %s", zip_info.filename
                                )

                                tif_path = temp_dir / zip_info.filename
                                Path(tif_path).write_bytes(zf.read(zip_info.filename))
                                downloaded_files.append(tif_path)

                    # Clean up the ZIP file after extraction
                    zip_path.unlink()

        except Exception as e:
            logger.error("Error processing item %s: %s", item_id, e)
            logger.exception("Full traceback:")
            continue

    logger.info("Total TIF files extracted: %d", len(downloaded_files))
    logger.info("Extracted TIF files: %s", downloaded_files)

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
            # Download and process files using ScienceBase item IDs
            tif_files = download_and_extract_tifs(
                HABITAT_ITEM_IDS, temp_path
            )  # Changed line
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
