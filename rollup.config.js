import resolve from 'rollup-plugin-node-resolve';

export default {
  input: "build/index.js",
  output: {
    file: "build/vega-datasets.js",
    format: "umd",
    sourcemap: true,
    name: "vegaDatasets"
  },
  plugins: [ resolve() ]
};
