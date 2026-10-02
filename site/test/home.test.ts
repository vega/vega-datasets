// The home page's copy states numbers, and its cards and chart come from the
// catalog: check the numbers, the filters, the README sections it quotes, and
// that the catalog chart compiles and draws a point per dataset.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import * as vega from 'vega';
import { compile, type TopLevelSpec } from 'vega-lite';
import { describe, expect, test } from 'vitest';
import { catalogSpec, toBrush } from '../src/lib/catalog-chart';
import { Catalog, GALLERIES, type Gallery } from '../src/lib/catalog';
import { expressionInterpreter } from 'vega-interpreter';
import { formatBytes } from '../src/lib/format';
import {
  baseMatches,
  chartRows,
  FORMAT_GROUPS,
  formatCounts,
  homeCounts,
  homeIndex,
  indexCatalog,
  isFiltered,
  listDatasets,
  NO_FILTERS,
  plainSummary,
  readmeSection,
  showcase,
  usageCount,
  usageTitle,
} from '../src/lib/home-model';
import { exampleCount, loadCatalog, REPO } from './catalog';

const catalog = loadCatalog();
const counts = homeCounts(catalog);

describe('counts the copy states', () => {
  test('datasets, and examples with and without data', () => {
    expect(counts.datasets).toBe(catalog.datasets.length);
    expect(counts.examples).toBe(catalog.examples.length);
    expect(counts.examplesWithData).toBeLessThan(counts.examples);
    expect(counts.examplesWithData).toBe(new Set(catalog.datasets.flatMap((d) => d.usedBy)).size);
  });

  test('format groups cover every dataset', () => {
    expect(FORMAT_GROUPS.reduce((s, g) => s + counts.formats[g], 0)).toBe(counts.datasets);
  });

  test('each gallery counts the datasets it uses', () => {
    for (const g of ['vega', 'vega-lite', 'altair'] as const) {
      expect(counts.galleries[g]).toBe(catalog.datasets.filter((d) => catalog.usage(d)[g] > 0).length);
    }
  });
});

describe('the card list', () => {
  test('lists everything, most used first, ties A to Z', () => {
    const list = listDatasets(catalog, NO_FILTERS);
    expect(list).toHaveLength(counts.datasets);
    for (let i = 1; i < list.length; i++) {
      const [a, b] = [list[i - 1]!, list[i]!];
      expect(a.usedBy.length > b.usedBy.length || (a.usedBy.length === b.usedBy.length && a.name < b.name)).toBe(true);
    }
  });

  test('sorts A to Z and by size', () => {
    const az = listDatasets(catalog, { ...NO_FILTERS, sort: 'az' }).map((d) => d.name);
    expect(az).toEqual(catalog.datasets.map((d) => d.name));
    const sizes = listDatasets(catalog, { ...NO_FILTERS, sort: 'size' }).map((d) => d.bytes ?? 0);
    expect(sizes).toEqual([...sizes].sort((a, b) => b - a));
  });

  test('search matches names, field names and descriptions', () => {
    const q = (query: string) => listDatasets(catalog, { ...NO_FILTERS, query }).map((d) => d.name);
    expect(q('CARS')).toContain('cars');
    expect(q('Miles_per_Gallon')).toContain('cars');
    expect(q('penguin')).toContain('penguins');
    expect(q('no dataset has this')).toEqual([]);
  });

  test('formats filter datasets while galleries only change their usage counts', () => {
    const topo = listDatasets(catalog, { ...NO_FILTERS, formats: new Set(['TopoJSON']) });
    expect(topo).toHaveLength(counts.formats.TopoJSON);
    const either = listDatasets(catalog, { ...NO_FILTERS, formats: new Set(['TopoJSON', 'CSV']) });
    expect(either).toHaveLength(counts.formats.TopoJSON + counts.formats.CSV);
    const vega = listDatasets(catalog, { ...NO_FILTERS, galleries: new Set(['vega']) });
    expect(vega).toHaveLength(counts.datasets);
    const both = listDatasets(catalog, { ...NO_FILTERS, formats: new Set(['TopoJSON']), galleries: new Set(['vega']) });
    expect(both).toHaveLength(counts.formats.TopoJSON);
    expect(both.every((d) => d.format === 'topojson')).toBe(true);
    expect(isFiltered({ ...NO_FILTERS, galleries: new Set(['vega']) })).toBe(false);
    expect(listDatasets(catalog, { ...NO_FILTERS, query: 'birdstrikes', galleries: new Set(['vega']) }).map((d) => d.name)).toContain('birdstrikes');
  });

  test('selecting every gallery keeps the same datasets and ranking as selecting none', () => {
    expect(listDatasets(catalog, { ...NO_FILTERS, galleries: new Set(GALLERIES) })).toEqual(listDatasets(catalog, NO_FILTERS));
    expect(catalog.datasets.some((d) => d.usedBy.length === 0)).toBe(true);
  });

  test('the chart brush keeps datasets inside it, in either drag direction', () => {
    const cars = catalog.dataset('cars')!;
    const uses = exampleCount(catalog, 'cars');
    const around = { bytes: [cars.bytes! * 1.1, cars.bytes! * 0.9] as [number, number], examples: [uses + 1, uses - 1] as [number, number] };
    const list = listDatasets(catalog, { ...NO_FILTERS, brush: around }).map((d) => d.name);
    expect(list).toContain('cars');
    expect(list.every((name) => Math.abs(exampleCount(catalog, name) - uses) <= 1)).toBe(true);
  });
});

