# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "geopandas",
#     "pandas",
#     "numpy",
#     "exactextract",
#     "rasterio",
#     "setuptools",
#     "sciencebasepy",
#     "tqdm",
#     "pyarrow",
#     "requests"
# ]
# ///

"""
Process and analyze USGS Gap Analysis Project Species Habitat Maps data.

This script downloads, extracts, and analyzes habitat data from USGS ScienceBase to
determine the percentage of habitat for specific species within US counties.

These habitat maps represent species distribution based on 2001 ground conditions and
use 30-meter resolution rasters in Albers Conical Equal Area projection (EPSG:5070).

Key Classes:
- `ScienceBaseClient`: Handles interactions with USGS ScienceBase.
- `RasterSet`: Manages a collection of raster files.
- `HabitatDataProcessor`: Orchestrates the data processing workflow.
"""

from __future__ import annotations

import argparse
import logging
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.feather
import pyarrow.parquet
import requests
from exactextract import exact_extract
from sciencebasepy import SbSession

if TYPE_CHECKING:
    from collections.abc import Sequence

# Set up module-level logger
logger = logging.getLogger(__name__)

# Type Aliases
ItemId = str
SpeciesInfo = dict[str, dict[str, str]]
CountyDataFrame = gpd.GeoDataFrame
RasterPath = Path
ZipPath = Path
CountyId = str
SpeciesCode = str
ProcessedDataFrame = pd.DataFrame
FileExtension = Literal[".csv", ".parquet", ".arrow"]
ExactExtractOp = Literal["unique", "frac"]


FILE_DIR = Path(__file__).parent
DATA_DIR = FILE_DIR.parent / "data"
VECTOR_FP = DATA_DIR / "us-10m.json"
VECTOR_URL = "https://vega.github.io/vega-datasets/data/us-10m.json"

HABITAT_ITEM_IDS: Sequence[ItemId] = [
    # "58fa6137e4b0b7ea5452571c", small files for testing
    # "58fe0ab2e4b007492829457b" small files for testing
    "58fa64ece4b0b7ea545257e3",  # Coyote
    "58fa513ce4b0b7ea5452521a",  # Cardinal
    "58fe0a6be4b007492829456e",  # Alligator
    "58fa3f0be4b0b7ea54524859",  # American bullfrog
]


class ScienceBaseClient:
    """Handles interactions with ScienceBase for downloading and retrieving item information."""

    def __init__(self) -> None:
        """Initializes the ScienceBase client with a session."""
        self.sb = SbSession()

    def download_zip_files(
        self, item_ids: Sequence[ItemId], temp_dir: Path
    ) -> list[ZipPath]:
        """
        Downloads ZIP files from ScienceBase to a temporary directory.

        Returns
        -------
            list[ZipPath]: A list of paths to the downloaded ZIP files.
        """
        downloaded_zips: list[ZipPath] = []

        for item_id in item_ids:
            try:
                item_json = self.sb.get_item(item_id)
                files_info = self.sb.get_item_file_info(item_json)

                for file_info in files_info:
                    if "HabMap" in file_info["name"] and file_info["name"].endswith(
                        ".zip"
                    ):
                        zip_path = temp_dir / file_info["name"]
                        self.sb.download_file(file_info["url"], str(zip_path))
                        downloaded_zips.append(zip_path)

            except Exception as e:  # Catch generic Exception
                if isinstance(e, requests.exceptions.RequestException):
                    logger.error(
                        "Error downloading files for item ID %s: %s", item_id, e
                    )
                else:
                    logger.error(
                        "An unexpected error occurred for item ID %s: %s", item_id, e
                    )
                continue  # Go to the next item_id

        return sorted(downloaded_zips)  # ALWAYS return the list

    def get_species_info(self, item_ids: Sequence[ItemId]) -> SpeciesInfo:
        """
        Retrieves species information from ScienceBase items.

        Returns
        -------
            SpeciesInfo: A dictionary containing species information.
        """
        species_info: SpeciesInfo = {}

        for item_id in item_ids:
            try:
                item_json = self.sb.get_item(item_id)

                species_code = None
                common_name = None
                scientific_name = None
                for identifier in item_json["identifiers"]:
                    if (
                        identifier["scheme"]
                        == "https://www.sciencebase.gov/vocab/category/bis/bis_identifiers/GAP_SpeciesCode"
                    ):
                        species_code = identifier["key"]
                    elif (
                        identifier["scheme"]
                        == "https://www.sciencebase.gov/vocab/category/bis/bis_identifiers/CommonName"
                    ):
                        common_name = identifier["key"]
                    elif (
                        identifier["scheme"]
                        == "https://www.sciencebase.gov/vocab/category/bis/bis_identifiers/ScientificName"
                    ):
                        scientific_name = identifier["key"]

                    if species_code:
                        species_info[species_code] = {
                            "item_id": item_id,
                            "CommonName": common_name or "Not Available",
                            "ScientificName": scientific_name or "Not Available",
                        }
            except Exception as e:  # Catch generic Exception
                if isinstance(e, requests.exceptions.RequestException):
                    logger.error(
                        "Error getting species info for item ID %s: %s", item_id, e
                    )
                else:
                    logger.error(
                        "An unexpected error occurred for item ID %s: %s", item_id, e
                    )
                continue

        return species_info


