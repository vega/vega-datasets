#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "niquests>=3.11.2",
# ]
# ///
"""
Generate gallery_examples.json from Vega ecosystem galleries.

This script collects example visualizations from three Vega ecosystem
repositories (Vega, Vega-Lite, and Altair) and generates a single JSON
file cataloging how datasets are used across these galleries.

Configuration can be customized via _data/gallery_examples.toml.
Command-line arguments override config file settings.

The script performs the following operations:

1. **Dataset Name Mapping**: Fetches datapackage.json from vega-datasets
   and builds a mapping from file paths to canonical dataset names.

2. **Gallery Collection**: Fetches example metadata from:
   - Vega-Lite: site/_data/examples.json
   - Vega: docs/_data/examples.json
   - Altair: Python test files from examples_methods_syntax and
     examples_arguments_syntax directories

3. **Dataset Extraction**: Fetches each example's specification and
   extracts dataset references:
   - Vega-Lite: Recursively searches for data.url in specs, layers,
     transforms, and concat/facet structures
   - Vega: Extracts from data array, handles signal-based URLs
   - Altair: Parses Python code for file paths and API calls

4. **Normalization**: Converts all dataset references to canonical
   names matching the datapackage.json resource names.

5. **Output Generation**: Writes a single JSON file with structure:
   {
     "created": "ISO-8601 timestamp",
     "examples": [
       {
         "id": int,
         "gallery_name": "vega" | "vega-lite" | "altair",
         "example_name": str,
         "example_url": str,
         "spec_url": str,
         "categories": list[str],
         "description": str | None,
         "datasets": list[str]
       }
     ]
   }

Usage
-----
    uv run scripts/generate_gallery_examples.py

Output
------
    gallery_examples.json : JSON file
        Single file containing all gallery examples with extracted
        dataset references.

Notes
-----
- The script uses niquests for HTTP requests with session pooling
- Examples are deduplicated across galleries
- Vega-Lite examples may appear in multiple categories
- Some examples use external datasets (preserved as-is)
- Expected runtime: 2-4 minutes depending on network speed

Examples
--------
To regenerate the gallery examples file:

    $ uv run scripts/generate_gallery_examples.py

See Also
--------
datapackage.json : Contains canonical dataset names and metadata
"""

from __future__ import annotations

import argparse
import json
import logging
import operator
import re
import time
import tomllib
from pathlib import Path
from typing import Any, Literal, NotRequired, Protocol, TypedDict, cast

import niquests as requests

# ============================================================================
# Constants
# ============================================================================

# Network timeout in seconds
DEFAULT_TIMEOUT = 30


# ============================================================================
# Type Aliases for Dataset References
# ============================================================================

# Current implementation uses string arrays for simplicity.
# This type alias provides a single point of change if we migrate
# to object arrays [{"name": "..."}] in the future.
#
# Migration path (when object structure becomes necessary):
# 1. Change: type DatasetReference = str
#    To:     class DatasetReference(TypedDict):
#                name: str
#                usage_type: NotRequired[Literal["primary", "secondary"]]
#
# 2. Update make_dataset_references() to return [{"name": n} for n in names]
#
# 3. Update GalleryExample.datasets to use list[DatasetReference]
#
# 4. Consumer code unchanged: [d if isinstance(d, str) else d["name"] for d in datasets]
#
type DatasetReference = str


# ============================================================================
# Semantic Type Aliases
# ============================================================================

type CanonicalName = str
"""Canonical dataset name from datapackage.json (e.g., 'cars', 'movies')."""

type FilePath = str
"""File path or URL to dataset (e.g., 'cars.json', 'data/cars.json')."""

type DatasetNameMap = dict[FilePath, CanonicalName]
"""Mapping from file paths/URLs to canonical dataset names."""

type ValidNames = set[CanonicalName]
"""Set of valid canonical dataset names from datapackage.json."""


# ============================================================================
# Configuration TypedDict Definitions
# ============================================================================


class AltairConfig(TypedDict):
    """
    Altair-specific configuration.

    Attributes
    ----------
    name_mapping : dict[str, str]
        Mapping from Altair API function names to canonical dataset names.
        Example: {"londonBoroughs": "london_boroughs"}
    """

    name_mapping: dict[str, str]


class SourcesConfig(TypedDict):
    """
    URLs for data sources.

    Attributes
    ----------
    datapackage_url : str
        URL to datapackage.json for dataset catalog.
    vega_lite_examples_url : str
        URL to Vega-Lite examples metadata JSON.
    vega_examples_url : str
        URL to Vega examples metadata JSON.
    altair_examples_dirs : list[str]
        List of GitHub raw URLs for Altair example directories.
    """

    datapackage_url: str
    vega_lite_examples_url: str
    vega_examples_url: str
    altair_examples_dirs: list[str]


class OutputConfig(TypedDict):
    """
    Output configuration.

    Attributes
    ----------
    default_output_path : str
        Default path for gallery_examples.json output.
    dry_run : bool
        If True, skip writing output file.
    """

    default_output_path: str
    dry_run: bool


class NetworkConfig(TypedDict):
    """
    Network request configuration.

    Attributes
    ----------
    timeout : int
        Request timeout in seconds.
    max_retries : int, optional
        Maximum number of retries for failed requests.
        Currently not used but reserved for future implementation.
    """

    timeout: int
    max_retries: NotRequired[int]


class GalleryConfig(TypedDict):
    """
    Complete configuration structure from gallery_examples.toml.

    Attributes
    ----------
    altair : AltairConfig
        Altair-specific settings.
    sources : SourcesConfig
        URLs for data sources.
    output : OutputConfig
        Output file settings.
    network : NetworkConfig
        Network request settings.
    """

    altair: AltairConfig
    sources: SourcesConfig
    output: OutputConfig
    network: NetworkConfig


# ============================================================================
# Type Definitions
# ============================================================================


class GalleryExample(TypedDict):
    """
    Final output format for a single gallery example.

    Attributes
    ----------
    id : int
        Unique sequential identifier for the example.
    gallery_name : Literal["vega", "vega-lite", "altair"]
        Name of the gallery this example belongs to.
    example_name : str
        Human-readable name or title of the example.
    example_url : str
        URL to the rendered example in the gallery.
    spec_url : str
        URL to the raw specification or code file.
    categories : list[str]
        Categories or tags associated with this example.
        Vega-Lite examples may have multiple categories.
    description : str | None
        Description of what the visualization demonstrates.
        May be None if not available in the source.
    datasets : list[str]
        List of dataset names referenced by this example.
        Names match the canonical 'name' field from datapackage.json.
        May be empty for examples with inline data.
    techniques : list[str]
        Auto-detected Vega/Vega-Lite/Altair features used in the example.
        Tags use category:subcategory format (e.g., "transform:window",
        "interaction:selection", "geo:projection").
        May be empty for simple examples with no notable features.
    """

    id: int
    gallery_name: Literal["vega", "vega-lite", "altair"]
    example_name: str
    example_url: str
    spec_url: str
    categories: list[str]
    description: str | None
    datasets: list[str]
    techniques: list[str]


class IntermediateExample(TypedDict):
    """
    Intermediate format during collection and enrichment.

    This structure is used while building the examples list before
    final ID assignment and output formatting.

    Attributes
    ----------
    gallery_name : str
        Gallery identifier.
    example_name : str
        Example title or name.
    example_url : str
        URL to rendered example.
    spec_url : str
        URL to specification source.
    categories : list[str]
        List of category names.
    description : str | None
        Example description if available.
    datasets : list[str]
        Dataset names (populated during enrichment phase).
    techniques : NotRequired[list[str]]
        Auto-detected techniques (populated during enrichment phase).
    """

    gallery_name: str
    example_name: str
    example_url: str
    spec_url: str
    categories: list[str]
    description: str | None
    datasets: list[str]
    techniques: NotRequired[list[str]]


# ============================================================================
# Validation Infrastructure
# ============================================================================


class DatasetValidator(Protocol):
    """
    Protocol for validating dataset references.

    This protocol allows multiple validation strategies while maintaining
    type safety. Useful for testing with mock validators or adding
    enhanced validation in the future.
    """

    def validate_name(self, name: str) -> str:
        """
        Validate a dataset name.

        Parameters
        ----------
        name : str
            Dataset name to validate.

        Returns
        -------
        str
            The validated name (same as input).

        Raises
        ------
        ValueError
            If name is not valid.
        """
        ...

    def validate_all(self, names: list[str]) -> list[str]:
        """
        Validate a list of dataset names.

        Parameters
        ----------
        names : list[str]
            Dataset names to validate.

        Returns
        -------
        list[str]
            The validated names (same as input).

        Raises
        ------
        ValueError
            If any name is invalid.
        """
        ...


