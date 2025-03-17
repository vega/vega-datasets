# Contributing to Vega Datasets

Thank you for your interest in contributing to Vega Datasets! This repository serves as a centralized hub for datasets used across the Vega ecosystem (Vega, Vega-Lite, Altair).

We welcome contributions that enhance metadata, improve documentation, fix dataset issues, enhance infrastructure, or add new datasets that demonstrate visualization techniques. Each dataset should serve a clear purpose in showcasing visualization capabilities.

All contributions are accepted under the [Project's license](./LICENSE). The Project abides by the Vega Organization's [code of conduct](https://github.com/vega/.github/blob/main/CODE_OF_CONDUCT.md) and [governance](https://github.com/vega/.github/blob/main/project-docs/GOVERNANCE.md).

## Dataset Contribution Guidelines

### General Principles

1. **Maintain backward compatibility**: Avoid modifying existing datasets as other projects rely on them for tests and examples.

2. **Use open datasets**: All datasets must be available under an open license (e.g., CC0, CC-BY, ODbL, Public Domain) with proper attribution and license documentation.

3. **Document thoroughly**: Include detailed descriptions, sources, license information, and field definitions.

**Important**: The BSD-3-Clause license of this repository applies to the package code and infrastructure, NOT to the datasets themselves. Each dataset maintains its original license.

### Data Generation Scripts

For datasets requiring processing:

- Place scripts in the `scripts/` directory and configuration files in `_data/`
- Include detailed documentation explaining parameters and processing steps
- Ensure reproducibility with deterministic outputs and fixed random seeds when applicable
- See `scripts/flights.py` as an example

## Metadata and Documentation

We follow the [Data Package Standard 2.0](https://datapackage.org/standard/) with:

- Auto-generated `datapackage.json` and `datapackage.md` files
- Datasets in the `data/` directory
- Source metadata in `_data/datapackage_additions.toml`

### Metadata Requirements

The metadata system combines automatic inference with manual specification:

1. The `build_datapackage.py` script automatically infers basic metadata for each dataset (file format, size, data types)
2. You provide additional context and documentation in `_data/datapackage_additions.toml`
3. The build process merges these together, with manual entries taking precedence over inferred ones

For each dataset, add an entry to `_data/datapackage_additions.toml`:

```toml
[[resources]] # Path: example.json
path = "example.json"
description = """Detailed description of the dataset"""

# Schema section for documenting data fields/columns
# The system will infer basic column types automatically, but you should add descriptions
[resources.schema]
[[resources.schema.fields]]
name = "field1"  # Must match the actual column name in the dataset
description = "Description of what this column/field represents"

[[resources.schema.fields]]
name = "field2"  # Must match the actual column name in the dataset
description = "Description of what this column/field represents"
# Optional: For categorical fields, list possible values
categories = ["category1", "category2", "category3"]

# For fields with numeric values, you can include statistics or other context if highly relevant
# [[resources.schema.fields]]
# name = "numericField"
# description = "mean: 0.5, range: [0, 1], etc."

# Data sources documentation
[[resources.sources]]
title = "Original Data Source Name"
path = "https://example.com/source-url"
# Optional: version information if available
# version = "1.0"

# License documentation
[[resources.licenses]]
name = "license-id"  # e.g., "CC-BY-4.0"
path = "https://example.com/license-url"
title = "Human-readable license name"
```

#### How the Metadata System Works

- **Automatic Inference**: For tabular files (CSV, TSV, JSON, Parquet, Arrow), the system automatically detects column names and data types
- **Manual Additions**: Use the TOML file to add descriptions, categories, source information, and licenses
- **Field Matching**: When documenting columns in `resources.schema.fields`, ensure the `name` field exactly matches the column name in your dataset
- **Precedence**: Your manual definitions in the TOML file will override any automatically inferred values
- **Complete Examples**: See existing entries in `_data/datapackage_additions.toml` for reference on documenting various types of datasets

Generate metadata files by running:

```bash
npm run build
```

## Development Setup

### Prerequisites

- Node.js (for npm)
- Python and [uv](https://github.com/astral-sh/uv) (for data processing scripts)

### Getting Started

1. Fork and clone the repository:
   ```
   git clone https://github.com/YOUR-USERNAME/vega-datasets.git
   cd vega-datasets
   npm install
   ```

2. (Optional) Set up Python environment:
   ```
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

### Code Quality Checks

Run these checks before submitting:

```bash
# TOML formatting
uvx taplo fmt --check --diff

# Python linting and formatting
uvx ruff check
uvx ruff format --check

To automatically fix issues:
```bash
uvx taplo fmt
uvx ruff format
```

## Contributing Process

1. Create a branch:
   ```
   git checkout -b your-feature-branch
   ```

2. Make your changes following the guidelines above.

3. Run checks and build:
   ```
   uvx taplo fmt --check --diff && uvx ruff check && uvx ruff format --check
   npm run build
   ```

4. Commit and push:
   ```
   git commit -am "Add new dataset: description of dataset and changes"
   git push origin your-feature-branch
   ```

5. Open a pull request against the `main` branch.

6. Wait for CI checks to pass and respond to reviewer feedback.
