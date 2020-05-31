# Vega Datasets

[![npm version](https://img.shields.io/npm/v/vega-datasets.svg)](https://www.npmjs.com/package/vega-datasets)
[![Build Status](https://github.com/vega/vega-datasets/workflows/Test/badge.svg)](https://github.com/vega/vega-datasets/actions)

Collection of datasets used in Vega and Vega-Lite examples. This data lives at https://github.com/vega/vega-datasets.

Common repository for example datasets used by Vega related projects. Keep changes to this repository minimal as other projects (Vega, Vega Editor, Vega-Lite, Polestar, Voyager) use this data in their tests and for examples.

The list of sources is in [SOURCES.md](https://github.com/vega/vega-datasets/blob/master/SOURCES.md).

To access the data in Observable, you can import `vega-dataset`. Try our [example notebook](https://observablehq.com/@vega/vega-datasets). To access these datasets from Python, you can use the [Vega datasets python package](https://github.com/jakevdp/vega_datasets). To access them from Julia, you can use the [VegaDatasets.jl julia package](https://github.com/davidanthoff/VegaDatasets.jl).

The [Vega datasets preview notebook](https://observablehq.com/@randomfractals/vega-datasets) offers a quick way to browse the content of the available datasets.

## How to use it

Note that when you get data via URL, the data may change in the future as we don't fully guarantee backwards compatibility.

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

Now you can import `data = require('vega-datasets')` and access the URLs of any dataset with `data[NAME].url`. `data[NAME]()` returns a promise that resolves to the actual data fetched from the URL. We use d3-dsv to parse CSV files.

Here is a full example

```ts
import data from 'vega-datasets';

const cars = await data['cars.json']();
// equivalent to
// const cars = await (await fetch(data['cars.json'].url)).json();

console.log(cars);
```

### HTTP

You can also get the data directly via HTTP served by GitHub like:

https://vega.github.io/vega-datasets/data/cars.json

## Development process

Install dependencies with `yarn`. To make a release, create a new tagged version with `yarn version` and then push the tag. The CI will automatically make a release. 