class RasterSet:
    """Represents a set of raster files and provides methods for extraction."""

    def __init__(self, zip_files: list[ZipPath], temp_dir: Path) -> None:
        """Initializes the RasterSet with a list of ZIP file paths and a temporary directory."""
        self.zip_files = zip_files
        self.temp_dir = temp_dir
        self.tif_files: list[RasterPath] = []

    def extract_tifs_from_zips(self) -> list[RasterPath]:
        """
        Extracts TIF files from ZIP archives.

        ZIP files are deleted after extraction.

        Returns
        -------
            list[RasterPath]: A list of paths to the extracted TIFF files.
        """
        extracted_tifs: list[RasterPath] = []

        for zip_path in self.zip_files:
            with zipfile.ZipFile(zip_path) as zf:
                for zip_info in zf.filelist:
                    if zip_info.filename.lower().endswith(".tif"):
                        tif_path = self.temp_dir / zip_info.filename
                        Path(tif_path).write_bytes(zf.read(zip_info.filename))
                        extracted_tifs.append(tif_path)

            zip_path.unlink()
        self.tif_files = sorted(extracted_tifs)
        return self.tif_files


class HabitatDataProcessor:
    """
    Manages the workflow for processing habitat data.

    This class orchestrates the download, extraction, analysis, and output
    of GAP species habitat maps to calculate habitat percentages within US counties.
    """

    def __init__(
        self,
        item_ids: Sequence[ItemId],
        vector_fp: Path,
        output_dir: Path,
        output_format: str = "arrow",
    ) -> None:
        """
        Initializes the HabitatDataProcessor.

        Args:
            item_ids: A sequence of ScienceBase item IDs.
            vector_fp: Path to the vector file (GeoJSON) containing county boundaries.
            output_dir: Path to the output directory.
            output_format: Output format for results (csv, parquet, arrow). Defaults to arrow.
        """
        self.item_ids = item_ids
        self.vector_fp = vector_fp
        self.output_dir = output_dir
        self.output_format = output_format  # Store the output format
        self.sciencebase_client = ScienceBaseClient()  # Create an instance
        self.gdf: CountyDataFrame = self._load_county_data()

    def _load_county_data(self) -> CountyDataFrame:
        """
        Loads and prepares the county geometry data from a local file or URL.

        The county data is expected to be in GeoJSON format and EPSG:4326 projection.
        It is reprojected to EPSG:5070 for analysis.

        Returns
        -------
            CountyDataFrame: A GeoDataFrame containing county geometries in EPSG:5070.
        """
        try:
            # Try loading from the local file path
            if Path(self.vector_fp).exists():
                logger.info("Loading vector data from local file: %s", self.vector_fp)
                gdf: CountyDataFrame = gpd.read_file(self.vector_fp, layer="counties")
            else:
                logger.info(
                    "Local file not found: %s. Attempting to load from URL: %s",
                    self.vector_fp,
                    VECTOR_URL,
                )
                # Try loading from the URL
                try:
                    gdf = gpd.read_file(
                        VECTOR_URL, layer="counties"
                    )  # GeoPandas can read directly from a URL!
                except Exception as e:
                    msg = (
                        f"Could not load vector data from URL: {VECTOR_URL}. Error: {e}"
                    )
                    raise FileNotFoundError(msg) from e

            gdf = gdf.set_crs(epsg=4326, allow_override=True)
            if gdf.crs is None or gdf.crs.to_epsg() != 4326:
                msg = "Input GeoJSON must be in EPSG:4326, or have a valid CRS definition."
                raise ValueError(msg)
            gdf = gdf.to_crs(epsg=5070)
            gdf = gdf[~gdf.is_empty]
            gdf.columns = ["county_id", "geometry"]
            return gdf

        except Exception as e:
            logger.error("Error loading county data: %s", e)
            raise  # Re-raise the exception to stop execution

    def process_habitat_data(
        self, temp_dir: Path
    ) -> tuple[list[RasterPath], SpeciesInfo]:
        """
        Processes habitat data: downloads ZIP files, extracts TIFFs, and retrieves species info.

        Args:
            temp_dir (Path): Path to a temporary directory to store downloaded and extracted files.

        Returns
        -------
            tuple[list[RasterPath], SpeciesInfo]: A tuple containing:
                - list[RasterPath]: List of paths to extracted TIFF raster files.
                - SpeciesInfo: Dictionary of species information.
        """
        logger.info("Retrieving species information from ScienceBase")
        species_info = self.sciencebase_client.get_species_info(self.item_ids)

        logger.info("Downloading habitat data files")
        zip_files = self.sciencebase_client.download_zip_files(self.item_ids, temp_dir)

        logger.info("Extracting raster files")
        raster_set = RasterSet(zip_files, temp_dir)
        tif_files = raster_set.extract_tifs_from_zips()

        return tif_files, species_info

    def analyze_habitat_rasters(
        self, tif_files: list[RasterPath], species_info: SpeciesInfo
    ) -> ProcessedDataFrame:
        """
        Analyzes habitat raster files against county geometries to calculate habitat percentages.

        Uses the `exactextract` library to perform zonal statistics.
        Focuses on year-round habitat (value 3) from the raster data.
        Habitat values in the rasters are:
        - 1: Summer habitat
        - 2: Winter habitat
        - 3: Year-round habitat

        Args:
            tif_files (list[RasterPath]): List of paths to habitat raster TIFF files.
            species_info (SpeciesInfo): Dictionary of species information.

        Returns
        -------
            ProcessedDataFrame: DataFrame containing county IDs, species codes, names, and habitat percentages.
        """
        # Define operations for exact_extract:
        # - unique: Find all unique values in each county
        # - frac: Calculate fraction of each unique value's coverage
        # 255 is used as the default_value for areas outside raster coverage,
        # and is assumed to NOT be a valid habitat code.
        ops: list[ExactExtractOp] = [
            "unique(default_value=255)",
            "frac(default_value=255)",
        ]
        results = exact_extract(
            rast=tif_files,
            vec=self.gdf,
            ops=ops,
            include_cols="county_id",
            output="pandas",
            progress=True,
        )

        # Log the columns generated by exact_extract
        logger.debug("Columns generated by exact_extract: %s", results.columns.tolist())

        # List to store processed data for each species
        all_data = []

        # Process each raster file's results
        for tif_file in tif_files:
            # Extract species code from filename
            stem: str = tif_file.stem
            species: SpeciesCode = stem.split("_")[0]

            # Determine column names based on number of raster files
            if len(tif_files) > 1:
                unique_col = f"{stem}_unique"
                frac_col = f"{stem}_frac"
            else:
                unique_col = "unique"
                frac_col = "frac"

            # Check if the required columns exist
            if unique_col not in results.columns or frac_col not in results.columns:
                logger.warning("Required columns not found for %s. Skipping.", species)
                continue

            # Log the contents of the unique and frac columns
            logger.debug("Contents of %s: %s", unique_col, results[unique_col].head())
            logger.debug("Contents of %s: %s", frac_col, results[frac_col].head())

            # Convert columns to NumPy arrays
            unique_values = np.array(results[unique_col].to_list(), dtype=object)
            frac_values = np.array(results[frac_col].to_list(), dtype=object)

            # Check if the unique and frac columns contain non-empty lists
            if len(unique_values) == 0 or len(frac_values) == 0:
                logger.warning(
                    "No valid data found in columns for %s. Skipping.", species
                )
                continue

            # Repeat county_ids based on array lengths
            county_ids = np.repeat(
                results["county_id"].values, [len(arr) for arr in unique_values]
            )

            # Flatten arrays
            unique_flat = np.concatenate(unique_values)
            frac_flat = np.concatenate(frac_values)

            # Filter for year-round habitat (value 3)
            # Note: This could be expanded to include seasonal habitat (values 1-2)
            mask = unique_flat == 3

            # Get species metadata
            species_metadata = species_info.get(
                species, {"CommonName": "Unknown", "ScientificName": "Unknown"}
            )

            species_df: ProcessedDataFrame = pd.DataFrame({
                "county_id": county_ids[mask],
                "species_code": species,
                "common_name": species_metadata["CommonName"],
                "scientific_name": species_metadata["ScientificName"],
                "pct": frac_flat[mask],
            })

            all_data.append(species_df)

        # Check if all_data is empty before concatenating
        if not all_data:
            logger.warning("No valid data found for any species.")
            return pd.DataFrame()

        # Combine all species data
        return pd.concat(all_data, ignore_index=True)

    # ... (rest of the code remains the same)

    def save_results(
        self, results_df: ProcessedDataFrame, species_info: SpeciesInfo
    ) -> None:
        """
        Saves the processed results to CSV, Parquet, or Arrow files.

        Files are named 'species' with the corresponding file extension.  Handles
        dictionary encoding for Arrow and Parquet output.

        Args:
            results_df (ProcessedDataFrame): DataFrame containing the processed habitat data.
            species_info (SpeciesInfo): Dictionary of species information.
        """
        if not results_df.empty:
            self.output_dir.mkdir(exist_ok=True)

            results_df = results_df.rename(
                columns={"species_code": "GAP_Species", "pct": "percent_habitat"}
            )
            results_df = results_df[["county_id", "GAP_Species", "percent_habitat"]]

            species_info_df = pd.DataFrame.from_dict(species_info, orient="index")
            final_df: ProcessedDataFrame = results_df.merge(
                species_info_df, left_on="GAP_Species", right_index=True
            )

            final_df = final_df[
                [
                    "item_id",
                    "CommonName",
                    "ScientificName",
                    "GAP_Species",
                    "county_id",
                    "percent_habitat",
                ]
            ]

            final_df["percent_habitat"] = final_df["percent_habitat"].round(4)

            if self.output_format == "csv":
                final_df.to_csv(self.output_dir / "species.csv", index=False)
            else:  # Handle both Parquet and Arrow
                table = pa.Table.from_pandas(final_df)
                for col in ["item_id", "CommonName", "county_id"]:
                    table = table.set_column(
                        table.schema.get_field_index(col),
                        col,
                        pa.compute.dictionary_encode(table[col]),
                    )

                if self.output_format == "parquet":
                    pa.parquet.write_table(table, self.output_dir / "species.parquet")
                else:  # Default to Arrow
                    with (
                        pa.OSFile(str(self.output_dir / "species.arrow"), "wb") as sink,
                        pa.RecordBatchFileWriter(sink, table.schema) as writer,
                    ):
                        writer.write_table(table)

    # ... (rest of the code remains the same)

    def run(self) -> None:
        """Runs the complete habitat data processing workflow."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            logger.info("Step 1/3: Downloading and extracting habitat data files")
            tif_files, species_info = self.process_habitat_data(temp_dir)

            species_count = len(species_info)
            logger.info(
                "Step 2/3: Beginning habitat analysis for %d species", species_count
            )
            results_df = self.analyze_habitat_rasters(tif_files, species_info)

            logger.info("Step 3/3: Saving analysis results")
            self.save_results(results_df, species_info)
            logger.info("Analysis complete. Results saved to: %s", self.output_dir)

        finally:
            if temp_dir.exists():
                for file in temp_dir.glob("*"):
                    file.unlink()
                temp_dir.rmdir()


def main() -> None:
    """Main entry point for the script: parses command-line arguments and runs the processor."""
    parser = argparse.ArgumentParser(
        description="Process and analyze GAP National Terrestrial Ecosystems data."
    )
    parser.add_argument(
        "--item_ids",
        nargs="+",
        type=str,
        default=HABITAT_ITEM_IDS,
        help="List of ScienceBase item IDs (space-separated).",
    )
    parser.add_argument(
        "--vector_fp",
        type=str,
        default=str(VECTOR_FP),
        help="Path to the vector file (GeoJSON).",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(DATA_DIR),
        help="Output directory for results.",
    )
    parser.add_argument(
        "-D",
        "--debug",
        action="store_true",
        help="Enable debug logging.",
    )
    parser.add_argument(
        "--output_format",
        type=str,
        default="arrow",
        choices=["csv", "parquet", "arrow"],
        help="Output format (csv, parquet, or arrow). Defaults to arrow.",
    )

    args = parser.parse_args()

    # Updated logging configuration
    log_format = "%(asctime)s [%(levelname)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format=log_format, datefmt=date_format)

    logger.info("Initializing GAP habitat analysis pipeline")
    processor = HabitatDataProcessor(
        args.item_ids, Path(args.vector_fp), Path(args.output_dir), args.output_format
    )
    processor.run()


if __name__ == "__main__":
    main()