test('the chart matches follow search and chips, never the brush', () => {
  const brush = { bytes: [1, 2] as [number, number], examples: [0, 0] as [number, number] };
  const topo = { ...NO_FILTERS, formats: new Set(['TopoJSON'] as const), brush };
  expect(listDatasets(catalog, topo)).toEqual([]);
  expect(baseMatches(catalog, topo)).toHaveLength(counts.formats.TopoJSON);
});

test('card summaries are the first paragraph as plain text', () => {
  expect(plainSummary('A [TopoJSON](https://x) map with `code` and **bold**.\n\nMore.')).toBe('A TopoJSON map with code and bold.');
  expect(plainSummary('Wrapped\nline.')).toBe('Wrapped line.');
});

test('the showcase mixes all three galleries without repeats', () => {
  const picks = showcase(catalog).map((p) => p.example);
  expect(picks).toHaveLength(10);
  expect(new Set(picks.map((e) => e.id)).size).toBe(10);
  expect(new Set(picks.map((e) => e.gallery)).size).toBe(3);
  expect(picks.every((e) => e.thumb && e.thumbSize && e.thumbSize.every((size) => size > 0))).toBe(true);
});

test('each showcase thumbnail stands for a different dataset that its example uses', () => {
  const picks = showcase(catalog);
  expect(new Set(picks.map((p) => p.dataset)).size).toBe(10);
  for (const { example, dataset } of picks) {
    const d = catalog.datasets.find((x) => x.name === dataset);
    expect(d, dataset).toBeTruthy();
    expect(catalog.examplesFor(d!).map((e) => e.id)).toContain(example.id);
  }
});

test('a missing featured thumbnail falls back to another example of the same dataset', () => {
  const first = showcase(catalog)[0]!;
  const degraded = new Catalog({ ...catalog, examples: catalog.examples.map((e) => e.id === first.example.id ? { ...e, thumb: null } : e) });
  const replacement = showcase(degraded).find((p) => p.dataset === first.dataset)!;
  expect(replacement.example.id).not.toBe(first.example.id);
  expect(replacement.example.thumb).toBeTruthy();
  expect(replacement.example.datasets).toContain(first.dataset);
});

test('unavailable datasets and examples never produce broken showcase tiles', () => {
  const first = showcase(catalog)[0]!;
  const missingDataset = new Catalog({ ...catalog, datasets: catalog.datasets.filter((d) => d.name !== first.dataset) });
  expect(showcase(missingDataset).some((p) => p.dataset === first.dataset)).toBe(false);
  const missingThumbnails = new Catalog({ ...catalog, examples: catalog.examples.map((e) => ({ ...e, thumb: null })) });
  expect(showcase(missingThumbnails)).toEqual([]);
});

