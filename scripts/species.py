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
#     "requests",
# ]
# ///

"""
Process and analyze USGS Gap Analysis Project (GAP) Species Habitat Maps.

This script downloads, extracts, and analyzes data from USGS ScienceBase to calculate
species habitat coverage within US counties. It uses a TOML configuration file
(_data/species.toml) for settings and US county boundaries from a 1:10M-scale TopoJSON
file derived from Census Bureau cartographic boundary files.

The habitat maps are provided as 30-meter resolution raster files in Albers Conical
Equal Area projection (EPSG:5070). The script overlays these raster habitat maps with
county boundary vectors to calculate the percentage of year-round habitat (value 3 in
rasters) within each county. Values 1 and 2 in the rasters represent summer and winter
habitat respectively, though these are not currently analyzed.

Output is available in multiple formats (CSV, Parquet, or Arrow) with dictionary-encoded
columns for efficient storage. Results include species metadata (GAP species code, common
name, scientific name) and habitat percentages by county. The script includes comprehensive
logging and error handling, with debug options configurable via TOML settings. Downloaded
and extracted files are managed in a temporary directory and cleaned up after processing.

Key Classes:
- `ScienceBaseClient`: Downloads habitat data and retrieves species metadata from USGS ScienceBase.
- `RasterSet`: Extracts and validates TIFF files from downloaded ZIP archives.
- `HabitatDataProcessor`: Orchestrates the complete workflow including vector data loading,
  habitat analysis, and output formatting.
"""

from __future__ import annotations

import logging
import tempfile
import tomllib
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
type ItemId = str
type SpeciesInfo = dict[str, dict[str, str]]
type CountyDataFrame = gpd.GeoDataFrame
type RasterPath = Path
type ZipPath = Path
type CountyId = str
type SpeciesCode = str
type ProcessedDataFrame = pd.DataFrame
type FileExtension = Literal[".csv", ".parquet", ".arrow"]
type ExactExtractOp = Literal["unique(default_value=255)", "frac(default_value=255)"]


FILE_DIR = Path(__file__).parent
CONFIG_DIR = FILE_DIR.parent / "_data"  # Configuration directory
DATA_DIR = FILE_DIR.parent / "data"
VECTOR_FP = DATA_DIR / "us-10m.json"
VECTOR_URL = "https://vega.github.io/vega-datasets/data/us-10m.json"


