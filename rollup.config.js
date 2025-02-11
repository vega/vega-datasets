import json from '@rollup/plugin-json';
import { nodeResolve } from '@rollup/plugin-node-resolve';
import typescript from '@rollup/plugin-typescript';
import bundleSize from 'rollup-plugin-bundle-size';

import pkg from './package.json' with { type: 'json' };

const outputs = [
  {
    input: 'src/index.ts',
    output: {
      file: pkg.exports.default,
      format: 'esm',
      sourcemap: true,
    },
    plugins: [nodeResolve(), json(), typescript(), bundleSize()],
    external: Object.keys(pkg.dependencies),
  },
];

export default outputs;
