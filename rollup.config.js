import json from "@rollup/plugin-json";
import ts from "rollup-plugin-ts";
import bundleSize from "rollup-plugin-bundle-size";
import { terser } from "rollup-plugin-terser";

const plugins = (browserslist, declaration) => [
  json(),
  ts({
    tsconfig: (resolvedConfig) => ({
      ...resolvedConfig,
      declaration,
      declarationMap: declaration,
    }),
    transpiler: "babel",
    babelConfig: { presets: ["@babel/preset-env"] },
    browserslist,
  }),
  bundleSize(),
];

const outputs = [
  {
    input: "src/index.ts",
    output: {
      file: "build/vega-datasets.module.js",
      format: "esm",
      sourcemap: true,
    },
    plugins: plugins(undefined, true)
  },
  {
    input: "src/index.ts",
    output: [
      {
        file: "build/vega-datasets.js",
        format: "umd",
        sourcemap: true,
        name: "vegaDatasets",
      },
      {
        file: "build/vega-datasets.min.js",
        format: "umd",
        sourcemap: true,
        name: "vegaDatasets",
        plugins: [terser()],
      },
    ],
    plugins: plugins("defaults and not IE 11", false)
  },
];

export default outputs;
