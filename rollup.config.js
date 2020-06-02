import resolve from '@rollup/plugin-node-resolve';
import json from '@rollup/plugin-json';

export default {
  input: "build/src/index.js",
  output: {
    file: "build/vega-datasets.js",
    format: "umd",
    sourcemap: true,
    name: "vegaDatasets"
  },
  plugins: [resolve(), json()]
};