class SimpleDatasetValidator:
    """
    Basic validator for dataset names against datapackage.json.

    Validates that dataset names exist in the canonical vega-datasets
    catalog and logs warnings for unknown references.
    """

    def __init__(self, valid_names: ValidNames) -> None:
        """
        Initialize validator with valid dataset names.

        Parameters
        ----------
        valid_names : ValidNames
            Set of canonical dataset names from datapackage.json.
        """
        self._valid_names = valid_names

    def validate_name(self, name: str) -> str:
        """
        Validate a single dataset name.

        Parameters
        ----------
        name : str
            Dataset name to validate.

        Returns
        -------
        str
            The validated name (same as input).

        Raises
        ------
        ValueError
            If name is not in valid_names.

        Examples
        --------
        >>> validator = SimpleDatasetValidator({"cars", "movies"})
        >>> validator.validate_name("cars")
        'cars'
        >>> validator.validate_name("unknown")
        ValueError: Unknown dataset: unknown. Valid datasets: ['cars', 'movies']
        """
        if not isinstance(name, str):
            msg = f"Dataset name must be str, got {type(name).__name__}"
            raise TypeError(msg)

        if name not in self._valid_names:
            msg = (
                f"Unknown dataset: {name}. Valid datasets: {sorted(self._valid_names)}"
            )
            raise ValueError(msg)

        return name

    def validate_all(self, names: list[str]) -> list[str]:
        """
        Validate all dataset names in a list.

        Parameters
        ----------
        names : list[str]
            Dataset names to validate.

        Returns
        -------
        list[str]
            The validated names (same as input if all valid).

        Raises
        ------
        ValueError
            If any name is invalid. Error message includes index.
        """
        for i, name in enumerate(names):
            try:
                self.validate_name(name)
            except (ValueError, TypeError) as e:
                # Include index in error for debugging
                msg = f"Invalid dataset at index {i}: {e}"
                raise ValueError(msg) from e
        return names


def is_valid_dataset_name(name: str, valid_names: ValidNames) -> bool:
    """
    Type guard to check if a name is a valid dataset reference.

    Parameters
    ----------
    name : str
        Name to check.
    valid_names : set[str]
        Set of valid dataset names.

    Returns
    -------
    bool
        True if name is in valid_names and is a string.

    Examples
    --------
    >>> is_valid_dataset_name("cars", {"cars", "movies"})
    True
    >>> is_valid_dataset_name("unknown", {"cars", "movies"})
    False
    >>> is_valid_dataset_name(123, {"cars"})
    False
    """
    return isinstance(name, str) and name in valid_names


def make_dataset_references(names: list[str]) -> list[DatasetReference]:
    """
    Convert dataset names to DatasetReference format.

    Currently returns string array for simplicity. This helper provides
    a single point of change if we migrate to object array structure
    [{"name": "..."}] in the future.

    Parameters
    ----------
    names : list[str]
        List of dataset names (may contain duplicates).

    Returns
    -------
    list[DatasetReference]
        Dataset references with duplicates removed, order preserved.

    Examples
    --------
    >>> make_dataset_references(["cars", "movies", "cars"])
    ['cars', 'movies']

    Future Enhancement Example
    --------------------------
    When migrating to object structure:

    >>> # DatasetReference becomes TypedDict instead of type alias
    >>> class DatasetReference(TypedDict):
    ...     name: str
    ...     usage_type: NotRequired[Literal["primary", "secondary"]]

    >>> def make_dataset_references(names: list[str]) -> list[DatasetReference]:
    ...     return [{"name": name} for name in dict.fromkeys(names)]

    >>> make_dataset_references(["cars", "movies"])
    [{'name': 'cars'}, {'name': 'movies'}]
    """
    # Remove duplicates while preserving order
    return list(dict.fromkeys(names))


class GalleryExamplesOutput(TypedDict):
    """
    Complete output structure for gallery_examples.json.

    .. deprecated:: 2.0.0
        This wrapper format is deprecated. As of Data Package v2 compliance,
        gallery_examples.json now contains only the examples array (data-only).
        Metadata (name, title, description, version, created, datapackage)
        is stored in datapackage.json as a resource entry.

    Attributes
    ----------
    name : str
        Machine-readable identifier for this file.
    title : str
        Human-readable title.
    description : str
        Explanation of purpose and relationship to vega-datasets.
    version : str
        Semantic version of this registry format.
    created : str
        ISO-8601 timestamp of generation.
    datapackage : dict[str, str]
        Cross-reference to datapackage.json with version.
    examples : list[GalleryExample]
        Array of gallery example records.
    """

    name: str
    title: str
    description: str
    version: str
    created: str
    datapackage: dict[str, str]
    examples: list[GalleryExample]


# ============================================================================
# Logging Configuration
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration Loading
# ============================================================================


def load_config() -> GalleryConfig:
    """
    Load configuration from _data/gallery_examples.toml file.

    Loads the TOML configuration file from the repository root directory.
    The configuration file is optional - if not found or if there are
    errors reading it, the function returns a default configuration with
    hardcoded fallback values.

    Returns
    -------
    dict[str, Any]
        Configuration dictionary with the following structure:
        {
            'altair': {
                'name_mapping': dict[str, str]  # Altair API name → canonical name
            },
            'sources': {
                'datapackage_url': str,
                'vega_lite_examples_url': str,
                'vega_examples_url': str,
                'altair_examples_dirs': list[str]
            },
            'output': {
                'default_output_path': str,
                'dry_run': bool
            },
            'network': {
                'timeout': int,
                'max_retries': int
            }
        }

    Examples
    --------
    >>> config = load_config()
    >>> config["sources"]["datapackage_url"]
    'https://raw.githubusercontent.com/vega/vega-datasets/main/datapackage.json'
    >>> config["altair"]["name_mapping"].get("londonBoroughs")
    'london_boroughs'

    Notes
    -----
    - Configuration file path is determined relative to this script's location
    - If _data/gallery_examples.toml is not found, default values are used
    - Any errors during loading are logged but don't crash the script
    - Default configuration matches the original hardcoded values
    - Command-line arguments should override these configuration values
    """
    # Default configuration (fallback values)

    repo_root = Path(__file__).parent.parent
    config_path = repo_root / "_data" / "gallery_examples.toml"

    if not config_path.exists():
        logger.error(
            "Configuration file not found: %s\n"
            "This script requires `_data/gallery_examples.toml`. "
            "If you're running this locally, copy the provided example or "
            "create the file with the required sections (altair, sources, output, network).",
            config_path,
        )
        msg = (
            f"Required config file missing: {config_path}. "
            "Create `_data/gallery_examples.toml` or run with a --dry-run flag."
        )
        raise FileNotFoundError(msg)

    try:
        with Path(config_path).open("rb") as f:
            config = tomllib.load(f)
        logger.info("Loaded configuration from %s", config_path)
    except Exception:
        logger.exception("Error loading configuration from %s", config_path)
        raise
    else:
        return cast("GalleryConfig", config)


# ============================================================================
# Dataset Name Mapping Functions
# ============================================================================


def fetch_datapackage(
    session: requests.Session, url: str, timeout: int = DEFAULT_TIMEOUT
) -> dict[str, Any]:
    """
    Fetch datapackage.json from vega-datasets repository.

    Retrieves the canonical dataset metadata file from the main branch
    of the vega-datasets GitHub repository.

    Parameters
    ----------
    session : requests.Session
        HTTP session for connection pooling.
    url : str
        URL to the datapackage.json file.
    timeout : int, default DEFAULT_TIMEOUT
        Timeout in seconds for the HTTP request.

    Returns
    -------
    dict[str, Any]
        Parsed datapackage.json content containing dataset metadata.
        The structure includes a 'resources' key with a list of
        dataset definitions, each having 'name' and 'path' fields.

    Raises
    ------
    requests.HTTPError
        If the fetch fails due to network issues or invalid response.
    requests.Timeout
        If the request exceeds the timeout period.

    Examples
    --------
    >>> session = requests.Session()
    >>> url = (
    ...     "https://raw.githubusercontent.com/vega/vega-datasets/main/datapackage.json"
    ... )
    >>> datapackage = fetch_datapackage(session, url)
    >>> len(datapackage["resources"])
    73
    """
    logger.info("Fetching %s", url)
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def build_dataset_name_map(datapackage: dict[str, Any]) -> DatasetNameMap:
    """
    Build mapping from file paths to canonical dataset names.

    Creates multiple variations for lookup to handle different ways
    datasets are referenced in specifications:
    - Full path: "annual-precip.json" → "annual_precip"
    - With data prefix: "data/annual-precip.json" → "annual_precip"
    - Just filename: "cars.json" → "cars"

    This normalization ensures consistent dataset identification across
    all three gallery types (Vega, Vega-Lite, Altair).

    Parameters
    ----------
    datapackage : dict[str, Any]
        Parsed datapackage.json containing resource definitions.

    Returns
    -------
    dict[str, str]
        Map from file path variations to canonical dataset names.
        Keys include the original path, the path with 'data/' prefix,
        and the filename alone.

    Examples
    --------
    >>> datapackage = {
    ...     "resources": [
    ...         {"name": "cars", "path": "cars.json"},
    ...         {"name": "annual_precip", "path": "annual-precip.json"},
    ...     ]
    ... }
    >>> name_map = build_dataset_name_map(datapackage)
    >>> name_map["cars.json"]
    'cars'
    >>> name_map["data/cars.json"]
    'cars'
    >>> name_map["annual-precip.json"]
    'annual_precip'
    """
    name_map = {}

    for resource in datapackage.get("resources", []):
        canonical_name = resource.get("name")
        path = resource.get("path")

        if not canonical_name or not path:
            continue

        # Map: full path → name
        name_map[path] = canonical_name

        # Map: data/path → name
        if not path.startswith("data/"):
            name_map[f"data/{path}"] = canonical_name

        # Map: filename → name
        filename = path.split("/")[-1]
        name_map[filename] = canonical_name

    return name_map


