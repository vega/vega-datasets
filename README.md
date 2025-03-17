# Vega Datasets

[![npm version](https://img.shields.io/npm/v/vega-datasets.svg)](https://www.npmjs.com/package/vega-datasets)
[![Build Status](https://github.com/vega/vega-datasets/workflows/Test/badge.svg)](https://github.com/vega/vega-datasets/actions)
[![](https://data.jsdelivr.com/v1/package/npm/vega-datasets/badge?style=rounded)](https://www.jsdelivr.com/package/npm/vega-datasets)

Vega Datasets is the centralized hub for over 70 datasets featured in the examples and documentation of Vega, Vega-Lite, Altair and related projects. A dataset catalog conforming to the [Data Package Standard v2](https://datapackage.org/blog/2024-06-26-v2-release/) provides information on data structure, sourcing, and licensing. Generation scripts document data provenance and transformation, enabling reproducibility and transparency throughout the data preparation process. Each dataset is curated to illustrate essential visualization concepts, statistical methods, or domain-specific applications.

This data lives at https://github.com/vega/vega-datasets and can be accessed via CDN at https://cdn.jsdelivr.net/npm/vega-datasets.

## Contributing

Modifications of existing datasets should be kept to a minimum as other projects (Vega, Vega Editor, Vega-Lite, Polestar, Voyager) use this data in their tests and examples. Contributions of new datasets, documentation, scripts, corrections and bug fixes are encouraged. Please review the [contribution guidelines](CONTRIBUTING.md).

> [!IMPORTANT]  
> **Dataset Licensing**: Each dataset hosted in this repository maintains its original license as documented in the [datapackage metadata](datapackage.md). While we've made efforts to provide accurate licensing information, this metadata should be considered a starting point rather than definitive guidance. Users should verify their intended use complies with original source licensing terms.

## Installation

Install Vega Datasets via npm:

```bash
npm install vega-datasets
```

## Usage

### HTTP Direct Access

You can get the data directly via HTTP served by GitHub or jsDelivr (a fast CDN):

- GitHub: https://vega.github.io/vega-datasets/data/cars.json
- jsDelivr (with fixed version, recommended): https://cdn.jsdelivr.net/npm/vega-datasets@3/data/cars.json

You can find a full listing of available datasets at https://cdn.jsdelivr.net/npm/vega-datasets/data/.

### Using ESM Import

```typescript
import data from 'vega-datasets';

const cars = await data['cars.json']();
// equivalent to
// const cars = await (await fetch(data['cars.json'].url)).json();

console.log(cars);
```

### In Vega/Vega-Lite Specifications

Reference a dataset via URL:

```json
{
  "data": {
    "url": "https://cdn.jsdelivr.net/npm/vega-datasets@latest/data/cars.json"
  },
  "mark": "point",
  "encoding": {
    "x": {"field": "Horsepower", "type": "quantitative"},
    "y": {"field": "Miles_per_Gallon", "type": "quantitative"}
  }
}
```

## Language Interfaces

- **JavaScript/Observable**: Directly import Vega Datasets in Observable. See the [example notebook](https://observablehq.com/@vega/vega-datasets).
- **Python**: Access datasets using the [Vega Datasets Python package](https://github.com/altair-viz/vega_datasets).
- **Julia**: Utilize the [VegaDatasets.jl package](https://github.com/davidanthoff/VegaDatasets.jl) for Julia integrations.

## Available Datasets

Repository highlights include:

- Geographic data ([world maps](datapackage.md#world-110mjson), [US states](datapackage.md#us-10mjson), [country boundaries](datapackage.md#world-110mjson))
- Economic indicators ([unemployment](datapackage.md#unemploymenttsv), [stock data](datapackage.md#stockscsv), [budgets](datapackage.md#budgetjson))
- Scientific measurements ([weather patterns](datapackage.md#seattle-weathercsv), [earthquake data](datapackage.md#earthquakesjson))
- Statistical examples ([Anscombe's quartet](datapackage.md#anscombesjson), [iris dataset](datapackage.md#irisjson))
- Historical records ([wheat prices](datapackage.md#wheatjson), [monarch data](datapackage.md#monarchsjson))

For the complete list and details, see the [data directory](https://github.com/vega/vega-datasets/tree/main/data) or review the [datapackage.md](https://github.com/vega/vega-datasets/blob/main/datapackage.md#resources) file.

## Dataset Information

Each dataset comes with:

- **Detailed Metadata**: Source, structure, and licensing information, following [Data Package Standard v2](https://datapackage.org/) for enhanced interoperability.
- **Generation Scripts**: Automation tools that facilitate data processing and updates, ensuring consistency and reproducibility.

Further information is available in [datapackage.md](https://github.com/vega/vega-datasets/blob/main/datapackage.md) (human-readable) and [datapackage.json](https://github.com/vega/vega-datasets/blob/main/datapackage.json) (machine-readable).

## Example Galleries

Visualizations built with these datasets are showcased in several galleries:

- [Vega Example Gallery](https://vega.github.io/vega/examples/)
- [Vega-Lite Example Gallery](https://vega.github.io/vega-lite/examples/)
- [Altair Example Gallery](https://altair-viz.github.io/gallery/index.html)
- [Observable Vega Examples](https://observablehq.com/@vega)

## Data Usage Note

- The datasets are designed for instructional and demonstration purposes.
- Some datasets include intentional inconsistencies to offer opportunities for data cleaning exercises.

## Versioning

Vega Datasets follows semantic versioning with additional data-specific guidelines:

- **Patch Releases**: Minor formatting or documentation updates without changes to the data.
- **Minor Releases**: Data content updates that maintain existing file and field names, including new datasets.
- **Major Releases**: Potential changes to file names or removal of datasets that may break backward compatibility.

## Development and Release

For development setup:

```bash
npm install
```

For releasing:

```bash
npm run release
```

## License

The repository code is licensed under the BSD-3-Clause License. Note that individual datasets have distinct licensing terms as specified in their metadata.

## Acknowledgments

Appreciation is extended to the numerous organizations and individuals who have generously shared their data for use in this collection.