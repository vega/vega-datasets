// Every "Try it in the Vega Editor" starter chart must compile and draw real marks
// against the actual data file, and the Editor link must carry exactly that spec.
import LZString from 'lz-string';
import * as vega from 'vega';
import { compile, type TopLevelSpec } from 'vega-lite';
import { describe, expect, test } from 'vitest';
import type { Dataset } from '../src/lib/catalog';
import { editorUrl, starterSpec } from '../src/lib/starter';
import { loadCatalog, readDataUrl } from './catalog';

const catalog = loadCatalog();
const withStarter = catalog.datasets.filter((d) => starterSpec(d) !== null);

/** One line per dataset: the chart the rules picked, for reviewing rule changes in the snapshot. */
function describeStarter(d: Dataset): string {
  const spec = starterSpec(d) as { mark: { type: string }; encoding?: Record<string, Record<string, string>> } | null;
  if (!spec) return `${d.name}: none`;
  const enc = spec.encoding ?? {};
  const channel = (k: string) => {
    const e = enc[k];
    if (!e) return null;
    const field = e.field ?? '';
    const inner = e.timeUnit ? `${e.timeUnit}(${field})` : field;
    return `${k}=${e.aggregate ? `${e.aggregate}(${inner})` : inner}`;
  };
  const channels = ['x', 'x2', 'y', 'latitude', 'longitude', 'color'].map(channel).filter(Boolean);
  return `${d.name}: ${spec.mark.type} ${channels.join(' ')}`.trimEnd();
}

test('starter chart choices', () => {
  expect(catalog.datasets.map(describeStarter).join('\n')).toMatchSnapshot();
});

/** Field names a spec encodes, with Vega-Lite's `\\.` / `\\[` escapes removed. */
function encodedFields(spec: unknown): string[] {
  const enc = (spec as { encoding?: Record<string, { field?: string }> }).encoding ?? {};
  return Object.values(enc).flatMap((e) => (e.field ? [e.field.replace(/\\(.)/g, '$1')] : []));
}

describe.each(withStarter.map((d) => [d.name, d] as const))('%s', (_name, d) => {
  test('encodes only columns the file has', () => {
    const columns = new Set(d.fields.map((f) => f.name));
    expect(encodedFields(starterSpec(d)).filter((f) => !columns.has(f))).toEqual([]);
  });

  test('compiles without warnings and draws marks from the real file', async () => {
    const warnings: string[] = [];
    const logger = {
      level: () => logger,
      error: (...m: unknown[]) => { throw new Error(m.join(' ')); },
      warn: (...m: unknown[]) => { warnings.push(m.join(' ')); return logger; },
      info: () => logger,
      debug: () => logger,
    };
    const { spec } = compile(starterSpec(d) as TopLevelSpec, { logger: logger as never });
    expect(warnings).toEqual([]);

    const loader = vega.loader();
    loader.load = async (uri: string) => readDataUrl(uri);
    const view = new vega.View(vega.parse(spec), { renderer: 'none', loader });
    try {
      await view.runAsync();
      const svg = await view.toSVG();
      const marks = svg.match(/<(path|line|rect|circle)\b/g) ?? [];
      expect(marks.length).toBeGreaterThanOrEqual(3);
      expect(svg).not.toMatch(/NaN|undefined/);
    } finally {
      view.finalize();
    }
  }, 60_000); // flights_200k_json draws 200,000 points; the default 5 s is too tight on a busy CPU.

  test('the Editor link decodes to the same spec', () => {
    const url = editorUrl(starterSpec(d)!);
    const encoded = url.split('#/url/vega-lite/')[1];
    expect(encoded).toBeTruthy();
    expect(JSON.parse(LZString.decompressFromEncodedURIComponent(encoded!)!)).toEqual(starterSpec(d));
  });
});