def normalize_dataset_reference(
    ref: FilePath, name_map: DatasetNameMap
) -> CanonicalName:
    """
    Normalize a dataset reference to canonical name.

    Attempts to map a raw dataset reference (as found in a visualization
    specification) to the canonical dataset name from datapackage.json.
    If the reference is not found in vega-datasets, it is returned as-is
    (this handles external datasets).

    Parameters
    ----------
    ref : str
        Raw reference from spec (e.g., "data/cars.json", "cars.json").
    name_map : dict[str, str]
        Map from paths to canonical names built by
        build_dataset_name_map().

    Returns
    -------
    str
        Canonical dataset name (e.g., "cars") if found in vega-datasets,
        or the original reference if not found.

    Examples
    --------
    >>> name_map = {"cars.json": "cars", "data/cars.json": "cars"}
    >>> normalize_dataset_reference("data/cars.json", name_map)
    'cars'
    >>> normalize_dataset_reference("cars.json", name_map)
    'cars'
    >>> normalize_dataset_reference("external.json", name_map)
    'external.json'
    """
    # Try exact match
    if ref in name_map:
        return name_map[ref]

    # Try just filename
    filename = ref.rsplit("/", maxsplit=1)[-1]
    if filename in name_map:
        return name_map[filename]

    # Not a vega-dataset, return as-is
    logger.debug("Dataset reference not in vega-datasets: %s", ref)
    return ref


# ============================================================================
# Gallery Collection Functions
# ============================================================================


def collect_vega_lite_examples(
    session: requests.Session, url: str, timeout: int = DEFAULT_TIMEOUT
) -> list[dict[str, Any]]:
    """
    Collect examples from Vega-Lite gallery.

    Fetches example metadata from the Vega-Lite gallery and builds a list
    of IntermediateExample dictionaries. Examples may appear in multiple
    categories and are deduplicated by name. Categories are stored as a
    list of strings.

    Parameters
    ----------
    session : requests.Session
        HTTP session for connection pooling.
    url : str
        URL to the Vega-Lite examples.json metadata file.
    timeout : int, default DEFAULT_TIMEOUT
        Timeout in seconds for the HTTP request.

    Returns
    -------
    list[dict[str, Any]]
        List of IntermediateExample dictionaries. The datasets field
        is initialized as an empty list and will be populated in Phase 4.
        Expected count: ~190 unique examples.

    Raises
    ------
    requests.HTTPError
        If the fetch fails due to network issues or invalid response.
    requests.Timeout
        If the request exceeds the timeout period.

    Examples
    --------
    >>> session = requests.Session()
    >>> url = "https://raw.githubusercontent.com/vega/vega-lite/main/site/_data/examples.json"
    >>> examples = collect_vega_lite_examples(session, url)
    >>> len(examples)
    190
    >>> examples[0]["gallery_name"]
    'vega-lite'
    >>> isinstance(examples[0]["categories"], list)
    True

    Notes
    -----
    - Examples appearing in multiple categories have all categories stored
      in the categories list
    - Full category names are built as "{category} - {subcategory}"
    - Example names use the 'title' field if available, falling back to 'name'
    """
    logger.info("Collecting Vega-Lite examples from %s", url)

    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    examples_data = response.json()

    # Dictionary to deduplicate examples across categories
    example_dict = {}

    for category_name, subcategories in examples_data.items():
        for subcategory_name, example_list in subcategories.items():
            # Build full category name
            full_category = (
                f"{category_name} - {subcategory_name}"
                if subcategory_name
                else category_name
            )

            for example in example_list:
                example_name = example.get("title", example["name"])

                # Deduplicate by name
                if example_name in example_dict:
                    example_dict[example_name]["categories"].append(full_category)
                else:
                    example_url = f"https://vega.github.io/vega-lite/examples/{example['name']}.html"
                    spec_url = f"https://raw.githubusercontent.com/vega/vega-lite/main/examples/specs/{example['name']}.vl.json"

                    example_dict[example_name] = {
                        "gallery_name": "vega-lite",
                        "example_name": example_name,
                        "example_url": example_url,
                        "spec_url": spec_url,
                        "categories": [full_category],
                        "description": example.get("description"),
                        "datasets": [],  # Will be filled later
                        "techniques": [],  # Will be filled later
                    }

    logger.info("  Found %s unique Vega-Lite examples", len(example_dict))
    return list(example_dict.values())


def collect_vega_examples(
    session: requests.Session, url: str, timeout: int = DEFAULT_TIMEOUT
) -> list[dict[str, Any]]:
    """
    Collect examples from Vega gallery.

    Fetches example metadata from the Vega gallery and builds a list
    of IntermediateExample dictionaries. Each example has a single
    category. Example names are converted to title case with spaces.

    Parameters
    ----------
    session : requests.Session
        HTTP session for connection pooling.
    url : str
        URL to the Vega examples.json metadata file.
    timeout : int, default DEFAULT_TIMEOUT
        Timeout in seconds for the HTTP request.

    Returns
    -------
    list[dict[str, Any]]
        List of IntermediateExample dictionaries. The datasets field
        is initialized as an empty list and will be populated in Phase 4.
        Expected count: ~93 examples.

    Raises
    ------
    requests.HTTPError
        If the fetch fails due to network issues or invalid response.
    requests.Timeout
        If the request exceeds the timeout period.

    Examples
    --------
    >>> session = requests.Session()
    >>> url = (
    ...     "https://raw.githubusercontent.com/vega/vega/main/docs/_data/examples.json"
    ... )
    >>> examples = collect_vega_examples(session, url)
    >>> len(examples)
    93
    >>> examples[0]["gallery_name"]
    'vega'
    >>> len(examples[0]["categories"])
    1

    Notes
    -----
    - Example names are converted from 'example-name' to 'Example Name'
    - Each example belongs to exactly one category
    - Descriptions are not available in the source and set to None
    """
    logger.info("Collecting Vega examples from %s", url)

    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    examples_data = response.json()

    examples = []

    for category_name, example_list in examples_data.items():
        for example in example_list:
            example_name = example["name"].replace("-", " ").title()
            example_url = f"https://vega.github.io/vega/examples/{example['name']}/"
            spec_url = f"https://raw.githubusercontent.com/vega/vega/main/docs/examples/{example['name']}.vg.json"

            examples.append({
                "gallery_name": "vega",
                "example_name": example_name,
                "example_url": example_url,
                "spec_url": spec_url,
                "categories": [category_name],
                "description": None,  # Will be extracted from spec
                "datasets": [],
                "techniques": [],  # Will be filled later
            })

    logger.info("  Found %s Vega examples", len(examples))
    return examples


def extract_altair_title(session: requests.Session, file_url: str) -> str | None:
    r"""
    Extract title from Altair example docstring.

    Altair examples use a docstring pattern with title and underline:
        \"\"\"Title
        ======
        \"\"\"

    This function attempts to extract the title from this pattern.

    Parameters
    ----------
    session : requests.Session
        HTTP session for connection pooling.
    file_url : str
        URL to the raw Python file.

    Returns
    -------
    str | None
        Extracted title if found, None otherwise.

    Examples
    --------
    >>> session = requests.Session()
    >>> url = "https://raw.githubusercontent.com/vega/altair/main/tests/examples_methods_syntax/bar_chart.py"
    >>> title = extract_altair_title(session, url)
    >>> title
    'Simple Bar Chart'

    Notes
    -----
    - Returns None if the file cannot be fetched or the pattern is not found
    - Uses regex pattern: ^\"\"\"?\\s*\\n?(.*?)\\n[-=]+\\s*\\n
    - Handles both triple-quote variants (''' and \"\"\")
    """
    try:
        response = session.get(file_url, timeout=DEFAULT_TIMEOUT)
        if response.status_code != 200:
            return None

        content = response.text
        assert isinstance(content, str)  # response.text is always str in requests
        pattern = r'^"""?\s*\n?(.*?)\n[-=]+\s*\n'
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            return match.group(1).strip()
    except Exception as e:
        logger.debug("Error extracting title from %s: %s", file_url, e)

    return None