test('About quotes README sections that exist', () => {
  for (const heading of ['Dataset Information', 'Versioning', 'Data Usage Note', 'Example Galleries']) {
    const body = readmeSection(catalog.readme, heading);
    expect(body, heading).toBeTruthy();
    expect(body).not.toMatch(/^## /m);
  }
  expect(readmeSection(catalog.readme, 'No such heading')).toBeNull();
});

test('links to README sections use anchors GitHub gives its headings', () => {
  // GitHub's slug: lowercase, punctuation other than - and _ dropped, spaces to hyphens.
  const slug = (heading: string) => heading.trim().toLowerCase().replace(/[^\w\- ]/g, '').replace(/ /g, '-');
  const readme = readFileSync(path.join(REPO, 'README.md'), 'utf8');
  const anchors = new Set([...readme.matchAll(/^#{1,6} (.+)$/gm)].map((m) => slug(m[1]!)));
  const source = readFileSync(path.join(REPO, 'site', 'src', 'pages', 'index.astro'), 'utf8');
  const used = [...source.matchAll(/`\$\{REPO\}#([^`]+)`/g)].map((m) => m[1]!);
  expect(used.length).toBeGreaterThanOrEqual(4);
  expect(used.filter((a) => !anchors.has(a))).toEqual([]);
});

describe('the catalog chart', () => {
  const rows = chartRows(catalog, formatBytes);
  const options = { brush: true, height: 240, labels: 9, monoFont: 'monospace' };

  test('has a row per dataset, linking to its page', () => {
    expect(rows).toHaveLength(counts.datasets);
    expect(rows.every((r) => r.href === `datasets/${encodeURIComponent(r.name)}/` && r.bytes > 0)).toBe(true);
  });

  test.each([
    ['wide, with brush', options],
    ['phone, tap only', { ...options, brush: false, height: 214, labels: 5 }],
    ['standalone export', { ...options, legend: true }],
  ])('%s: compiles without warnings and draws every point', async (_name, o) => {
    const warnings: string[] = [];
    const logger = {
      level: () => logger,
      error: (...m: unknown[]) => { throw new Error(m.join(' ')); },
      warn: (...m: unknown[]) => { warnings.push(m.join(' ')); return logger; },
      info: () => logger,
      debug: () => logger,
    };
    const spec = { ...catalogSpec(rows, o), width: 800 };
    const { spec: vgSpec } = compile(spec as TopLevelSpec, { logger: logger as never });
    expect(warnings).toEqual([]);
    const view = new vega.View(vega.parse(vgSpec), { renderer: 'none' });
    try {
      await view.runAsync();
      const svg = await view.toSVG();
      expect(svg.match(/<path [^>]*class="[^"]*"|<path\b/g)?.length ?? 0).toBeGreaterThan(rows.length);
      expect(svg).not.toMatch(/NaN|undefined/);
      expect(svg.includes('role-legend')).toBe('legend' in o && o.legend === true);
      expect(svg).toContain(`cars: JSON, 100 KB, Gallery examples: ${exampleCount(catalog, 'cars')}`);
      expect(svg).toContain('(square root scale)');
      expect(svg).toContain('10 MB');
      // Counts remain in data units: the native scale spaces a quarter of the domain halfway up.
      const y = view.scale('y');
      const [lo, hi] = y.domain();
      const [bottom, top] = y.range();
      expect(lo).toBe(0);
      expect(y(0)).toBe(bottom);
      expect(y(hi / 4)).toBeCloseTo((bottom + top) / 2);
      const labels = [...svg.matchAll(/<text[^>]*font-family="monospace"[^>]*>([^<]+)<\/text>/g)].map((m) => m[1]);
      expect(labels.length).toBeLessThanOrEqual(o.labels);
      expect(labels).toContain('cars');
    } finally {
      view.finalize();
    }
  });

  test('filters fade the points they exclude, and the axes stay put', async () => {
    const view = new vega.View(vega.parse(compile({ ...catalogSpec(rows, options), width: 800 } as TopLevelSpec).spec), { renderer: 'none' });
    try {
      await view.runAsync();
      const ticks = (svg: string) => [...svg.matchAll(/<text[^>]*>([\d.,]+(?: [KM]?B)?)<\/text>/g)].map((m) => m[1]).join('|');
      const faded = (svg: string) => (svg.match(/<path[^>]*opacity="0\.1"/g) ?? []).length;
      const before = await view.toSVG();
      expect(faded(before)).toBe(0);
      await view.signal('matched', ['cars', 'movies']).runAsync();
      const after = await view.toSVG();
      expect(faded(after)).toBe(rows.length - 2);
      expect(ticks(after)).toBe(ticks(before));
      await view.signal('matched', null).runAsync();
      expect(faded(await view.toSVG())).toBe(0);
    } finally {
      view.finalize();
    }
  });

  test('reads the brush signal, and treats a cleared brush as none', () => {
    expect(toBrush({ bytes: [1, 2], examples: [3, 4] })).toEqual({ bytes: [1, 2], examples: [3, 4] });
    expect(toBrush({})).toBeNull();
    expect(toBrush(null)).toBeNull();
  });

  const selections: Gallery[][] = [[], ['vega'], ['vega-lite'], ['altair'], ['vega-lite', 'vega'], ['vega', 'altair'], ['vega-lite', 'altair'], [...GALLERIES]];

  test.each([
    [288, 214, false, 5], [358, 214, false, 5], [398, 214, false, 5], [608, 214, false, 5],
    [563, 128, true, 9], [722, 165, true, 9], [1242, 283, true, 9],
  ] as const)('labels stay apart at width %i and height %i (brush=%s, limit=%i)', async (width, height, brush, limit) => {
    const compiled = compile({ ...catalogSpec(rows, { ...options, brush, height, labels: limit }), width, autosize: { type: 'fit', contains: 'padding' } } as TopLevelSpec).spec;
    const view = new vega.View(vega.parse(compiled, {}, { ast: true }), { renderer: 'none', expr: expressionInterpreter });
    type Item = { text?: string; font?: string; bounds: { x1: number; x2: number; y1: number; y2: number }; items?: Item[] };
    const textItems = (item: Item): Item[] => [
      ...(item.font === 'monospace' && item.text ? [item] : []),
      ...(item.items ?? []).flatMap(textItems),
    ];
    try {
      for (const selected of [...selections, []]) {
        await view.signal('galleries', selected).runAsync();
        const labels = textItems(view.scenegraph().root as unknown as Item);
        expect(labels.length).toBeGreaterThan(0);
        expect(labels.length).toBeLessThanOrEqual(limit);
        for (let i = 0; i < labels.length; i++) {
          for (const other of labels.slice(i + 1)) {
            const a = labels[i]!.bounds, b = other.bounds;
            const overlaps = a.x1 < b.x2 && a.x2 > b.x1 && a.y1 < b.y2 && a.y2 > b.y1;
            expect(overlaps, `${selected}: ${labels[i]!.text} / ${other.text}`).toBe(false);
          }
        }
        // Omitting a crowded label must never omit its point or dataset link.
        const svg = await view.toSVG();
        expect((svg.match(/aria-roledescription="circle"/g) ?? []).length).toBe(rows.length);
      }
    } finally { view.finalize(); }
  });

  test('Vega recounts and ranks every dataset including zeros for every gallery combination under CSP', async () => {
    const compiled = compile({ ...catalogSpec(rows, options), width: 800 } as TopLevelSpec).spec;
    const view = new vega.View(vega.parse(compiled, {}, { ast: true }), { renderer: 'none', expr: expressionInterpreter });
    try {
      // Reverse as well: returning to all galleries must recover the original totals.
      for (const selected of [...selections, ...selections.toReversed()]) {
        await view.signal('galleries', selected).runAsync();
        const svg = await view.toSVG();
        const galleries = new Set(selected);
        const listed = listDatasets(catalog, { ...NO_FILTERS, galleries });
        expect(listed).toHaveLength(counts.datasets);
        const values = listed.map((d) => usageCount(catalog, d, galleries));
        expect(values).toEqual([...values].sort((a, b) => b - a));
        for (const d of catalog.datasets) {
          const n = selected.length ? catalog.examplesFor(d).filter((e) => selected.includes(e.gallery)).length : d.usedBy.length;
          expect(usageCount(catalog, d, galleries)).toBe(n);
          const description = `aria-label="${d.name}: `;
          expect(svg).toContain(`${description}${rows.find((r) => r.name === d.name)!.format}, ${formatBytes(d.bytes)}, ${usageTitle(galleries)}: ${n}"`);
        }
        expect(svg).not.toMatch(/NaN|undefined/);
        expect(svg).toContain(usageTitle(galleries));
        const labels = [...svg.matchAll(/<text[^>]*font-family="monospace"[^>]*>([^<]+)<\/text>/g)].map((m) => m[1]);
        const leading = listed.slice(0, options.labels).map((d) => d.name);
        expect(labels).toContain(leading[0]);
        for (const name of labels) expect(leading).toContain(name);
      }
    } finally { view.finalize(); }
  });

  test('standalone charts restore gallery counts, the legend and native brush without page controls', async () => {
    const uses = exampleCount(catalog, 'cars', ['vega']);
    const initialBrush = { bytes: [50_000, 150_000] as [number, number], examples: [uses - 1, uses + 1] as [number, number] };
    const compiled = compile({ ...catalogSpec(rows, { ...options, galleries: ['vega'], initialBrush, legend: true }), width: 800 } as TopLevelSpec).spec;
    const view = new vega.View(vega.parse(compiled), { renderer: 'none' });
    try {
      await view.runAsync();
      const brush = toBrush(view.signal('brush'))!;
      expect(brush.bytes[0]).toBeCloseTo(initialBrush.bytes[0]);
      expect(brush.bytes[1]).toBeCloseTo(initialBrush.bytes[1]);
      expect(brush.examples[0]).toBeCloseTo(initialBrush.examples[0]);
      expect(brush.examples[1]).toBeCloseTo(initialBrush.examples[1]);
      await view.signal('matched', ['cars']).runAsync();
      expect(toBrush(view.signal('brush'))).toEqual(brush);
      expect(await view.toSVG()).toContain(`cars: JSON, 100 KB, Vega examples: ${uses}`);
      const svg = await view.toSVG();
      expect(svg).toContain('role-legend');
      expect(svg).toContain('(square root scale)');
      expect(svg).toContain('birdstrikes: CSV, 1.2 MB, Vega examples: 0');
    } finally { view.finalize(); }
  });

  test('brush filtering uses the selected galleries count, not the lifetime total', () => {
    const cars = catalog.dataset('cars')!;
    const uses = exampleCount(catalog, 'cars', ['vega']);
    const filters = { ...NO_FILTERS, galleries: new Set<Gallery>(['vega']), brush: { bytes: [cars.bytes! - 1, cars.bytes! + 1] as [number, number], examples: [uses - 1, uses + 1] as [number, number] } };
    expect(listDatasets(catalog, filters).map((d) => d.name)).toContain('cars');
    expect(listDatasets(catalog, { ...filters, galleries: new Set() }).map((d) => d.name)).not.toContain('cars');
  });

  test('brushing the zero baseline finds every dataset unused by the selected gallery', () => {
    const filters = { ...NO_FILTERS, galleries: new Set<Gallery>(['vega']), brush: { bytes: [50, 2e7] as [number, number], examples: [0, 0] as [number, number] } };
    const unused = listDatasets(catalog, filters);
    expect(unused.length).toBe(counts.datasets - counts.galleries.vega);
    expect(unused.every((d) => catalog.usage(d).vega === 0)).toBe(true);
  });
});

