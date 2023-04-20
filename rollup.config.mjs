import json from "@rollup/plugin-json";
import resolve from '@rollup/plugin-node-resolve';
import bundleSize from "rollup-plugin-bundle-size";
import { terser } from "rollup-plugin-terser";
import ts from "rollup-plugin-ts";

import pkg from './package.json' assert { type: 'json' };

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

export default outputs;