def collect_altair_examples(
    session: requests.Session,
    directories: list[str],
    timeout: int = DEFAULT_TIMEOUT,
) -> list[dict[str, Any]]:
    """
    Collect examples from Altair gallery.

    Fetches example files from Altair test directories (methods syntax
    and arguments syntax) and builds a list of IntermediateExample
    dictionaries. Files are deduplicated by filename across directories.
    Titles are extracted from docstrings when available.

    Parameters
    ----------
    session : requests.Session
        HTTP session for connection pooling.
    directories : list[str]
        List of Altair example directory paths to scan.
    timeout : int, default DEFAULT_TIMEOUT
        Timeout in seconds for HTTP requests.

    Returns
    -------
    list[dict[str, Any]]
        List of IntermediateExample dictionaries. The datasets field
        is initialized as an empty list and will be populated in Phase 4.
        Expected count: ~185 examples.

    Raises
    ------
    requests.HTTPError
        If the fetch fails due to network issues or invalid response.
    requests.Timeout
        If the request exceeds the timeout period.

    Examples
    --------
    >>> session = requests.Session()
    >>> dirs = ["tests/examples_methods_syntax", "tests/examples_arguments_syntax"]
    >>> examples = collect_altair_examples(session, dirs)
    >>> len(examples)
    185
    >>> examples[0]["gallery_name"]
    'altair'

    Notes
    -----
    - Examples are collected from all specified directories
    - Deduplication is done by filename (if same file exists in multiple dirs,
      it's only included once)
    - Titles are extracted from docstrings using extract_altair_title()
    - Falls back to filename-based titles if docstring extraction fails
    - Categories are initialized as empty list (will be extracted in Phase 4)
    """
    logger.info("Collecting Altair examples")

    examples = []
    seen_files = set()

    for directory in directories:
        api_url = f"https://api.github.com/repos/vega/altair/contents/{directory}"
        response = session.get(api_url, timeout=timeout)
        response.raise_for_status()
        files = response.json()

        for file in files:
            if not file["name"].endswith(".py") or file["name"].startswith("__"):
                continue

            # Deduplicate
            if file["name"] in seen_files:
                continue
            seen_files.add(file["name"])

            spec_url = f"https://raw.githubusercontent.com/vega/altair/main/{directory}/{file['name']}"

            # Try to extract title from docstring
            example_name = extract_altair_title(session, spec_url)
            if not example_name:
                # Fallback to filename
                example_name = file["name"].replace(".py", "").replace("_", " ").title()

            example_url = f"https://altair-viz.github.io/gallery/{file['name'].replace('.py', '.html')}"

            examples.append({
                "gallery_name": "altair",
                "example_name": example_name,
                "example_url": example_url,
                "spec_url": spec_url,
                "categories": [],  # Will be extracted from code
                "description": None,  # Will be extracted from code
                "datasets": [],
                "techniques": [],  # Will be filled later
            })

    logger.info("  Found %s Altair examples", len(examples))
    return examples


# ============================================================================
# Dataset Extraction Functions
# ============================================================================

# OPTIMIZATION OPPORTUNITIES (Task 4.5):
#
# Following the "make it work, make it right, make it fast" principle,
# these functions prioritize correctness and clarity. Post-implementation
# optimization review identified these potential improvements:
#
# 1. Vega-Lite Recursive Extraction:
#    - Current: Multiple recursive calls for layers/concat/facet
#    - Consideration: Could use iterative approach with stack/queue
#    - Trade-off: Recursion is clearer and handles arbitrary nesting
#    - Decision: Keep recursive for maintainability at ~468 examples scale
#
# 2. Vega Signal Extraction:
#    - Current: Linear search through signals array
#    - Consideration: Could build signal index dict if multiple lookups
#    - Trade-off: Signal-based URLs are rare (~few examples)
#    - Decision: Linear search is sufficient for current use case
#
# 3. Altair Regex Patterns:
#    - Current: 5 separate patterns compiled on each call
#    - Consideration: Could pre-compile regex patterns as module constants
#    - Impact: ~185 Altair examples * 5 patterns = ~925 compilations
#    - Decision: Worth optimizing - see ALTAIR_API_PATTERNS below
#
# 4. Code Duplication:
#    - Current: Three Altair approach functions have identical pattern extraction
#    - Consideration: Could factor out common pattern extraction logic
#    - Trade-off: Current separation makes each approach self-contained
#    - Decision: Keep separate for clarity and ease of comparison
#
# 5. Network Performance:
#    - Current: Sequential HTTP requests for ~468 examples
#    - Consideration: Could use async/await for concurrent fetching
#    - Impact: Could reduce total runtime from ~3-4 minutes to ~1 minute
#    - Decision: Out of scope for Phase 4, consider for Phase 6
#
# Conclusion: At current scale (~468 examples), extreme optimization is not
# necessary. Focus remains on correctness and maintainability. If collection
# grows to thousands of examples, revisit items 1, 3, and 5.


def extract_signal_values(spec: dict[str, Any], signal_name: str) -> list[str]:
    """
    Extract possible values from a signal definition in Vega spec.

    Signals in Vega can define dynamic values through bind inputs with
    options. This function extracts those option values and default values
    to determine which datasets might be loaded through signal-based URLs.

    Parameters
    ----------
    spec : dict[str, Any]
        Vega specification containing signal definitions.
    signal_name : str
        Name of the signal to extract values from.

    Returns
    -------
    list[str]
        List of possible string values the signal can take.
        Empty list if signal not found or has no extractable values.

    Examples
    --------
    >>> spec = {
    ...     "signals": [
    ...         {
    ...             "name": "dataset",
    ...             "value": "data/cars.json",
    ...             "bind": {
    ...                 "input": "select",
    ...                 "options": ["data/cars.json", "data/movies.json"],
    ...             },
    ...         }
    ...     ]
    ... }
    >>> extract_signal_values(spec, "dataset")
    ['data/cars.json', 'data/movies.json']

    Notes
    -----
    - Looks for signals with bind.options (select inputs)
    - Also includes the default value if present
    - Only extracts string values (ignores non-string defaults)
    """
    values = []

    if "signals" not in spec:
        return values

    for signal in spec["signals"]:
        if signal.get("name") == signal_name:
            # Check for select input with options
            # This is the primary source for signal-based dataset switching
            if "bind" in signal and "options" in signal.get("bind", {}):
                values.extend(signal["bind"]["options"])

            # Check the default value if present
            # This catches the initial dataset loaded
            if "value" in signal and isinstance(signal["value"], str):
                values.append(signal["value"])

            break

    return values


def extract_datasets_from_vega_spec(
    spec: dict[str, Any], name_map: DatasetNameMap
) -> list[CanonicalName]:
    """
    Extract dataset references from Vega specification.

    Vega specifications organize data in an array with each data source
    having a name and optional URL. This function extracts all external
    data sources, handling both static URLs and signal-based dynamic URLs.

    Parameters
    ----------
    spec : dict[str, Any]
        Vega specification (must contain 'data' array).
    name_map : dict[str, str]
        Map from file paths to canonical dataset names.

    Returns
    -------
    list[str]
        List of normalized dataset names.
        May contain duplicates if same dataset referenced multiple times.

    Examples
    --------
    >>> spec = {
    ...     "data": [
    ...         {"name": "source", "url": "data/cars.json"},
    ...         {
    ...             "name": "lookup",
    ...             "transform": [
    ...                 {
    ...                     "type": "lookup",
    ...                     "from": {"data": {"url": "data/movies.json"}},
    ...                 }
    ...             ],
    ...         },
    ...     ]
    ... }
    >>> name_map = {"data/cars.json": "cars", "data/movies.json": "movies"}
    >>> extract_datasets_from_vega_spec(spec, name_map)
    ['cars', 'movies']

    Notes
    -----
    - Returns empty list if spec has no data array
    - Handles direct URL strings
    - Handles signal-based URLs by extracting all possible signal values
    - Extracts from lookup transforms within data items
    - Does not extract from inline data values
    """
    datasets = []

    # Vega specs must have a data array
    if "data" not in spec or not isinstance(spec["data"], list):
        return datasets

    for data_item in spec["data"]:
        if not isinstance(data_item, dict):
            continue

        # Extract from direct URL field
        if "url" in data_item:
            url_value = data_item["url"]

            # Handle signal-based URLs (dynamic dataset selection)
            # Example: {"signal": "dataset_url"} where signal has multiple options
            if isinstance(url_value, dict) and "signal" in url_value:
                signal_name = url_value["signal"]
                signal_values = extract_signal_values(spec, signal_name)
                for value in signal_values:
                    normalized = normalize_dataset_reference(value, name_map)
                    datasets.append(normalized)
            elif isinstance(url_value, str):
                # Normal string URL
                normalized = normalize_dataset_reference(url_value, name_map)
                datasets.append(normalized)

        # Extract from transforms within data items
        # Vega allows transforms to be nested inside data definitions
        if "transform" in data_item and isinstance(data_item["transform"], list):
            for transform in data_item["transform"]:
                if isinstance(transform, dict) and transform.get("type") == "lookup":
                    # Lookup transforms can reference external data
                    if "from" in transform:
                        from_data = transform["from"]
                        if isinstance(from_data, dict) and "data" in from_data:
                            # Check if the 'data' field has a URL
                            if (
                                isinstance(from_data["data"], dict)
                                and "url" in from_data["data"]
                            ):
                                normalized = normalize_dataset_reference(
                                    from_data["data"]["url"], name_map
                                )
                                datasets.append(normalized)

    return datasets


