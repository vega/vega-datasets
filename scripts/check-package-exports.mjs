import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

// Read the file list from npm pack --dry-run --json, not the local build directory.
const pkg = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));
const [pack] = JSON.parse(readFileSync(0, 'utf8'));
const files = new Set(pack.files.map(({ path }) => path));

for (const [condition, target] of Object.entries(pkg.exports)) {
  assert.ok(
    files.has(target.replace(/^\.\//, '')),
    `Missing ${condition} export in npm package: ${target}`
  );
}
