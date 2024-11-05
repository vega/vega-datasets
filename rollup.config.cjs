const { readFileSync } = require('fs');
const json = require("@rollup/plugin-json");
const resolve = require('@rollup/plugin-node-resolve');
const terser = require("@rollup/plugin-terser");
const bundleSize = require("rollup-plugin-bundle-size");
const ts = require("rollup-plugin-ts");

const pkg = JSON.parse(readFileSync('./package.json'));

const plugins = (browserslist, declaration) => [
  resolve(),
  json(),
  ts({
    tsconfig: (resolvedConfig) => ({
      ...resolvedConfig,
      declaration,
      declarationMap: declaration,
    }),
    transpiler: "babel",
    browserslist,
  }),
  bundleSize(),
];

const outputs = [
  {
    input: "src/index.ts",
    output: {
      file: pkg.module,
      format: "esm",
      sourcemap: true,
    },
    plugins: plugins(false, true)
  },
  {
    input: "src/index.ts",
    output: [
      {
        file: pkg.main,
        format: "umd",
        sourcemap: true,
        name: "vegaDatasets",
      },
      {
        file: pkg.unpkg,
        format: "umd",
        sourcemap: true,
        name: "vegaDatasets",
        plugins: [terser()],
      },
    ],
    plugins: plugins("defaults", false)
  },
];

module.exports = outputs;