def extract_datasets_from_vegalite_spec(
    spec: dict[str, Any], name_map: DatasetNameMap
) -> list[CanonicalName]:
    """
    Extract dataset references from Vega-Lite specification.

    Vega-Lite has a more implicit structure where data can appear at
    multiple levels: top-level, in layers, in concat/facet views, and
    in transform lookups. This function recursively searches all these
    locations to find all dataset references.

    Parameters
    ----------
    spec : dict[str, Any]
        Vega-Lite specification (can be a view or sub-view).
    name_map : dict[str, str]
        Map from file paths to canonical dataset names.

    Returns
    -------
    list[str]
        List of normalized dataset names.
        May contain duplicates if same dataset referenced multiple times
        across different views or layers.

    Examples
    --------
    >>> spec = {
    ...     "data": {"url": "data/cars.json"},
    ...     "layer": [
    ...         {"mark": "point"},
    ...         {"data": {"url": "data/movies.json"}, "mark": "rule"},
    ...     ],
    ... }
    >>> name_map = {"data/cars.json": "cars", "data/movies.json": "movies"}
    >>> extract_datasets_from_vegalite_spec(spec, name_map)
    ['cars', 'movies']

    Notes
    -----
    - Recursively processes nested structures (layers, concat, facet)
    - Top-level data is inherited by layers unless overridden
    - Transform lookups can introduce additional datasets
    - Returns all datasets found, duplicates included (caller can dedupe)
    - Only extracts from URL-based data sources (not inline data)
    """
    datasets = []

    # Top-level data.url extraction
    # This is the most common case for simple specs
    if "data" in spec and isinstance(spec["data"], dict) and "url" in spec["data"]:
        normalized = normalize_dataset_reference(spec["data"]["url"], name_map)
        datasets.append(normalized)

    # Transform lookups
    # Lookup transforms reference external datasets for joins
    if "transform" in spec and isinstance(spec["transform"], list):
        for transform in spec["transform"]:
            if isinstance(transform, dict) and "lookup" in transform:
                # Lookup structure: {lookup: field, from: {data: {url: ...}}}
                if "from" in transform and isinstance(transform["from"], dict):
                    if (
                        "data" in transform["from"]
                        and isinstance(transform["from"]["data"], dict)
                        and "url" in transform["from"]["data"]
                    ):
                        normalized = normalize_dataset_reference(
                            transform["from"]["data"]["url"], name_map
                        )
                        datasets.append(normalized)

    # Layers (recursive)
    # Each layer can override data or inherit from parent
    if "layer" in spec and isinstance(spec["layer"], list):
        for layer in spec["layer"]:
            if isinstance(layer, dict):
                # Check for layer-specific data override
                if "data" in layer and isinstance(layer["data"], dict):
                    if "url" in layer["data"]:
                        normalized = normalize_dataset_reference(
                            layer["data"]["url"], name_map
                        )
                        datasets.append(normalized)

                # Recursively extract from the layer itself
                # This handles nested layers and transforms within layers
                layer_datasets = extract_datasets_from_vegalite_spec(layer, name_map)
                datasets.extend(layer_datasets)

    # Concat specs (recursive)
    # Concatenation combines multiple independent views
    for concat_type in ["concat", "hconcat", "vconcat"]:
        if concat_type in spec and isinstance(spec[concat_type], list):
            for sub_spec in spec[concat_type]:
                if isinstance(sub_spec, dict):
                    sub_datasets = extract_datasets_from_vegalite_spec(
                        sub_spec, name_map
                    )
                    datasets.extend(sub_datasets)

    # Facet/repeat specs (recursive)
    # Faceting and repeat wrap a sub-specification
    if "spec" in spec and isinstance(spec["spec"], dict):
        sub_datasets = extract_datasets_from_vegalite_spec(spec["spec"], name_map)
        datasets.extend(sub_datasets)

    return datasets


# ============================================================================
# Altair Dataset Extraction Functions
# ============================================================================


def extract_altair_api_datasets(
    code: str,
    valid_names: ValidNames,
    name_mapping: dict[str, str] | None = None,
) -> list[CanonicalName]:
    """
    Extract Altair API dataset names using optional name mapping.

    LEGACY SUPPORT: Altair v6+ (PR #3859, merged Oct 2025) uses canonical
    vega-datasets names directly, making name mapping unnecessary when tracking
    Altair main branch. This function supports name mapping for backward
    compatibility with Altair v5.x releases.

    Historical context:
    - Altair v5.x used camelCase API names (e.g., data.londonBoroughs.url)
    - vega-datasets canonical names use snake_case (e.g., london_boroughs)
    - Name mapping bridged this gap
    - Altair v6+ adopted canonical names, eliminating the need for mapping

    Current behavior (Altair v6+, with name_mapping=None):
    - Extracts dataset names from Altair code patterns
    - Validates directly against vega-datasets canonical names
    - Logs warnings for external datasets (expected for some examples)
    - No name transformation occurs

    Parameters
    ----------
    code : str
        Altair Python source code.
    valid_names : set[str]
        Valid dataset names from datapackage.json.
    name_mapping : dict[str, str] | None, default None
        Optional mapping from Altair API names to canonical names.
        - For Altair v6+: Pass None or {} (canonical names used directly)
        - For Altair v5: Pass mapping like {"londonBoroughs": "london_boroughs"}
        Typically loaded from _data/gallery_examples.toml under [altair.name_mapping].

    Returns
    -------
    list[str]
        List of validated dataset names (canonical names from vega-datasets).

    Examples
    --------
    Altair v6+ (no mapping needed):

    >>> code = "data.london_boroughs.url"
    >>> valid_names = {"london_boroughs"}
    >>> extract_altair_api_datasets(code, valid_names)
    ['london_boroughs']

    Altair v5 (with mapping):

    >>> code = "data.londonBoroughs.url"
    >>> valid_names = {"london_boroughs"}
    >>> mapping = {"londonBoroughs": "london_boroughs"}
    >>> extract_altair_api_datasets(code, valid_names, name_mapping=mapping)
    ['london_boroughs']
    # Logs: DEBUG - Altair mapping applied: londonBoroughs → london_boroughs

    External dataset (not in vega-datasets):

    >>> code = "data.unknown_dataset()"
    >>> extract_altair_api_datasets(code, valid_names)
    []
    # Logs: WARNING - External Altair dataset (not in vega-datasets): unknown_dataset

    Notes
    -----
    - External datasets (not in vega-datasets) log warnings but are skipped
    - This approach was selected after comparative testing showed best accuracy
      and performance (see ALTAIR_APPROACH_COMPARISON_RESULTS.md)
    - Patterns may overlap (e.g., alt.UrlData(data.cars.url) matches multiple patterns)
      but deduplication via set() ensures each name appears once
    """
    # Use provided mapping or empty dict
    if name_mapping is None:
        name_mapping = {}

    datasets = []

    # Regex patterns for different Altair dataset reference styles
    patterns = [
        r"data\.(\w+)\s*\(",  # data.cars()
        r"data\.(\w+)\.url",  # data.cars.url
        r"alt\.topo_feature\s*\(\s*data\.(\w+)\.url",  # alt.topo_feature(data.cars.url
        r"vega_datasets\.data\.(\w+)\.url",  # Legacy: from vega_datasets import data
        r"altair\.datasets\.data\.(\w+)\.url",  # Altair v6: import altair (fully qualified)
        r"alt\.UrlData\s*\(\s*data\.(\w+)\.url",  # alt.UrlData(data.cars.url
    ]

    # Extract dataset names from all patterns
    # Note: Patterns may overlap (e.g., alt.UrlData(data.cars.url) matches patterns 2 and 6)
    # Deduplication via set() ensures each name appears once
    extracted_names = set()
    for pattern in patterns:
        matches = re.findall(pattern, code)
        extracted_names.update(matches)

    for name in extracted_names:
        # Apply explicit mapping if exists
        canonical_name = name_mapping.get(name, name)

        if canonical_name in valid_names:
            datasets.append(canonical_name)
            # Log debug message if mapping was applied
            if canonical_name != name:
                logger.debug("Altair mapping applied: %s → %s", name, canonical_name)
        else:
            # External dataset (not in vega-datasets) - informational warning
            logger.warning("External Altair dataset (not in vega-datasets): %s", name)
            # Skip the dataset - it's expected that some examples use external data

    return datasets


