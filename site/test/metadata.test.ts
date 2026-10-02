// A fully described dataset (test/fixtures.ts) shows every standard property it fills in:
// titles on axes, legends, tooltips and pickers; ordered categories in their order and
// with their labels; documented ranges as axis bounds (only when every value is inside);
// and, in the fields table's text, ranges, values, rules, keys, joins and formats. The
// charts are drawn the way the page draws them (the expression interpreter, no eval).
import { describe, expect, test } from 'vitest';
import { Catalog, type CatalogFile, categoryLabels, type Dataset, documentedRange, fieldTitle, joins, missingMarkers, orderedCategories, primaryKey } from '../src/lib/catalog';
import { defaultAxes, scatterFields, scatterSpec } from '../src/lib/explore-model';
import { fieldNotes, formatNote, isKey, missingNote } from '../src/lib/field-meta';
import { homeIndex, listDatasets, NO_FILTERS } from '../src/lib/home-model';
import { densityPageSpec, densitySpec, type DensityGrid } from '../src/lib/large-data';
import { datasetMetaDescription } from '../src/lib/seo';
import { starterSpec } from '../src/lib/starter';
import { draw as drawRows } from './draw';
import { described, only, ROWS, strip } from './fixtures';

type Spec = Record<string, unknown>;
type Enc = Record<string, Record<string, unknown>>;

const d = described();
const field = (name: string) => d.fields.find((f) => f.name === name)!;
const enc = (spec: Spec | null) => (spec as { encoding: Enc }).encoding;

const GRADE_LABELS = 'indexof(["v:low","v:mid","v:high"], "v:" + datum.label) < 0 ? datum.label : slice(["v:Low","v:Medium","v:High"][indexof(["v:low","v:mid","v:high"], "v:" + datum.label)], 2)';
const draw = (spec: Spec, signals: Record<string, unknown> = {}) => drawRows(spec, ROWS, signals);

describe('catalog helpers normalize the Table Schema forms', () => {
  test('titles, categories, ranges and keys', () => {
    expect(fieldTitle(field('hp'))).toBe('Horsepower (hp)');
    expect(fieldTitle(field('parent'))).toBe('parent');
    expect(orderedCategories(field('grade'))).toEqual(['low', 'mid', 'high']);
    expect(orderedCategories(field('side'))).toBeNull();
    expect(categoryLabels(field('grade'))).toEqual([['low', 'Low'], ['mid', 'Medium'], ['high', 'High']]);
    expect(categoryLabels(field('side'))).toBeNull();
    expect(documentedRange(field('hp'))).toEqual({ min: 0, max: 500, fits: true });
    expect(documentedRange(field('mpg'))).toEqual({ min: 0, max: 40, fits: false });
    expect(documentedRange(field('id'))).toBeNull();
    expect(primaryKey(d)).toEqual(['id']);
    expect(primaryKey({ ...d, primaryKey: ['id', 'when'] })).toEqual(['id', 'when']);
    expect(primaryKey(strip(d))).toEqual([]);
    expect(missingMarkers([{ value: '-', label: 'Not asked' }])).toEqual(['-']);
  });

  test('foreign keys: string or array fields; no resource, or "", is the table itself', () => {
    expect(joins(d)).toEqual([
      { fields: ['parent'], resource: 'fixture', referenceFields: ['id'], self: true },
      { fields: ['origin'], resource: 'origins', referenceFields: ['name'], self: false },
    ]);
    expect(joins({ ...d, foreignKeys: [{ fields: 'parent', reference: { fields: 'id' } }] })[0]!.self).toBe(true);
    expect(joins(strip(d))).toEqual([]);
  });
});