test('the home page index (home-index.json) lists, counts and charts like the full catalog', () => {
  const index = indexCatalog(JSON.parse(JSON.stringify(homeIndex(catalog))));
  const names = (c: typeof catalog, f: Parameters<typeof listDatasets>[1]) => listDatasets(c, f).map((d) => d.name);
  for (const f of [
    NO_FILTERS,
    { ...NO_FILTERS, query: 'weather' },
    { ...NO_FILTERS, query: 'Miles_per_Gallon' },
    { ...NO_FILTERS, formats: new Set(['CSV', 'TopoJSON'] as const), sort: 'size' as const },
    { ...NO_FILTERS, galleries: new Set(['altair'] as const), sort: 'az' as const },
  ]) {
    expect(names(index, f)).toEqual(names(catalog, f));
  }
  expect(formatCounts(index)).toEqual(counts.formats);
  expect(chartRows(index, formatBytes)).toEqual(chartRows(catalog, formatBytes));
  for (const d of catalog.datasets) expect(index.usage(index.dataset(d.name)!)).toEqual(catalog.usage(d));
});

test('legacy #name links name a dataset; About anchors and unknown names do not', async () => {
  const { legacyDataset } = await import('../src/lib/home-model');
  const names = new Set(['cars', 'us_10m', 'weather']);
  expect(legacyDataset('#cars', names)).toBe('cars');
  expect(legacyDataset('#us_10m', names)).toBe('us_10m');
  expect(legacyDataset('#about-versioning', names)).toBeNull();
  expect(legacyDataset('#browse', names)).toBeNull();
  expect(legacyDataset('', names)).toBeNull();
  expect(legacyDataset('#', names)).toBeNull();
  expect(legacyDataset('#%E0', names)).toBeNull();
  expect(legacyDataset('#c%61rs', names)).toBe('cars');
});