def extract_datasets_from_altair_code(
    code: str,
    name_map: DatasetNameMap,
    valid_names: ValidNames,
    config: GalleryConfig,
) -> list[CanonicalName]:
    """
    Extract dataset references from Altair Python code.

    Altair examples can reference datasets in two ways:
    1. File paths: "data/cars.json" or pd.read_csv("data/...")
    2. Python API: data.cars(), data.cars.url, etc.

    This function handles both patterns, using explicit mappings from
    _data/gallery_examples.toml for API name validation.

    Parameters
    ----------
    code : str
        Altair Python source code.
    name_map : dict[str, str]
        Map from file paths to canonical dataset names.
    valid_names : set[str]
        Valid dataset names from datapackage.json.
    config : GalleryConfig
        Configuration dictionary with Altair name mappings.

    Returns
    -------
    list[str]
        List of normalized dataset names.
        May contain duplicates if dataset referenced multiple times.

    Examples
    --------
    >>> code = '''
    ... source = pd.read_csv("data/cars.json")
    ... data.movies()
    ... '''
    >>> name_map = {"data/cars.json": "cars"}
    >>> valid_names = {"cars", "movies"}
    >>> config = {"altair": {"name_mapping": {}}}
    >>> extract_datasets_from_altair_code(code, name_map, valid_names, config)
    ['cars', 'movies']

    Notes
    -----
    - File path extraction uses name_map for normalization
    - API name validation uses optional _data/gallery_examples.toml mappings (for Altair v5 legacy support)
    - Altair v6+ uses canonical names directly (empty mapping in _data/gallery_examples.toml)
    - Checks for vega_datasets or altair.datasets imports before attempting API extraction
    """
    datasets = []

    # Pattern 1: File paths in quotes
    # Matches: "data/cars.json", 'data/movies.csv', etc.
    file_pattern = r'["\']data/[^"\']+["\']'
    file_matches = re.findall(file_pattern, code)
    for match in file_matches:
        normalized = normalize_dataset_reference(match.strip("\"'"), name_map)
        datasets.append(normalized)

    # Pattern 2: pd.read_csv("data/...")
    # Pandas file reading with data/ prefix
    read_csv_pattern = r'read_csv\s*\(\s*["\']([^"\']+)["\']'
    read_csv_matches = re.findall(read_csv_pattern, code)
    for match in read_csv_matches:
        if match.startswith("data/"):
            normalized = normalize_dataset_reference(match, name_map)
            datasets.append(normalized)

    # Check if code uses vega_datasets Python API
    # Only attempt API extraction if imports are present
    vega_import = r"from\s+vega_datasets\s+import\s+data"
    altair_import = r"from\s+altair\.datasets\s+import\s+data"

    if re.search(vega_import, code) or re.search(altair_import, code):
        # Extract API datasets using _data/gallery_examples.toml mappings
        # For Altair v6+, mapping is typically empty (no transformation needed)
        api_datasets = extract_altair_api_datasets(
            code,
            valid_names,
            name_mapping=config.get("altair", {}).get("name_mapping", {}),
        )
        datasets.extend(api_datasets)

    return datasets


# ============================================================================
# Technique Detection
# ============================================================================

# Technique detection patterns by category
# Each tuple: (list of patterns to match, tag to assign)
# Patterns are matched case-insensitively against serialized spec or code text
#
# The three libraries have different syntax for the same concepts:
# - Vega-Lite (JSON): {"window": [...]} in transform array
# - Altair (Python): .transform_window(...) method call
# - Vega (JSON): {"type": "window"} in data transforms
#
# Tags use category:subcategory format for flexible filtering:
# - transform:* for data transformations
# - interaction:* for user interaction features
# - geo:* for geographic visualizations
# - composition:* for multi-view compositions
# - mark:* for special mark types

TECHNIQUE_PATTERNS: list[tuple[list[str], str]] = [
    # === TRANSFORMS ===
    # Vega-Lite: "transform":[{"window":...}]
    # Altair: .transform_window(...)
    # Vega: {"type":"window"} in data transforms
    (['"window":', "transform_window", '"type":"window"'], "transform:window"),
    (['"fold":', "transform_fold", '"type":"fold"'], "transform:fold"),
    (['"pivot":', "transform_pivot", '"type":"pivot"'], "transform:pivot"),
    (
        ['"calculate":', "transform_calculate", '"type":"formula"'],
        "transform:calculate",
    ),
    (
        ['"aggregate":', "transform_aggregate", '"type":"aggregate"'],
        "transform:aggregate",
    ),
    (['"filter":', "transform_filter", '"type":"filter"'], "transform:filter"),
    (['"lookup":', "transform_lookup", '"type":"lookup"'], "transform:lookup"),
    (['"density":', "transform_density", '"type":"kde"'], "transform:density"),
    (
        ['"regression":', "transform_regression", '"type":"regression"'],
        "transform:regression",
    ),
    (['"loess":', "transform_loess", '"type":"loess"'], "transform:loess"),
    (['"flatten":', "transform_flatten", '"type":"flatten"'], "transform:flatten"),
    (['"sample":', "transform_sample", '"type":"sample"'], "transform:sample"),
    (['"quantile":', "transform_quantile", '"type":"quantile"'], "transform:quantile"),
    (['"impute":', "transform_impute", '"type":"impute"'], "transform:impute"),
    (
        ['"joinaggregate":', "transform_joinaggregate", '"type":"joinaggregate"'],
        "transform:joinaggregate",
    ),
    # Bin is tricky - appears in encoding too, so check for transform context
    # Vega uses {"type":"bin"}, Vega-Lite uses {"bin":true} or {"bin":{...}}
    (['"bin":true', '"bin":{', "transform_bin", '"type":"bin"'], "transform:bin"),
    # Extent transform (Vega-only) - computes min/max of a field
    (['"type":"extent"'], "transform:extent"),
    # Crossfilter transform (Vega-only) - multi-dimensional filtering
    # resolvefilter is always used with crossfilter
    (['"type":"crossfilter"', '"type":"resolvefilter"'], "transform:crossfilter"),
    # === INTERACTION ===
    # Vega-Lite: "params":[{"select":"point"}] or {"select":"interval"}
    # Altair: selection_point(), selection_interval(), add_params()
    # Vega: "signals":[...] with event handlers
    (
        [
            '"select":"point"',
            '"select":"interval"',
            "selection_point",
            "selection_interval",
        ],
        "interaction:selection",
    ),
    # Note: "signals":[ matches most Vega specs since signals are fundamental.
    # This is intentional - Vega's reactive model IS its interaction system.
    (['"params":[', "add_params(", '"signals":['], "interaction:param"),
    (
        [
            '"bind":',
            "binding_select",
            "binding_range",
            "binding_radio",
            "binding_checkbox",
        ],
        "interaction:binding",
    ),
    (['"condition":{"param"', "alt.when("], "interaction:conditional"),
    # === GEOGRAPHIC ===
    (['"geoshape"', "mark_geoshape"], "geo:shape"),
    (['"projection":', "projection=", '"projections":'], "geo:projection"),
    (['"longitude"', '"latitude"', "longitude:", "latitude:"], "geo:coordinates"),
    (["topojson", "topo_feature"], "geo:topojson"),
    # === COMPOSITION ===
    # Vega-Lite: "facet":{}, "row":{}, "column":{}
    # Altair: .facet(), row=, column=
    (
        ['"facet":', '"row":{', '"column":{', ".facet(", "row=", "column="],
        "composition:facet",
    ),
    (['"layer":[', "alt.layer("], "composition:layer"),
    (
        ['"hconcat":', '"vconcat":', '"concat":', "alt.hconcat(", "alt.vconcat("],
        "composition:concat",
    ),
    (['"repeat":', ".repeat("], "composition:repeat"),
    # === SPECIAL MARKS ===
    (['"boxplot"', "mark_boxplot"], "mark:boxplot"),
    (['"errorbar"', '"errorband"', "mark_errorbar", "mark_errorband"], "mark:error"),
    (['"trail"', "mark_trail"], "mark:trail"),
]


def detect_techniques(
    spec_or_code: dict[str, Any] | str,
    _gallery_name: str,
) -> list[str]:
    """
    Detect Vega/Vega-Lite/Altair techniques from spec or code.

    Scans the spec (JSON) or code (Python string) for known patterns
    that indicate usage of specific visualization techniques.

    Parameters
    ----------
    spec_or_code
        For Vega/Vega-Lite: parsed JSON spec as dict
        For Altair: Python source code as string
    _gallery_name
        One of "vega", "vega-lite", "altair" (currently unused but
        reserved for future library-specific detection logic)

    Returns
    -------
    list[str]
        Sorted list of technique tags like ["transform:window", "interaction:selection"]

    Examples
    --------
    Vega-Lite spec with window transform:

    >>> spec = {"transform": [{"window": [{"op": "rank", "as": "rank"}]}]}
    >>> detect_techniques(spec, "vega-lite")
    ['transform:window']

    Altair code with selection:

    >>> code = "brush = alt.selection_interval()"
    >>> detect_techniques(code, "altair")
    ['interaction:selection']

    Notes
    -----
    - Pattern matching on serialized JSON is intentionally simple—catches 90%+ of cases
    - Tags use `category:subcategory` format for future filtering flexibility
    - Empty `techniques: []` is valid (simple examples with no notable features)
    - _gallery_name parameter is reserved for future use where library-specific
      detection may be needed
    """
    techniques: set[str] = set()

    # Convert to searchable lowercase text
    if isinstance(spec_or_code, dict):
        # JSON spec - serialize compactly for pattern matching
        text = json.dumps(spec_or_code, separators=(",", ":")).lower()
    else:
        # Python code string
        text = spec_or_code.lower()

    for patterns, tag in TECHNIQUE_PATTERNS:
        if any(p.lower() in text for p in patterns):
            techniques.add(tag)

    return sorted(techniques)