describe('starter charts', () => {
  test('a scatter plot: titled axes, the documented range that fits, colors in order and labeled', () => {
    const e = enc(starterSpec(only(d, ['hp', 'mpg', 'grade', 'side'])));
    expect(e.x).toEqual({ field: 'hp', type: 'quantitative', scale: { zero: false, domainMin: 0, domainMax: 500 }, title: 'Horsepower (hp)' });
    // Documented as at most 40, but a value is 46.6: the data's own extent stays.
    expect(e.y).toEqual({ field: 'mpg', type: 'quantitative', scale: { zero: false }, title: 'Miles per Gallon' });
    expect(e.color).toEqual({
      field: 'grade', type: 'nominal', sort: ['low', 'mid', 'high'], title: 'Trim Grade',
      legend: { labelExpr: GRADE_LABELS },
    });
  });

  test('unordered plain categories change nothing', () => {
    const plain = only(d, ['hp', 'mpg', 'side']);
    expect(enc(starterSpec(plain)).color).toEqual({ field: 'side', type: 'nominal' });
    expect(enc(starterSpec(plain)).color).toEqual(enc(starterSpec(strip(plain))).color);
  });

  test('bars follow the documented order instead of sorting by value', () => {
    const e = enc(starterSpec(only(d, ['grade', 'hp'])));
    expect(e.y).toEqual({
      field: 'grade', type: 'ordinal', sort: ['low', 'mid', 'high'], title: 'Trim Grade',
      axis: { labelExpr: GRADE_LABELS },
    });
    expect(e.x).toEqual({ field: 'hp', type: 'quantitative', aggregate: 'mean', scale: { domainMin: 0, domainMax: 500 }, title: 'Mean of Horsepower (hp)' });
    expect(enc(starterSpec(only(strip(d), ['grade', 'hp']))).y).toEqual({ field: 'grade', type: 'nominal', sort: '-x' });
  });

  test('a histogram bins over the documented range', () => {
    expect(enc(starterSpec(only(d, ['hp']))).x).toEqual({ field: 'hp', type: 'quantitative', bin: { maxbins: 30, extent: [0, 500] }, title: 'Horsepower (hp)' });
  });

  test('a time series titles its axes, and a series without metadata stays nominal', () => {
    const e = enc(starterSpec(d));
    expect(e.x).toEqual({ field: 'when', type: 'temporal', title: 'Date Sold' });
    expect(e.y).toEqual({ field: 'hp', type: 'quantitative', aggregate: 'mean', scale: { domainMin: 0, domainMax: 500 }, title: 'Mean of Horsepower (hp)' });
    expect(e.color).toEqual({ field: 'origin', type: 'nominal' });
  });

  test('they draw with the interpreter: bounds, order and labels reach the view', async () => {
    const scatter = await draw(starterSpec(only(d, ['hp', 'mpg', 'grade']))!);
    try {
      expect(scatter.scale('x').domain()).toEqual([0, 500]);
      expect(scatter.scale('color').domain()).toEqual(['low', 'mid', 'high']);
      const svg = await scatter.toSVG();
      for (const text of ['Horsepower (hp)', 'Miles per Gallon', 'Trim Grade', 'Low', 'Medium', 'High']) expect(svg).toContain(`>${text}<`);
    } finally {
      scatter.finalize();
    }
    const bars = await draw(starterSpec(only(d, ['grade', 'hp']))!);
    try {
      expect(bars.scale('y').domain()).toEqual(['low', 'mid', 'high']);
      expect(bars.scale('x').domain()).toEqual([0, 500]);
      expect(await bars.toSVG()).toContain('>Medium<');
    } finally {
      bars.finalize();
    }
  });
});

describe('Explore scatter plot', () => {
  const sf = scatterFields(d)!;
  const spec = scatterSpec(d, sf, { ...defaultAxes(sf), zoom: true, height: 380 });
  const params = spec.params as { name: string; bind: { labels?: string[]; options: string[] } }[];

  test('the pickers show the titles; the values stay field names', () => {
    expect(params[0]!.bind.options).toEqual(['hp', 'mpg']);
    expect(params[0]!.bind.labels).toEqual(['Horsepower (hp)', 'Miles per Gallon']);
  });

  test('without titles or ranges the spec is the one an undescribed dataset gets', () => {
    const bare = strip(d);
    const bf = scatterFields(bare)!;
    const plain = JSON.stringify(scatterSpec(bare, bf, { ...defaultAxes(bf), zoom: true, height: 380 }));
    expect(plain).not.toMatch(/labels|domainMin|domainMax|labelExpr|Horsepower|ordinal|"sort"/);
  });

  test('axis titles, bounds for the picked field, and the ordered legend, drawn with the interpreter', async () => {
    const view = await draw(spec);
    try {
      // x is mpg (no bounds: a value lies outside its documented range), y is hp.
      expect(view.scale('y').domain()).toEqual([0, 500]);
      expect(view.scale('x').domain()[1]).toBeGreaterThan(40);
      expect(view.scale('color').domain()).toEqual(['low', 'mid', 'high']);
      let svg = await view.toSVG();
      for (const text of ['Horsepower (hp)', 'Miles per Gallon', 'Trim Grade', 'Medium']) expect(svg).toContain(`>${text}<`);
      view.signal('xField', 'hp').signal('yField', 'mpg');
      await view.runAsync();
      expect(view.scale('x').domain()).toEqual([0, 500]);
      svg = await view.toSVG();
      expect(svg).toContain('>Horsepower (hp)<');
    } finally {
      view.finalize();
    }
  });

  test('tooltips title the category, label and time fields', () => {
    const tooltip = (spec.layer as { encoding: { tooltip: Record<string, unknown>[] } }[])[0]!.encoding.tooltip;
    expect(tooltip.map((t) => t.title)).toEqual(['x', 'y', 'Trim Grade', 'Date Sold']);
  });
});

