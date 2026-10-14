/** Test helpers: the built catalog and the repository's data files. */
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Catalog, type CatalogFile, type Gallery } from '../src/lib/catalog';

export const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');

export function loadCatalog(): Catalog {
  const file = path.join(REPO, 'site', 'generated', 'catalog.json');
  if (!existsSync(file)) throw new Error(`${file} is missing: run \`npm run site:build\` first.`);
  return new Catalog(JSON.parse(readFileSync(file, 'utf8')) as CatalogFile);
}

/** Count example membership independently of the per-dataset usage index. */
export function exampleCount(catalog: Catalog, name: string, galleries: readonly Gallery[] = []): number {
  return catalog.examples.filter((e) => e.datasets.includes(name) && (!galleries.length || galleries.includes(e.gallery))).length;
}

/** Read the local copy of a dataset URL (jsDelivr or GitHub Pages), so tests run offline. */
export function readDataUrl(url: string): string {
  const rel = url.split('/data/').pop();
  if (!rel || !/^https:\/\/(cdn\.jsdelivr\.net\/npm\/vega-datasets@\d+|vega\.github\.io\/vega-datasets)\/data\//.test(url)) {
    throw new Error(`Not a vega-datasets data URL: ${url}`);
  }
  return readFileSync(path.join(REPO, 'data', rel), 'utf8');
}