def extract_altair_category(code: str) -> str | None:
    r"""
    Extract category from Altair example code comment.

    Altair examples use a comment convention to specify categories:
        # category: bar charts

    This function extracts and normalizes the category name.

    Parameters
    ----------
    code : str
        Altair Python source code.

    Returns
    -------
    str | None
        Extracted category in Title Case, or None if not found.

    Examples
    --------
    >>> code = "# category: bar charts\\nimport altair as alt"
    >>> extract_altair_category(code)
    'Bar Charts'

    >>> code = "import altair as alt"
    >>> extract_altair_category(code)
    None

    Notes
    -----
    - Pattern matches: # category: <text>
    - Whitespace around category name is stripped
    - Result is converted to Title Case for consistency
    - Returns None if comment not found
    """
    # Match: # category: <category name>
    # Must be at start of line (^)
    pattern = r"^#\s*category:\s*(.*)$"
    match = re.search(pattern, code, re.MULTILINE)
    if match:
        return match.group(1).strip().title()
    return None


def extract_altair_description(code: str) -> str | None:
    """
    Extract description from Altair example module docstring.

    Altair examples typically have a module docstring with structure:
        \"\"\"Title
        ======
        Description text here.
        \"\"\"

    This function extracts the description text, skipping the title
    and underline.

    Parameters
    ----------
    code : str
        Altair Python source code.

    Returns
    -------
    str | None
        Extracted description with normalized whitespace, or None if
        not found or empty.

    Examples
    --------
    >>> code = '''
    ... \"\"\"Bar Chart
    ... =========
    ... A simple bar chart example.
    ... \"\"\"
    ... import altair as alt
    ... '''
    >>> extract_altair_description(code)
    'A simple bar chart example.'

    >>> code = "import altair as alt"
    >>> extract_altair_description(code)
    None

    Notes
    -----
    - Handles both triple-quote styles (''' and \"\"\")
    - Detects title/underline pattern and skips them
    - Normalizes whitespace (converts multiple spaces/newlines to single space)
    - Returns None if docstring empty after removing title
    - Underlines can be = or - characters
    """
    # Match docstring at start of file
    # (?:'''|\"\"\") = non-capturing group for quote style
    # .+? = non-greedy match for content
    # re.DOTALL = . matches newlines
    pattern = r'^(?:\'\'\'|""")(.+?)(?:\'\'\'|""")'
    match = re.search(pattern, code, re.MULTILINE | re.DOTALL)
    if match:
        docstring = match.group(1).strip()
        lines = docstring.split("\n")

        # Check if second line is an underline (title pattern)
        # Pattern: line of = or - characters
        if len(lines) >= 2 and re.match(r"^[=-]+$", lines[1].strip()):
            # Skip title and underline, join the rest
            description = "\n".join(lines[2:]).strip()
        else:
            # No title pattern, use whole docstring
            description = docstring

        # Normalize whitespace: collapse multiple spaces/newlines
        description = re.sub(r"\s+", " ", description).strip()
        return description or None

    return None


def enrich_examples_with_datasets(
    examples: list[dict[str, Any]],
    session: requests.Session,
    name_map: DatasetNameMap,
    valid_names: ValidNames,
    config: GalleryConfig,
) -> None:
    """
    Fetch specs and extract datasets and techniques for all examples (in-place).

    This is the main orchestration function for Phase 4. It iterates
    through all collected examples, fetches their specifications or
    code, routes to the appropriate extraction function, and updates
    the example dictionaries with dataset and technique information.

    Parameters
    ----------
    examples : list[dict[str, Any]]
        List of IntermediateExample dictionaries (modified in-place).
        Each example's datasets, techniques, description, and categories
        fields will be populated.
    session : requests.Session
        HTTP session for connection pooling.
    name_map : dict[str, str]
        Map from file paths to canonical dataset names.
    valid_names : set[str]
        Valid dataset names from datapackage.json.
    config : GalleryConfig
        Configuration dictionary with network and Altair settings.

    Returns
    -------
    None
        Modifies examples list in-place.

    Examples
    --------
    >>> examples = [
    ...     {"gallery_name": "vega-lite", "spec_url": "http://...", "datasets": []}
    ... ]
    >>> session = requests.Session()
    >>> name_map = {"data/cars.json": "cars"}
    >>> valid_names = {"cars"}
    >>> config = {"network": {"timeout": 30}, "altair": {"name_mapping": {}}}
    >>> enrich_examples_with_datasets(examples, session, name_map, valid_names, config)
    >>> examples[0]["datasets"]
    ['cars']

    Notes
    -----
    - Progress logged every 50 examples
    - Errors are logged but don't stop processing
    - Duplicates in datasets are removed while preserving order
    - Techniques are auto-detected via pattern matching (see detect_techniques())
    - Vega-Lite and Vega descriptions extracted from spec.description
    - Altair categories and descriptions extracted from code comments
    - Altair API name validation uses _data/gallery_examples.toml mappings
    - Failed fetches or parsing errors are logged as warnings
    """
    logger.info("Enriching %s examples with dataset information...", len(examples))
    timeout = config.get("network", {}).get("timeout", DEFAULT_TIMEOUT)

    for i, example in enumerate(examples):
        # Progress logging every 50 examples
        if (i + 1) % 50 == 0:
            logger.info("  Progress: %s/%s", i + 1, len(examples))

        try:
            # Fetch the specification or code
            response = session.get(example["spec_url"], timeout=timeout)
            if response.status_code != 200:
                logger.warning(
                    "Failed to fetch %s: %s", example["spec_url"], response.status_code
                )
                continue

            # Route to appropriate extraction function based on gallery
            # Each branch extracts: datasets, techniques, and optionally description
            if example["gallery_name"] == "vega-lite":
                spec = response.json()
                datasets = extract_datasets_from_vegalite_spec(spec, name_map)
                techniques = detect_techniques(spec, "vega-lite")
                # Extract description from spec if not already set
                if not example["description"] and "description" in spec:
                    example["description"] = spec["description"]

            elif example["gallery_name"] == "vega":
                spec = response.json()
                datasets = extract_datasets_from_vega_spec(spec, name_map)
                techniques = detect_techniques(spec, "vega")
                # Extract description from spec if not already set
                if not example["description"] and "description" in spec:
                    example["description"] = spec["description"]

            elif example["gallery_name"] == "altair":
                code = response.text
                assert isinstance(code, str)  # response.text is always str in requests
                datasets = extract_datasets_from_altair_code(
                    code, name_map, valid_names, config
                )
                techniques = detect_techniques(code, "altair")
                # Extract category from code comment
                category = extract_altair_category(code)
                if category:
                    example["categories"] = [category]
                # Extract description from docstring
                description = extract_altair_description(code)
                if description:
                    example["description"] = description

            else:
                # Defensive: should not happen with TypedDict
                logger.warning("Unknown gallery: %s", example["gallery_name"])
                continue

            # Remove duplicates while preserving order
            unique_datasets = make_dataset_references(datasets)

            # Validate dataset references (log warnings for unknown datasets)
            try:
                validator = SimpleDatasetValidator(valid_names)
                validator.validate_all(unique_datasets)
            except ValueError as e:
                # Log warning but don't fail - gallery examples may reference
                # datasets not yet in vega-datasets or use custom data sources
                logger.warning(
                    "Dataset validation warning for %s example '%s': %s",
                    example.get("gallery_name", "unknown"),
                    example.get("example_name", "unnamed"),
                    e,
                )

            example["datasets"] = unique_datasets
            example["techniques"] = techniques

        except Exception as e:
            # Log error but continue processing other examples
            # This ensures one bad example doesn't crash the entire run
            logger.warning("Error processing %s: %s", example["example_name"], e)
            continue

    logger.info("Enrichment complete!")


# ============================================================================
# Output Generation Functions (Phase 5)
# ============================================================================


