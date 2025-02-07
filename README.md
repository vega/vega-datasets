# Vega Datasets

[![npm version](https://img.shields.io/npm/v/vega-datasets.svg)](https://www.npmjs.com/package/vega-datasets)
[![Build Status](https://github.com/vega/vega-datasets/workflows/Test/badge.svg)](https://github.com/vega/vega-datasets/actions)
[![](https://data.jsdelivr.com/v1/package/npm/vega-datasets/badge?style=rounded)](https://www.jsdelivr.com/package/npm/vega-datasets)

Collection of datasets used in example galleries for [Vega](https://vega.github.io/vega/examples/) and [Vega-Lite](https://vega.github.io/vega-lite/examples/). This data lives at https://github.com/vega/vega-datasets and https://cdn.jsdelivr.net/npm/vega-datasets.

Common repository for example datasets used by Vega related projects. Keep changes to this repository minimal as other projects (Vega, Vega Editor, Vega-Lite, Polestar, Voyager) use this data in their tests and for examples.

The list of sources is in [datapackage.md](https://github.com/vega/vega-datasets/blob/main/datapackage.md#resources).
This metadata is also available in a machine-readable format at [datapackage.json](https://github.com/vega/vega-datasets/blob/main/datapackage.json).


To access the data in Observable, you can import `vega-dataset`. Try our [example notebook](https://observablehq.com/@vega/vega-datasets). To access these datasets from Python, you can use the [Vega datasets python package](https://github.com/altair-viz/vega_datasets). To access them from Julia, you can use the [VegaDatasets.jl julia package](https://github.com/davidanthoff/VegaDatasets.jl).

## Data Usage Note

These datasets are intended only for instructional and demonstration purposes. Datasets may contain intentional inconsistencies or errors to provide opportunities for data cleaning exercises and to illustrate common data quality issues.

## Versioning

We use semantic versioning. However, since this package serves datasets we have additional rules about how we version data.

We do not change data in patch releases except to resolve formatting issues. Minor releases may change the data but only update datasets in ways that do not change field names or file names. Minor releases may also add datasets. Major versions may change file names, file contents, and remove or update files.

## How to use it

### HTTP

You can also get the data directly via HTTP served by GitHub or jsDelivr (a fast CDN) like:

https://vega.github.io/vega-datasets/data/cars.json or with a fixed version (recommended) such as https://cdn.jsdelivr.net/npm/vega-datasets@3/data/cars.json.

You can find a full listing of the available datasets at https://cdn.jsdelivr.net/npm/vega-datasets/data/.

### NPM

#### Get the data on disk

```
npm i vega-datasets
```

Now you have all the datasets in a folder in `node_modules/vega-datasets/data/`.

#### Get the URLs or Data via URL

```
npm i vega-datasets
```

Now you can import `import data from 'vega-datasets';` and access the URLs of any dataset with `data[NAME].url`. `data[NAME]()` returns a promise that resolves to the actual data fetched from the URL. We use d3-dsv to parse CSV files.

Here is a full example

```ts
import data from 'vega-datasets';

const cars = await data['cars.json']();
// equivalent to
// const cars = await (await fetch(data['cars.json'].url)).json();

console.log(cars);
```

## Development process

Install dependencies with `npm install`.

## Release process

To make a release, run `npm run release`.