class ScienceBaseClient:
    """Handles interactions with ScienceBase for downloading and retrieving item information."""

    def __init__(self) -> None:
        """
        Initializes the ScienceBase client with a session.

        Establishes a ScienceBase session (`SbSession`) for interacting with the USGS ScienceBase API.
        This session is used for authentication and managing requests to ScienceBase.
        """
        self.sb = SbSession()

    def download_zip_files(
        self, item_ids: Sequence[ItemId], temp_dir: Path
    ) -> list[ZipPath]:
        """
        Downloads ZIP files from ScienceBase associated with the given ScienceBase ID to a temporary directory.

        Each ZIP file is expected to contain a habitat map raster (TIFF).

        Args:
                item_ids: A sequence of ScienceBase item IDs to download files for.
                temp_dir: Path to a temporary directory where ZIP files will be downloaded.

        Returns
        -------
                list[ZipPath]: A list of paths to the downloaded ZIP files, sorted alphabetically.
                           Returns an empty list if no ZIP files are successfully downloaded.
                           Logs errors to the logger if downloads fail for specific item IDs,
                           but continues processing other item IDs.
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

        Extracts metadata (species code, common name, scientific name) from ScienceBase
        items based on their identifiers.

        Args:
            item_ids: A sequence of ScienceBase item IDs to retrieve information for.



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
                            "common_name": common_name or "Not Available",
                            "scientific_name": scientific_name or "Not Available",
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
        Extracts TIFF files from ZIP archives.

        Assumes and enforces that each ZIP file contains *exactly one* .tif file.
        Raises a RuntimeError if this is not the case.

        Returns a sorted list of paths to the extracted TIFF files.
        """
        extracted_tifs: list[RasterPath] = []

        for zip_path in self.zip_files:
            with zipfile.ZipFile(zip_path) as zf:  # Use context manager for ZipFile
                zip_root = zipfile.Path(zf)
                tif_files = list(zip_root.glob("*.tif"))

                if len(tif_files) != 1:
                    msg = (
                        f"Expected exactly one .tif file in {zip_path}, "
                        f"found {len(tif_files)}"
                    )
                    raise RuntimeError(msg)

                tif_file = tif_files[0]  # Get the single TIF file
                output_path = self.temp_dir / tif_file.name
                with tif_file.open("rb") as src, output_path.open("wb") as dst:
                    dst.write(src.read())
                extracted_tifs.append(output_path)

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

        Args
        ----
            tif_files (list[RasterPath]): List of paths to habitat raster TIFF files.
            species_info (SpeciesInfo): Dictionary of species information.

        Returns
        -------
            ProcessedDataFrame: DataFrame containing county IDs, species codes, names, and habitat percentages.

        Note
        ----
            A `RuntimeWarning` about spatial reference systems may appear. This is often benign,
            resulting from minor differences in coordinate system descriptions (WKT) between
            vector and raster data, even when projections are effectively the same (EPSG:5070).
            It does not impact analysis accuracy here and is addressed in newer versions of `exactextract`
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
                "common_name": species_metadata["common_name"],
                "scientific_name": species_metadata["scientific_name"],
                "pct": frac_flat[mask],
            })

            all_data.append(species_df)

        # Check if all_data is empty before concatenating
        if not all_data:
            logger.warning("No valid data found for any species.")
            return pd.DataFrame()

        # Combine all species data
        return pd.concat(all_data, ignore_index=True)

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

            # Rename columns to allow for future expansion of the dataset to include summer
            # or winter-only habitat data, or range data that may be summer/winter/yearround.
            results_df = results_df.rename(
                columns={
                    "species_code": "gap_species_code",
                    "pct": "habitat_yearround_pct",
                }
            )
            results_df = results_df[
                ["county_id", "gap_species_code", "habitat_yearround_pct"]
            ]

            species_info_df = pd.DataFrame.from_dict(species_info, orient="index")
            final_df: ProcessedDataFrame = results_df.merge(
                species_info_df, left_on="gap_species_code", right_index=True
            )

            final_df = final_df[
                [
                    "item_id",
                    "common_name",
                    "scientific_name",
                    "gap_species_code",
                    "county_id",
                    "habitat_yearround_pct",
                ]
            ]

            final_df["habitat_yearround_pct"] = final_df["habitat_yearround_pct"].round(
                4
            )

            if self.output_format == "csv":
                final_df.to_csv(self.output_dir / "species.csv", index=False)
            else:  # Handle both Parquet and Arrow
                table = pa.Table.from_pandas(final_df)
                for col in ["item_id", "common_name", "county_id"]:
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
    """Main entry point: loads TOML config, runs the processor."""
    # --- Configuration Loading (TOML) ---
    config_path = CONFIG_DIR / "species.toml"  # Correct path
    try:
        with config_path.open("rb") as f:
            config = tomllib.load(f)
    except FileNotFoundError:
        logger.error("Configuration file not found: %s", config_path)
        raise  # Critical error: stop execution
    except tomllib.TOMLDecodeError as e:
        logger.error("Error decoding TOML file: %s", e)
        raise

    processing_config = config.get("processing", {})
    if not processing_config:
        logger.error("Missing [processing] table in TOML configuration.")
        msg = "Missing [processing] table in TOML configuration."
        raise ValueError(msg)

    # --- Extract Configuration Values ---
    # Require item_ids in configuration
    if "item_ids" not in processing_config:
        logger.error("Required configuration 'item_ids' not found in TOML file")
        msg = "Missing required configuration: item_ids must be specified in the TOML file"
        raise ValueError(msg)

    item_ids = processing_config["item_ids"]
    vector_fp = processing_config.get("vector_fp", str(VECTOR_FP))
    output_dir = processing_config.get("output_dir", str(DATA_DIR))
    output_format = processing_config.get("output_format", "arrow")
    debug = processing_config.get("debug", False)

    # --- Resolve Relative Paths ---
    #  Make paths absolute, relative to the *config file*, not the CWD
    vector_fp = (config_path.parent / vector_fp).resolve()
    output_dir = (config_path.parent / output_dir).resolve()

    # --- Basic Configuration Validation ---
    if not isinstance(item_ids, list) or not item_ids:
        logger.error("`item_ids` in the TOML file must be a non-empty list.")
        msg = "`item_ids` must be a non-empty list."
        raise TypeError(msg)

    if not isinstance(vector_fp, str | Path):
        logger.error("`vector_fp` must be a string or Path.")
        msg = "`vector_fp` must be a string or Path."
        raise TypeError(msg)
    vector_fp = Path(vector_fp)

    if not isinstance(output_dir, str | Path):
        logger.error("`output_dir` must be a string or Path.")
        msg = "`output_dir` must be a string or Path."
        raise TypeError(msg)
    output_dir = Path(output_dir)

    if output_format not in {"csv", "parquet", "arrow"}:
        logger.error("Invalid `output_format`: %s", output_format)
        msg = f"Invalid `output_format`: {output_format}"
        raise ValueError(msg)

    if not isinstance(debug, bool):
        logger.error("`debug` must be a boolean.")
        msg = "`debug` must be a boolean."
        raise TypeError(msg)

    # --- Logging Setup ---
    log_format = "%(asctime)s [%(levelname)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=log_level, format=log_format, datefmt=date_format)

    # --- Initialize and Run Processor ---
    logger.info("Initializing GAP habitat analysis pipeline")
    processor = HabitatDataProcessor(item_ids, vector_fp, output_dir, output_format)
    processor.run()


if __name__ == "__main__":
    main()