def finalize_examples(examples: list[dict[str, Any]]) -> list[GalleryExample]:
    """
    Finalize examples: assign IDs, sort. Returns data-only list for v2 compliance.

    Takes a list of enriched examples and prepares them for JSON output
    by assigning sequential IDs and sorting consistently. Per Data Package v2,
    the output is a plain array (data-only); metadata is stored in datapackage.json.

    Parameters
    ----------
    examples : list[dict[str, Any]]
        List of enriched IntermediateExample dictionaries.

    Returns
    -------
    list[GalleryExample]
        List of gallery examples ready for JSON serialization.
        Sorted by gallery_name, then example_name, with sequential IDs.

    Examples
    --------
    >>> examples = [
    ...     {'gallery_name': 'vega-lite', 'example_name': 'Scatter Plot', ...},
    ...     {'gallery_name': 'altair', 'example_name': 'Bar Chart', ...}
    ... ]
    >>> output = finalize_examples(examples)
    >>> output[0]["id"]
    1
    >>> output[1]["id"]
    2
    >>> isinstance(output, list)
    True

    Notes
    -----
    - Examples are sorted first by gallery_name, then by example_name
    - IDs are assigned sequentially starting at 1
    - This ensures consistent output across runs (same examples = same order)
    - Data Package v2 compliance: metadata is in datapackage.json, not here
    """
    # Sort by gallery name, then example name for consistent ordering
    # This ensures the output is deterministic and easy to diff
    examples.sort(key=operator.itemgetter("gallery_name", "example_name"))

    # Assign sequential IDs starting at 1
    for i, example in enumerate(examples, start=1):
        example["id"] = i

    # Return data-only list (Data Package v2 compliance)
    # Cast needed because list[dict[str, Any]] is not compatible with list[GalleryExample]
    # due to invariance, even though the runtime structure matches
    return cast("list[GalleryExample]", examples)


def write_json_output(
    data: list[GalleryExample] | list[dict[str, Any]], output_path: Path
) -> None:
    """
    Write final JSON output to file.

    Writes the finalized example data to a JSON file with human-readable
    formatting (2-space indentation, UTF-8 encoding, preserved unicode).
    Per Data Package v2, the output is a plain array (data-only).

    Parameters
    ----------
    data : list[GalleryExample] | list[dict[str, Any]]
        List of gallery examples from finalize_examples().
    output_path : Path
        Path to the output JSON file.

    Returns
    -------
    None

    Raises
    ------
    OSError
        If the file cannot be written (permissions, disk space, etc.).

    Examples
    --------
    >>> data = [{"id": 1, "gallery_name": "altair", ...}, ...]
    >>> output_path = Path("gallery_examples.json")
    >>> write_json_output(data, output_path)
    # Writes formatted JSON array to gallery_examples.json

    Notes
    -----
    - Uses 2-space indentation for readability
    - UTF-8 encoding for international character support
    - ensure_ascii=False preserves unicode characters
    - Creates parent directories if they don't exist
    - Data Package v2 compliance: outputs plain array, metadata in datapackage.json
    """
    logger.info("Writing output to %s", output_path)

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write with human-readable formatting
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,  # Allow unicode characters
            sort_keys=False,  # Preserve order
        )

    logger.info("Wrote %s examples to %s", len(data), output_path)


# ============================================================================
# Main Orchestration (Phase 6)
# ============================================================================


def main(
    output_path: Path | None = None,
    dry_run: bool = False,
) -> None:
    """
    Main entry point for gallery examples collection.

    Orchestrates all phases of the collection process:
    1. Load configuration from _data/gallery_examples.toml
    2. Build dataset name mapping from datapackage.json
    3. Collect examples from all three galleries
    4. Enrich examples with dataset information
    5. Finalize and write output

    Configuration is loaded from _data/gallery_examples.toml in the repository root.
    Command-line arguments override configuration file settings.

    Parameters
    ----------
    output_path : Path | None, default None
        Custom output file path. If None, uses default from _data/gallery_examples.toml
        or gallery_examples.json in the repository root.
    dry_run : bool, default False
        If True, performs all collection and extraction but does not
        write output file. Useful for testing and validation.
        Overrides _data/gallery_examples.toml setting.

    Returns
    -------
    None

    Raises
    ------
    requests.HTTPError
        If any HTTP request fails.
    OSError
        If output file cannot be written (unless dry_run=True).

    Examples
    --------
    >>> main()  # Use defaults from _data/gallery_examples.toml
    >>> main(output_path=Path("test.json"))  # Custom output
    >>> main(dry_run=True)  # Test without writing

    Notes
    -----
    - Expected runtime: 2-4 minutes depending on network speed
    - Progress is logged to console
    - Errors in individual examples don't stop the entire process
    - Session is closed automatically via try/finally
    - Dry-run still fetches all data but skips file write
    - Configuration file is optional (uses defaults if not found)
    - Altair API name validation uses _data/gallery_examples.toml mappings (see config['altair']['name_mapping'])
    """
    start_time = time.time()

    logger.info("=== Gallery Examples Collection Starting ===")

    # Load configuration
    config = load_config()

    # Apply config defaults (can be overridden by parameters)
    if output_path is None:
        repo_dir = Path(__file__).parent.parent
        default_output = config.get("output", {}).get(
            "default_output_path", "gallery_examples.json"
        )
        output_path = repo_dir / default_output

    # output_path is guaranteed to be Path at this point
    assert output_path is not None, "output_path should be set"

    # CLI dry_run overrides config
    if not dry_run:
        dry_run = config.get("output", {}).get("dry_run", False)

    if dry_run:
        logger.info("DRY RUN MODE - Will not write output file")

    # Get config values
    timeout = config.get("network", {}).get("timeout", DEFAULT_TIMEOUT)
    sources = config.get("sources", {})

    session = requests.Session()

    try:
        # Phase 1: Build dataset mapping
        logger.info("\n--- Phase 1: Building dataset name mapping ---")
        datapackage_url = sources.get(
            "datapackage_url",
            "https://raw.githubusercontent.com/vega/vega-datasets/main/datapackage.json",
        )
        datapackage = fetch_datapackage(session, datapackage_url, timeout)
        name_map = build_dataset_name_map(datapackage)
        valid_names = set(name_map.values())
        logger.info("Built mapping for %s datasets", len(valid_names))

        # Phase 2: Collect examples
        logger.info("\n--- Phase 2: Collecting gallery examples ---")

        vegalite_url = sources.get(
            "vega_lite_examples_url",
            "https://raw.githubusercontent.com/vega/vega-lite/main/site/_data/examples.json",
        )
        vegalite_examples = collect_vega_lite_examples(session, vegalite_url, timeout)

        vega_url = sources.get(
            "vega_examples_url",
            "https://raw.githubusercontent.com/vega/vega/main/docs/_data/examples.json",
        )
        vega_examples = collect_vega_examples(session, vega_url, timeout)

        altair_dirs = sources.get(
            "altair_examples_dirs",
            [
                "tests/examples_methods_syntax",
                "tests/examples_arguments_syntax",
            ],
        )
        altair_examples = collect_altair_examples(session, altair_dirs, timeout)

        all_examples = vegalite_examples + vega_examples + altair_examples
        logger.info("Total examples collected: %s", len(all_examples))

        # Phase 3: Enrich with datasets
        logger.info("\n--- Phase 3: Extracting datasets from specs ---")
        enrich_examples_with_datasets(
            all_examples, session, name_map, valid_names, config
        )

        # Phase 4: Finalize and write
        logger.info("\n--- Phase 4: Finalizing and writing output ---")
        output_data = finalize_examples(all_examples)

        if not dry_run:
            write_json_output(output_data, output_path)
        else:
            logger.info("DRY RUN: Skipping write to %s", output_path)
            logger.info("Would have written %s examples", len(output_data))

        # Summary
        elapsed = time.time() - start_time
        logger.info("\n=== Collection Complete ===")
        if not dry_run:
            logger.info("Output: %s", output_path)
        else:
            logger.info("Mode: DRY RUN (no file written)")
        logger.info("Examples: %s", len(all_examples))
        logger.info("Time: %.1fs", elapsed)

    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
        raise
    finally:
        session.close()


def parse_args() -> dict[str, Any]:
    """
    Parse command-line arguments.

    Returns
    -------
    dict[str, Any]
        Dictionary of parsed arguments with keys:
        - output: Path or None
        - verbose: bool
        - dry_run: bool

    Examples
    --------
    >>> # Command: python script.py --output test.json --verbose
    >>> args = parse_args()
    >>> args["output"]
    PosixPath('test.json')
    >>> args["verbose"]
    True
    """
    parser = argparse.ArgumentParser(
        description="Generate gallery_examples.json from Vega ecosystem galleries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Use defaults from _data/gallery_examples.toml
  %(prog)s --output test.json                 # Custom output path
  %(prog)s --dry-run                          # Test without writing
  %(prog)s --verbose --dry-run                # Debug with dry-run

Notes:
  - Altair API name validation uses _data/gallery_examples.toml mappings (see config['altair']['name_mapping'])
  - Expected runtime: 2-4 minutes depending on network speed
  - Output: ~470 examples from Vega, Vega-Lite, and Altair galleries
        """,
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file path (default: gallery_examples.json in repo root)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Collect data but do not write output file",
    )

    args = parser.parse_args()

    return {
        "output": args.output,
        "verbose": args.verbose,
        "dry_run": args.dry_run,
    }


if __name__ == "__main__":
    args = parse_args()

    # Set log level if verbose
    if args["verbose"]:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Run main with parsed arguments
    main(
        output_path=args["output"],
        dry_run=args["dry_run"],
    )
