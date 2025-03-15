"""
Process and analyze USGS Gap Analysis Project (GAP) Species Habitat Maps.

This script downloads, extracts, and analyzes data from USGS ScienceBase to calculate
species habitat coverage within US counties in the contiguous (conterminous) United States.
It uses a TOML configuration file (_data/species.toml) for settings and US county
boundaries from a 1:10M-scale TopoJSON file derived from Census Bureau cartographic
boundary files.

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
import shutil
import sys
import tempfile
import time
import tomllib
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, LiteralString, TypedDict, cast

import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.feather
import pyarrow.parquet as pa_pq
import requests
from exactextract import exact_extract
from sciencebasepy import SbSession

if TYPE_CHECKING:
    from collections.abc import Sequence

    from typing_extensions import TypeIs

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


REPO_ROOT: Path = Path(__file__).parent.parent
INPUT_DIR: Path = REPO_ROOT / "_data"
OUTPUT_DIR: Path = REPO_ROOT / "data"

CONFIG_FP: Path = INPUT_DIR / "species.toml"
VECTOR_FP: Path = OUTPUT_DIR / "us-10m.json"
VECTOR_URL: LiteralString = "https://vega.github.io/vega-datasets/data/us-10m.json"


class ScienceBaseClient:
    """
    Handles interactions with ScienceBase for downloading and retrieving item information.

    Establishes a ScienceBase session (`SbSession`) for interacting with the USGS ScienceBase API.
    This session is used for authentication and managing requests to ScienceBase.
    """

    def __init__(self) -> None:
        self.sb = SbSession()

    def download_zip_files(
        self, item_ids: Sequence[ItemId], temp_dir: Path
    ) -> list[ZipPath]:
        """
        Downloads ZIP files from ScienceBase associated with the given ScienceBase ID to a temporary directory.

        Each ZIP file is expected to contain a habitat map raster (TIFF).

        Parameters
        ----------
        item_ids
            A sequence of ScienceBase item IDs to download files for.
        temp_dir
            Path to a temporary directory where ZIP files will be downloaded.

        Returns
        -------
        list[ZipPath]: A list of paths to the downloaded ZIP files, sorted alphabetically.
        Returns an empty list if no ZIP files are successfully downloaded.
        logs errors to the logger if downloads fail for specific item IDs,
        but continues processing other item IDs.
        """
        downloaded_zips: list[ZipPath] = []
        logger.info(
            "Starting download of files from %s ScienceBase items", len(item_ids)
        )

        for i, item_id in enumerate(item_ids):
            logger.info("Processing item %s/%s - %s", i + 1, len(item_ids), item_id)
            try:
                item_json = self.sb.get_item(item_id)
                files_info = self.sb.get_item_file_info(item_json)

                hab_map_files = [
                    f
                    for f in files_info
                    if "HabMap" in f["name"] and f["name"].endswith(".zip")
                ]

                if not hab_map_files:
                    logger.info("No HabMap zip files found for item %s", item_id)
                    continue

                logger.info(
                    "Found %s HabMap zip files for item %s", len(hab_map_files), item_id
                )

                for file_info in hab_map_files:
                    zip_path = temp_dir / file_info["name"]
                    file_size_mb = file_info.get("size", 0) / (1024 * 1024)
                    logger.info(
                        "Downloading: %s (%.1f MB)", file_info["name"], file_size_mb
                    )

                    try:
                        self._download_file_with_progress(
                            file_info["url"], str(zip_path)
                        )
                        downloaded_zips.append(zip_path)
                        logger.info("Download complete: %s", file_info["name"])
                    except (OSError, requests.exceptions.RequestException) as e:
                        logger.error("Error downloading %s: %s", file_info["name"], e)

            except (requests.exceptions.RequestException, ValueError, KeyError) as e:
                if isinstance(e, requests.exceptions.RequestException):
                    logger.error(
                        "Error downloading files for item ID %s: %s", item_id, e
                    )
                else:
                    logger.error(
                        "An unexpected error occurred for item ID %s: %s", item_id, e
                    )
                continue  # Go to the next item_id

        logger.info(
            "Download complete! %s files downloaded successfully.", len(downloaded_zips)
        )
        return sorted(downloaded_zips)  # ALWAYS return the list

    def _download_file_with_progress(self, url: str, destination: str) -> None:
        """Downloads a file with a progress bar."""
        try:
            with requests.get(url, stream=True, timeout=(10, 60)) as response:
                response.raise_for_status()
                total_size = int(response.headers.get("content-length", 0))

                with Path(destination).open("wb") as f:
                    if total_size == 0:
                        f.write(response.content)
                        logger.info("Downloaded file of unknown size")
                    else:
                        downloaded = 0
                        chunk_size = 8192 * 16  # Increased chunk size for performance
                        start_time = time.time()
                        last_update_time = start_time

                        filename = Path(destination).name
                        mb_total = total_size / (1024 * 1024)
                        logger.info("Downloading: %s (%.1fMB)", filename, mb_total)

                        bar_length = 30
                        bar = " " * bar_length
                        sys.stdout.write(f"\rProgress: [{bar}] 0.0% (0.0MB)")
                        sys.stdout.flush()

                        for chunk in response.iter_content(chunk_size=chunk_size):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)

                                current_time = time.time()
                                if current_time - last_update_time >= 0.1:
                                    last_update_time = current_time
                                    percent = min(100, (downloaded / total_size) * 100)
                                    filled_length = int(bar_length * percent / 100)
                                    bar = "=" * filled_length + " " * (
                                        bar_length - filled_length
                                    )
                                    mb_downloaded = downloaded / (1024 * 1024)

                                    elapsed = current_time - start_time
                                    if elapsed > 0:
                                        speed = downloaded / elapsed / (1024 * 1024)
                                        remaining = (
                                            (total_size - downloaded)
                                            / (speed * 1024 * 1024)
                                            if speed > 0
                                            else 0
                                        )
                                        eta = (
                                            f" ETA: {int(remaining)}s"
                                            if remaining > 0
                                            else ""
                                        )
                                    else:
                                        speed = 0
                                        eta = ""

                                    sys.stdout.write(
                                        f"\rProgress: [{bar}] {percent:.1f}% ({mb_downloaded:.1f}MB/{mb_total:.1f}MB) {speed:.1f}MB/s{eta}"
                                    )
                                    sys.stdout.flush()

                        sys.stdout.write("\n")
                        sys.stdout.flush()

                        elapsed = time.time() - start_time
                        avg_speed = (
                            downloaded / (elapsed * 1024 * 1024) if elapsed > 0 else 0
                        )
                        logger.info(
                            "Download complete: %s (%.1fMB in %.1fs, avg: %.1fMB/s)",
                            filename,
                            mb_total,
                            elapsed,
                            avg_speed,
                        )
        except requests.exceptions.Timeout:
            logger.error("Timeout occurred while downloading %s", url)
            raise
        except requests.exceptions.RequestException as e:
            logger.error("Request failed: %s", e)
            raise

    def get_species_info(self, item_ids: Sequence[ItemId]) -> SpeciesInfo:
        """
        Retrieves species information from ScienceBase items.

        Extracts metadata (species code, common name, scientific name) from ScienceBase
        items based on their identifiers.

        Parameters
        ----------
        item_ids
            A sequence of ScienceBase item IDs to retrieve information for.

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
            except (requests.exceptions.RequestException, ValueError, KeyError) as e:
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

    Parameters
    ----------
    item_ids
        A sequence of ScienceBase item IDs.
    vector_fp
        Path to the vector file (GeoJSON) containing county boundaries.
    output_dir
        Path to the output directory.
    output_format
        Output format for results.
    """

    def __init__(
        self,
        item_ids: Sequence[ItemId],
        vector_fp: Path,
        output_dir: Path,
        output_format: FileExtension,
        config: Config,
    ) -> None:
        self.item_ids: Sequence[ItemId] = item_ids
        self.vector_fp: Path = vector_fp
        self.output_dir: Path = output_dir

        if not is_file_extension(output_format):
            msg = (
                f"Invalid output_format: {output_format}. "
                f"Must be one of {['.csv', '.parquet', '.arrow']!r}"
            )
            raise ValueError(msg)

        self.output_format: FileExtension = output_format
        self.config: Config = config
        self.sciencebase_client = ScienceBaseClient()
        self.gdf: CountyDataFrame = self._load_county_data()

    def _load_county_data(self) -> CountyDataFrame:
        """
        Loads county boundary data and prepares it for habitat analysis.

        This function:
        1. Loads county boundaries from a file or URL
        2. Filters areas by FIPS code to focus on the conterminous United States
        3. Converts the map to a projection that accurately represents area in the conterminous US
        4. Returns clean county data ready for analysis

        Returns
        -------
        CountyDataFrame: A dataset of conterminous US county boundaries
        """
        return (
            self._load_raw_county_data()
            .pipe(self._prepare_county_data)
            .pipe(self._filter_to_conterminous_us)
            .pipe(self._finalize_county_data)
        )

    def _load_raw_county_data(self) -> CountyDataFrame:
        """Loads raw county boundary data from file or URL."""
        if Path(self.vector_fp).exists():
            logger.info("Loading county boundaries from local file: %s", self.vector_fp)
            try:
                gdf: CountyDataFrame = gpd.read_file(self.vector_fp, layer="counties")
                logger.info(
                    "Successfully loaded county data with these columns: %s",
                    gdf.columns.tolist(),
                )
                return gdf
            except (OSError, ValueError) as e:
                logger.error("Error reading file: %s", e)
                raise
        else:
            # If local file doesn't exist, try downloading from URL
            logger.info(
                "Local file not found: %s. Trying to download from: %s",
                self.vector_fp,
                VECTOR_URL,
            )
            try:
                # Return directly instead of assigning to a variable first
                return gpd.read_file(VECTOR_URL, layer="counties")
            except (OSError, ValueError) as e:
                msg = (
                    f"Could not download county data from URL: {VECTOR_URL}. Error: {e}"
                )
                raise FileNotFoundError(msg) from e

    def _prepare_county_data(self, gdf: CountyDataFrame) -> CountyDataFrame:
        """Prepares county data by setting CRS and reformatting identifiers."""
        # Make sure the map has the correct coordinate system
        gdf = gdf.set_crs(epsg=4326, allow_override=True)
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            msg = "County map must use standard global coordinates (EPSG:4326)."
            raise ValueError(msg)

        # Rename the county identifier column to 'county_id' for consistency
        if "id" in gdf.columns:
            gdf = gdf.rename(columns={"id": "county_id"})
        else:
            logger.error(
                "County ID column not found. Available columns: %s",
                gdf.columns.tolist(),
            )
            msg = "Required column 'id' missing from county data"
            raise ValueError(msg)

        # Format county FIPS codes consistently (5-digit format with leading zeros)
        gdf["county_id"] = gdf["county_id"].astype(str).str.zfill(5)

        # Handle duplicate counties - variables defined but not used
        # These variables are used in the commented-out duplicate handling code
        # that might be reactivated in the future
        # _ = len(gdf)  # total_records
        # _ = len(gdf["county_id"].unique())  # unique_counties

        # Extract state code from county FIPS code (first 2 digits)
        gdf["state_fips"] = gdf["county_id"].str[:2]

        return gdf

    def _filter_to_conterminous_us(self, gdf: CountyDataFrame) -> CountyDataFrame:
        """Filters out non-conterminous US counties based on FIPS codes from config or defaults to no filtering."""
        # Get excluded FIPS codes from config
        excluded_fips = []
        fips_names = {}

        # Check for filter config
        if (
            "processing" in self.config
            and "geographic_filter" in self.config["processing"]
        ):
            filters = self.config["processing"]["geographic_filter"].get(
                "excluded_fips", []
            )
            for filter_item in filters:
                code = filter_item.get("code")
                name = filter_item.get("name", f"FIPS {code}")
                if code:
                    excluded_fips.append(code)
                    fips_names[code] = name

        # If no filters found in config, log that no filtering will be applied
        if not excluded_fips:
            logger.info(
                "No geographic filter found in config. No areas will be excluded."
            )
            # Return the original DataFrame without filtering
            return gdf

        # Log which areas we're filtering out
        logger.info(
            "Filtering out %d areas by FIPS code to focus on conterminous US",
            len(excluded_fips),
        )

        for fips_code in excluded_fips:
            counties = gdf[gdf["state_fips"] == fips_code]["county_id"].unique()
            area_name = fips_names.get(fips_code, f"FIPS {fips_code}")

            if len(counties) > 0:
                logger.info(
                    "Excluding %d counties with FIPS prefix %s (%s)",
                    len(counties),
                    fips_code,
                    area_name,
                )
                logger.info(
                    "Excluded county FIPS codes: %s", ", ".join(sorted(counties))
                )
            else:
                logger.info(
                    "No counties found with FIPS prefix %s (%s)", fips_code, area_name
                )

        # Apply filter to keep only counties in conterminous US
        filtered_gdf = gdf[~gdf["state_fips"].isin(excluded_fips)].drop(
            columns=["state_fips"]
        )

        logger.info("Analyzing %d counties in conterminous US", len(filtered_gdf))

        return filtered_gdf

    def _finalize_county_data(self, gdf: CountyDataFrame) -> CountyDataFrame:
        """Projects to equal-area and removes invalid geometries."""
        # Convert to an equal-area projection for the conterminous US
        projected_gdf = gdf.to_crs(epsg=5070)

        # Remove any counties with invalid/empty geometries
        valid_counties = projected_gdf[~projected_gdf.is_empty]
        if len(valid_counties) < len(projected_gdf):
            logger.warning(
                "Removed %d counties with invalid boundaries",
                len(projected_gdf) - len(valid_counties),
            )

        return valid_counties

    def process_habitat_data(
        self, temp_dir: Path
    ) -> tuple[list[RasterPath], SpeciesInfo]:
        """
        Processes habitat data: downloads ZIP files, extracts TIFFs, and retrieves species info.

        Parameters
        ----------
        temp_dir
            Path to a temporary directory to store downloaded and extracted files.

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

        Parameters
        ----------
        tif_files
            List of paths to habitat raster TIFF files.
        species_info
            Dictionary of species information.

        Returns
        -------
        ProcessedDataFrame: DataFrame containing county IDs, species codes, names, and habitat percentages.

        Notes
        -----
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
        if not isinstance(results, pd.DataFrame):
            msg = f"Expected `pd.DataFrame` but got {type(results).__name__}"
            raise NotImplementedError(msg)

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
                results["county_id"].to_numpy(), [len(arr) for arr in unique_values]
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
        """Saves processed results with conterminous US (contiguous US) US counties only, filling missing values with zeros."""
        if results_df.empty:
            return

        # Basic setup and column renaming
        self.output_dir.mkdir(exist_ok=True)
        results_df = results_df.rename(
            columns={"species_code": "gap_species_code", "pct": "habitat_yearround_pct"}
        )
        results_df = results_df[
            ["county_id", "gap_species_code", "habitat_yearround_pct"]
        ]

        # Merge with species info and round percentages
        species_info_df = pd.DataFrame.from_dict(species_info, orient="index")
        final_df = results_df.merge(
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
        final_df["habitat_yearround_pct"] = final_df["habitat_yearround_pct"].round(4)

        # Ensure consistent county_id format
        final_df["county_id"] = final_df["county_id"].astype(str).str.zfill(5)

        # Get list of all conterminous US counties (already filtered in _load_county_data)
        conterminous_counties = self.gdf["county_id"].unique()

        # Create complete dataset with zeros for missing counties
        complete_data = []
        for _species, group in final_df.groupby("gap_species_code"):
            # Create template row with species info
            template = {
                col: group[col].iloc[0]
                for col in [
                    "item_id",
                    "common_name",
                    "scientific_name",
                    "gap_species_code",
                ]
            }

            # Create dictionary of existing county data
            county_data = dict(
                zip(group["county_id"], group["habitat_yearround_pct"], strict=False)
            )

            # Add rows for all counties (existing values or zeros)
            for county in conterminous_counties:
                row = template.copy()
                row["county_id"] = county
                row["habitat_yearround_pct"] = county_data.get(county, 0.0)
                complete_data.append(row)

        # Convert to dataframe
        final_df = pd.DataFrame(complete_data)

        # Extract the common functionality for dictionary encoding to a helper function
        def create_dictionary_encoded_table(df: pd.DataFrame) -> pa.Table:
            """Create a PyArrow table with dictionary-encoded columns for efficiency."""
            table = pa.Table.from_pandas(df)
            schema = table.schema
            for col in ["item_id", "common_name", "county_id"]:
                arr = table.column(col).dictionary_encode()
                table = table.set_column(schema.get_field_index(col), col, arr)  # pyright: ignore[reportArgumentType]
            return table

        # Save to specified format
        if self.output_format == ".parquet":
            table = create_dictionary_encoded_table(final_df)
            pa_pq.write_table(table, self.output_dir / "species.parquet")
        elif self.output_format == ".arrow":
            table = create_dictionary_encoded_table(final_df)
            with (
                pa.OSFile(str(self.output_dir / "species.arrow"), "wb") as sink,
                pa.RecordBatchFileWriter(sink, table.schema) as writer,
            ):
                writer.write_table(table)
        else:  # Default to CSV
            final_df.to_csv(
                self.output_dir / "species.csv", index=False, lineterminator="\n"
            )

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
            shutil.rmtree(temp_dir, ignore_errors=True)


class FilterItem(TypedDict):
    code: str
    name: str


class GeographicFilter(TypedDict):
    excluded_fips: Sequence[FilterItem]


class ProcessingConfig(TypedDict):
    item_ids: list[str]
    output_format: FileExtension
    debug: bool
    geographic_filter: GeographicFilter


class Config(TypedDict):
    processing: ProcessingConfig


def is_file_extension(obj: Any) -> TypeIs[FileExtension]:
    return obj in {".csv", ".parquet", ".arrow"}


def read_config(fp: Path, /) -> Config:
    if not fp.exists():
        msg = f"Configuration file not found: {fp}"
        raise FileNotFoundError(msg)
    mapping = tomllib.loads(fp.read_text("utf-8"))
    if "processing" in mapping:
        return cast("Config", mapping)
    msg = "Missing [processing] table in TOML configuration."
    raise ValueError(msg)


def main() -> None:
    """Main entry point: loads TOML config, runs the processor."""
    config = read_config(CONFIG_FP)
    processing_config = config["processing"]
    output_format = processing_config.get("output_format", ".arrow")
    if item_ids := processing_config.get("item_ids", None):
        if not isinstance(item_ids, list):
            msg = "`item_ids` must be a non-empty list."
            raise TypeError(msg)
    else:
        msg = "Missing required configuration: item_ids must be specified in TOML file"
        raise ValueError(msg)

    logging.basicConfig(
        level=logging.DEBUG if processing_config.get("debug", False) else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger.info("Initializing GAP habitat analysis pipeline")
    processor = HabitatDataProcessor(
        item_ids, VECTOR_FP, OUTPUT_DIR, output_format, config=config
    )
    processor.run()


if __name__ == "__main__":
    main()
