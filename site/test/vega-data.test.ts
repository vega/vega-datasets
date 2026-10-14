// The two Vega hooks that let the page run a spec as published under its CSP
// (lib/vega-data.ts): CSV and TSV readers that compile no code, and the loader's mapping
// from public data URLs to the site's own data/.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { csvParse } from 'd3-dsv';
import * as vega from 'vega';
import { describe, expect, test } from 'vitest';
import { PUBLIC_DATA, readers, siteDataUri } from '../src/lib/vega-data';
import { loadCatalog, REPO } from './catalog';

const catalog = loadCatalog();

type Reader = (text: string, format: Record<string, unknown>) => Record<string, unknown>[];
const registry = vega as unknown as { formats(name: string, reader?: unknown): Reader };
/** Vega's own readers, taken before any test registers ours. */
const BUILT_IN: Record<string, Reader> = Object.fromEntries(['csv', 'tsv', 'dsv'].map((t) => [t, registry.formats(t)]));

/** Run `fn` with our readers registered, then put Vega's back (all of them). */
function withOurReaders<T>(fn: () => T): T {
  try {
    for (const [name, reader] of Object.entries(readers())) registry.formats(name, reader);
    return fn();
  } finally {
    for (const [name, reader] of Object.entries(BUILT_IN)) registry.formats(name, reader);
  }
}
const text = (file: string) => readFileSync(path.join(REPO, 'data', file), 'utf8');

/** Run `fn` as under the page's CSP (script-src 'self', no 'unsafe-eval'): compiling code throws. */
function withoutEval<T>(fn: () => T): T {
  const original = globalThis.Function;
  globalThis.Function = new Proxy(original, {
    apply() { throw new EvalError('CSP: unsafe-eval'); },
    construct() { throw new EvalError('CSP: unsafe-eval'); },
  });
  try {
    return fn();
  } finally {
    globalThis.Function = original;
  }
}

describe('reading tables under the page CSP', () => {
  const tables = catalog.datasets.filter((d) => d.kind === 'table' && (d.format === 'csv' || d.format === 'tsv'));

  test("our readers are not Vega's (the comparisons below are real)", () => {
    expect(BUILT_IN.csv).not.toBe(readers().csv);
    expect(String(BUILT_IN.csv)).toContain('delimiter');
  });

  test('the harness catches code compilation (d3 csvParse, which Vega uses, fails)', () => {
    expect(() => withoutEval(() => csvParse(text('seattle-weather.csv')))).toThrow(EvalError);
  });

  test.each(tables.map((d) => [d.name, d] as const))('%s parses through vega.formats without compiling code', (_name, d) => {
    const rows = withOurReaders(() => withoutEval(() => vega.read(text(d.file), { type: d.format as 'csv' }))) as Record<string, unknown>[];
    expect(rows).toHaveLength(d.rows!);
    expect(Object.keys(rows[0]!)).toEqual(d.fields.map((f) => f.name));
  });

  test('the "dsv" type keeps its delimiter', () => {
    expect(readers().dsv!('a|b\n1|2', { delimiter: '|' })).toEqual([{ a: '1', b: '2' }]);
    expect(readers().csv!('a,b\n1,\n', {})).toEqual([{ a: '1', b: '' }]);
  });
});

describe("the readers match Vega's own on every format option they can meet", () => {
  const vegaReader = (type: string) => BUILT_IN[type]!;
  const ours = readers() as unknown as Record<string, Reader>;

  test.each([
    ['csv', 'a,b\n1,2\n3,4\n', {}],
    ['csv', '1,2\n3,4', { header: ['a', 'b'] }],
    ['csv', '"x, y",z\n"multi\nline","q ""uoted"""\n', {}],
    ['csv', 'a,b,c\n1\n1,2,3,4\n', {}],
    ['csv', '', {}],
    ['csv', 'a,b\n1,2', { delimiter: '|' }],
    ['tsv', 'a\tb\n1\t2\n', {}],
    ['tsv', '1\t2\n3\t4', { header: ['a', 'b'] }],
    ['dsv', 'a|b\n1|2\n', { delimiter: '|' }],
    ['dsv', '1|2\n3|4', { delimiter: '|', header: ['a', 'b'] }],
  ] as const)('%s %j %j', (type, text, format) => {
    const theirs = [...vegaReader(type)(text, { type, ...format })];
    expect(ours[type]!(text, { type, ...format })).toEqual(theirs);
  });

  test('Vega still applies `parse` after our reader', () => {
    const text = 'a,d,s\n1,2001,x\n2.5,2002,y\n';
    const format = { type: 'csv', parse: { a: 'number', d: 'date:"%Y"' } } as const;
    const theirs = vega.read(text, { ...format });
    const mine = withOurReaders(() => vega.read(text, { ...format })) as Record<string, unknown>[];
    expect(mine).toEqual(theirs);
    expect(mine[1]!.a).toBe(2.5);
    expect(mine[0]!.d).toBeInstanceOf(Date);
  });

  test("the readers ask for text, as Vega's do", () => {
    for (const type of ['csv', 'tsv', 'dsv']) expect((ours[type] as unknown as { responseType?: string }).responseType, type).toBe('text');
  });
});

describe('the loader maps public data URLs to the site', () => {
  const site = 'http://localhost:8000/vega-datasets/data/';

  test.each([
    ['https://cdn.jsdelivr.net/npm/vega-datasets@3/data/cars.json', `${site}cars.json`],
    ['https://cdn.jsdelivr.net/npm/vega-datasets@3.2.1/data/us-10m.json', `${site}us-10m.json`],
    ['https://vega.github.io/vega-datasets/data/flights-200k.json', `${site}flights-200k.json`],
    ['https://vega.github.io/vega-datasets/data/sub/dir.csv', `${site}sub/dir.csv`],
  ])('%s', (uri, local) => {
    expect(uri).toMatch(PUBLIC_DATA);
    expect(siteDataUri(uri, site)).toBe(local);
  });

  test.each([
    'https://cdn.jsdelivr.net/npm/other-package@1/data/cars.json',
    'https://vega.github.io/vega-lite/data/cars.json',
    'https://example.org/vega-datasets/data/cars.json',
    'data/cars.json',
  ])('leaves %s alone', (uri) => {
    expect(siteDataUri(uri, site)).toBe(uri);
  });
});