test('the density overview titles its axes and tooltip with the field titles', () => {
  const g: DensityGrid = {
    x: 'mpg', y: 'hp', rows: 5, complete: 5, outside: 0, box: { x: [12, 46.6], y: [46, 230] },
    xstart: 10, xstep: 10, nx: 4, ystart: 0, ystep: 50, ny: 5, cells: [[0, 0, 1]],
  };
  for (const spec of [densitySpec(d, g, 300), densityPageSpec(d, g, 300)]) {
    const e = enc(spec);
    expect([e.x!.title, e.y!.title]).toEqual(['Miles per Gallon', 'Horsepower (hp)']);
  }
  const tips = enc(densityPageSpec(d, g, 300)).tooltip as unknown as { title: string }[];
  expect(tips.map((t) => t.title)).toEqual(['Miles per Gallon', 'Horsepower (hp)', 'Rows']);
});

describe('fields table text', () => {
  test('ranges, values, rules and missing markers, quietly', () => {
    expect(fieldNotes(field('hp'))).toEqual(['Documented range 0 – 500', 'Counted as missing: -99']);
    expect(fieldNotes(field('mpg'))).toEqual(['Documented range 0 – 40 (some values fall outside)']);
    expect(fieldNotes(field('grade'))).toEqual(['Values, in order: low (Low), mid (Medium), high (High)']);
    expect(fieldNotes(field('side'))).toEqual(['Values: left, right']);
    // A label that only repeats its value isn't shown twice.
    expect(fieldNotes({ ...field('side'), categories: [{ value: 'left', label: 'left' }, { value: 'right', label: 'Right side' }] })).toEqual(['Values: left, right (Right side)']);
    expect(fieldNotes(field('origin'))).toEqual(['Allowed values: usa, japan, europe']);
    expect(fieldNotes(field('id'))).toEqual(['Required', 'Unique']);
    expect(fieldNotes({ ...field('hp'), constraints: { minimum: 0 }, missingValues: [''] })).toEqual(['Documented minimum 0', 'Counted as missing: empty']);
    expect(fieldNotes({ ...field('origin'), constraints: { enum: Array.from({ length: 15 }, (_, i) => `v${i}`) } })).toEqual([
      'Allowed values: v0, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11 and 3 more',
    ]);
    for (const f of strip(d).fields) expect(fieldNotes(f), f.name).toEqual([]);
  });

  test('formats, keys and the schema’s missing markers', () => {
    expect(formatNote(field('when'))).toBe('%Y/%m/%d');
    expect(formatNote({ ...field('when'), format: 'default' })).toBeNull();
    expect(formatNote(field('hp'))).toBeNull();
    expect(d.fields.filter((f) => isKey(d, f)).map((f) => f.name)).toEqual(['id']);
    // hp lists its own markers.
    expect(missingNote(d)).toBe('Empty cells and “NA” count as missing, except in fields that list their own markers.');
    expect(missingNote({ ...d, missingValues: ['NA'] })).toBe('“NA” counts as missing, except in fields that list their own markers.');
    expect(missingNote({ ...d, missingValues: [''] })).toBeNull();
    expect(missingNote(strip(d))).toBeNull();
  });
});

describe('the dataset title', () => {
  test('leads the meta description; the description alone without one', () => {
    expect(datasetMetaDescription(d)).toBe('Five cars, fully described. A small table for testing.');
    expect(datasetMetaDescription(strip(d))).toBe('A small table for testing.');
    expect(datasetMetaDescription({ ...strip(d), description: '' })).toBe('fixture from vega-datasets.');
  });

  test('home search matches it, and the home index carries it only when present', () => {
    const catalog = new Catalog({ package: { name: 'x', version: '1', commit: 'c' }, readme: '', datasets: [d, { ...strip(d), name: 'plain' }], examples: [] } as CatalogFile);
    expect(listDatasets(catalog, { ...NO_FILTERS, query: 'fully described' }).map((x: Dataset) => x.name)).toEqual(['fixture']);
    const index = homeIndex(catalog).datasets;
    expect(index.map((x) => x.title)).toEqual(['Five cars, fully described', undefined]);
    expect(Object.keys(index[0]!)).toEqual(['name', 'format', 'kind', 'bytes', 'rows', 'title', 'description', 'usedBy', 'fields']);
    expect('title' in index[1]!).toBe(false);
  });
});
