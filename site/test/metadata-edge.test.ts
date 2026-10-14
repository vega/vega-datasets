// Edge cases of the metadata rendering, covering category
// values that are also JavaScript property names, missing-value markers in charts, range
// bounds that must not leak into bars or other measures, date ranges, integer categories,
// the constraints the fields table lists, its missing-values footer, and literal titles.
import { describe, expect, test } from 'vitest';
import { type Dataset, type Field, insideDocumented } from '../src/lib/catalog';
import { defaultAxes, scatterFields, scatterSpec } from '../src/lib/explore-model';
import { fieldNotes, missingNote } from '../src/lib/field-meta';
import { densityGrid } from '../src/lib/large-data';
import { datasetMetaDescription } from '../src/lib/seo';
import { starterSpec } from '../src/lib/starter';
import { draw, rowsWith } from './draw';
import { described, strip } from './fixtures';

type Spec = Record<string, unknown>;
type Enc = Record<string, Record<string, unknown>>;

const enc = (spec: Spec | null) => (spec as { encoding: Enc }).encoding;
const quant = (min: number, max: number, extra: Partial<Field> = {}): Field => ({
  name: 'v', type: 'number', description: null, profile: { kind: 'quantitative', min, max, mean: (min + max) / 2, missing: 0, bins: [1, 1] }, ...extra,
});
const nominal = (name: string, values: string[], extra: Partial<Field> = {}): Field => ({
  name, type: 'string', description: null, profile: { kind: 'nominal', distinct: values.length, top: values.map((v) => [v, 1]), missing: 0 }, ...extra,
});
/** A bare table of these fields (no dataset-level metadata). */
const table = (fields: Field[], extra: Partial<Dataset> = {}): Dataset => ({ ...strip(described()), fields, ...extra });

describe('category labels', () => {
  test('any value, even a JavaScript property name, gets its label (interpreter-safe)', async () => {
    const values = ['toString', '__proto__', 'constructor', 'x'];
    const labels = ['Method', 'Proto', 'Maker', 'Ex'];
    const kind = nominal('kind', values, { categories: values.map((value, i) => ({ value, label: labels[i] })) });
    const spec = starterSpec(table([kind, quant(1, 4)]))!;
    const view = await draw(spec, values.map((kind, i) => ({ kind, v: i + 1 })));
    try {
      const svg = await view.toSVG();
      for (const label of labels) expect(svg).toContain(`>${label}<`);
    } finally {
      view.finalize();
    }
  });
});

describe('missing-value markers are missing in charts too', () => {
  const hp = quant(100, 200, { name: 'hp', missingValues: ['-99'] });
  const rows = [{ c: 'a', hp: 100 }, { c: 'a', hp: -99 }, { c: 'b', hp: 200 }, { c: 'b', hp: '-99' }];

  test('a mean by category leaves them out', async () => {
    const view = await draw(starterSpec(table([nominal('c', ['a', 'b']), hp]))!, rows);
    try {
      expect(rowsWith(view, 'mean_hp').map((r) => [r.c, r.mean_hp])).toEqual([['a', 100], ['b', 200]]);
    } finally {
      view.finalize();
    }
  });

  test('the schema’s markers apply to fields without their own; a category marker drops its bar', async () => {
    const d = table([nominal('c', ['a', 'b', 'NA']), quant(100, 200, { name: 'hp' })], { missingValues: ['NA'] });
    const view = await draw(starterSpec(d)!, [...rows.slice(0, 1), { c: 'NA', hp: 150 }, rows[2]!]);
    try {
      expect(rowsWith(view, 'mean_hp').map((r) => r.c)).toEqual(['a', 'b']);
    } finally {
      view.finalize();
    }
  });

  test('the Explore scatter plot leaves them out of the picked measures', async () => {
    const d = table([hp, quant(10, 40, { name: 'mpg' })]);
    const sf = scatterFields(d)!;
    const view = await draw(scatterSpec(d, sf, { x: 'hp', y: 'mpg', zoom: false, height: 300 }), [
      { hp: 100, mpg: 10 }, { hp: -99, mpg: 20 }, { hp: 200, mpg: 40 },
    ]);
    try {
      expect(view.scale('x').domain()[0]).toBeGreaterThan(0);
      view.signal('xField', 'mpg').signal('yField', 'hp');
      await view.runAsync();
      expect(view.scale('x').domain()[0]).toBeGreaterThan(0);
      expect(view.scale('y').domain()[0]).toBeGreaterThan(0);
    } finally {
      view.finalize();
    }
  });

  test('the density overview doesn’t bin them', () => {
    const rows = [{ a: '1', b: '2' }, { a: '-99', b: '3' }, { a: -99, b: 4 }, { a: '2', b: '5' }];
    expect(densityGrid(rows, 'a', 'b', { x: 10, y: 10 }).complete).toBe(4);
    const g = densityGrid(rows, 'a', 'b', { x: 10, y: 10 }, { x: ['-99'] });
    expect([g.rows, g.complete]).toEqual([4, 2]);
    expect(g.box.x[0]).toBeGreaterThan(0);
  });

  test('without declared markers the specs carry no filter', () => {
    const bare = table([nominal('c', ['a', 'b']), quant(100, 200, { name: 'hp' })]);
    expect(starterSpec(bare)).not.toHaveProperty('transform');
    const both = table([quant(100, 200, { name: 'hp' }), quant(10, 40, { name: 'mpg' })]);
    const sf = scatterFields(both)!;
    expect(JSON.stringify(scatterSpec(both, sf, { ...defaultAxes(sf), zoom: true, height: 300 }))).not.toContain('indexof');
  });
});

describe('documented ranges', () => {
  test('a positive minimum doesn’t push bars off the plot: bars keep their zero baseline', async () => {
    const hp = quant(46, 230, { name: 'hp', constraints: { minimum: 40, maximum: 500 } });
    const spec = starterSpec(table([nominal('c', ['a', 'b']), hp]))!;
    const view = await draw(spec, [{ c: 'a', hp: 46 }, { c: 'b', hp: 230 }]);
    try {
      expect(view.scale('x').domain()).toEqual([0, 500]);
    } finally {
      view.finalize();
    }
  });

  test('a bound on one measure leaves another measure’s axis as it was', async () => {
    const rows = [{ hp: 46, mpg: 12 }, { hp: 230, mpg: 46.6 }];
    const domains = async (d: Dataset) => {
      const sf = scatterFields(d)!;
      const view = await draw(scatterSpec(d, sf, { x: 'mpg', y: 'hp', zoom: true, height: 300 }), rows);
      try {
        return [view.scale('x').domain(), view.scale('y').domain()];
      } finally {
        view.finalize();
      }
    };
    const mpg = quant(12, 46.6, { name: 'mpg' });
    const [plainX] = await domains(table([quant(46, 230, { name: 'hp' }), mpg]));
    const [x, y] = await domains(table([quant(46, 230, { name: 'hp', constraints: { minimum: 0 } }), mpg]));
    expect(x).toEqual(plainX);
    expect(y![0]).toBe(0);
  });

  test('a one-sided bound leaves a histogram’s bins on the data (a bin extent needs both ends)', () => {
    for (const constraints of [{ minimum: 0 }, { maximum: 500 }]) {
      const x = enc(starterSpec(table([quant(46, 230, { constraints })]))).x!;
      expect(x).toEqual({ field: 'v', type: 'quantitative', bin: { maxbins: 30 } });
    }
  });

  test('date bounds are checked against the data like numbers', () => {
    const when: Field = {
      name: 'when', type: 'date', description: null, constraints: { minimum: '2020-01-01', maximum: '2020-12-31' },
      profile: { kind: 'temporal', min: '2019-06-01T00:00:00Z', max: '2021-02-01T00:00:00Z', missing: 0 },
    };
    expect(fieldNotes(when)).toEqual(['Documented range 2020-01-01 – 2020-12-31 (some values fall outside)']);
    const inside = { ...when, profile: { ...when.profile, min: '2020-01-01T00:00:00Z', max: '2020-12-31T00:00:00Z' } } as Field;
    expect(fieldNotes(inside)).toEqual(['Documented range 2020-01-01 – 2020-12-31']);
  });
});

describe('integer categories', () => {
  const grade: Field = {
    name: 'grade', type: 'integer', description: null,
    categories: [{ value: 1, label: 'Low' }, { value: 2, label: 'Mid' }, { value: 3, label: 'High' }],
    profile: { kind: 'quantitative', min: 1, max: 3, mean: 2, missing: 0, bins: [1, 1, 1] },
  };

  test('group a measure’s bars, labeled', async () => {
    const spec = starterSpec(table([grade, quant(46, 230)]))!;
    expect(enc(spec).y).toMatchObject({ field: 'grade', type: 'nominal' });
    const view = await draw(spec, [{ grade: 1, v: 46 }, { grade: 2, v: 100 }, { grade: 3, v: 230 }]);
    try {
      expect(await view.toSVG()).toContain('>Mid<');
    } finally {
      view.finalize();
    }
  });

  test('alone, are counted', () => {
    expect(enc(starterSpec(table([grade]))).y).toMatchObject({ field: 'grade', type: 'nominal' });
  });
});

describe('fields table text', () => {
  test('an allowed set narrower than the categories is listed too', () => {
    const f = nominal('c', ['a', 'b'], { categories: ['a', 'b'], constraints: { enum: ['a'] } });
    expect(fieldNotes(f)).toEqual(['Values: a, b', 'Allowed values: a']);
    // The same set isn't said twice.
    expect(fieldNotes({ ...f, constraints: { enum: ['b', 'a'] } })).toEqual(['Values: a, b']);
  });

  test('lengths, patterns and exclusive bounds', () => {
    expect(fieldNotes(nominal('c', ['AB'], { constraints: { minLength: 2, maxLength: 5, pattern: '^[A-Z]+$' } }))).toEqual([
      'Length 2 – 5 characters', 'Pattern ^[A-Z]+$',
    ]);
    expect(fieldNotes(nominal('c', ['AB'], { constraints: { minLength: 2 } }))).toEqual(['At least 2 characters']);
    expect(fieldNotes(nominal('c', ['AB'], { constraints: { maxLength: 1 } }))).toEqual(['At most 1 character']);
    expect(fieldNotes(quant(1, 2, { constraints: { exclusiveMinimum: 0, exclusiveMaximum: 10 } }))).toEqual(['Greater than 0', 'Less than 10']);
  });

  test('an empty list of its own says the field has no markers', () => {
    expect(fieldNotes(nominal('c', ['a'], { missingValues: [] }))).toEqual(['No missing-value markers']);
  });

  test('the footer names the schema’s markers only for the fields they apply to', () => {
    const own = nominal('c', ['NA'], { missingValues: [] });
    expect(missingNote(table([own], { missingValues: ['NA'] }))).toBeNull();
    expect(missingNote(table([own, nominal('d', ['x'])], { missingValues: ['NA'] }))).toBe('“NA” counts as missing, except in fields that list their own markers.');
    expect(missingNote(table([nominal('d', ['x'])], { missingValues: ['NA'] }))).toBe('“NA” counts as missing.');
  });
});

test('a title is plain text in the meta description, not Markdown', () => {
  expect(datasetMetaDescription({ ...described(), title: 'CO_2 *measurements*' })).toBe('CO_2 *measurements*. A small table for testing.');
  expect(datasetMetaDescription({ ...described(), description: 'A **bold** start.' })).toBe('Five cars, fully described. A bold start.');
});

test('bars with only a positive minimum documented encode as if undescribed', () => {
  const plain = starterSpec(table([nominal('c', ['a', 'b']), quant(46, 230, { name: 'hp' })]));
  expect(starterSpec(table([nominal('c', ['a', 'b']), quant(46, 230, { name: 'hp', constraints: { minimum: 40 } })]))).toEqual(plain);
});

describe('rounded profile extremes', () => {
  // The builder rounds min and max to four significant figures: 100.01–100.04 profiles as 100–100.
  const near = quant(100, 100, { constraints: { minimum: 0, maximum: 100 } });

  test('don’t prove a documented range fits: no bin extent that could drop every row', async () => {
    const spec = starterSpec(table([near]))!;
    expect(enc(spec).x).toEqual({ field: 'v', type: 'quantitative', bin: { maxbins: 30 } });
    const view = await draw(spec, [{ v: 100.01 }, { v: 100.02 }, { v: 100.04 }]);
    try {
      expect(rowsWith(view, '__count').reduce((n, r) => n + (r.__count as number), 0)).toBe(3);
    } finally {
      view.finalize();
    }
  });

  test('nor prove values fall outside', () => {
    expect(fieldNotes(near)).toEqual(['Documented range 0 – 100']);
    expect(fieldNotes(quant(100.1, 230, { constraints: { minimum: 0, maximum: 100 } }))).toEqual(['Documented range 0 – 100 (some values fall outside)']);
    // Clearly inside by more than the rounding: still bounded.
    expect(enc(starterSpec(table([quant(46, 99.5, { constraints: { minimum: 0, maximum: 100 } })]))).x!.bin).toEqual({ maxbins: 30, extent: [0, 100] });
  });
});

test('a text field’s markers match as text: "01" doesn’t make "1" missing', async () => {
  const kind = nominal('kind', ['01', '1', 'A'], { missingValues: ['01'] });
  const view = await draw(starterSpec(table([kind, quant(10, 30)]))!, [{ kind: '01', v: 10 }, { kind: '1', v: 20 }, { kind: 'A', v: 30 }]);
  try {
    expect(rowsWith(view, 'mean_v').map((r) => r.kind).sort()).toEqual(['1', 'A']);
  } finally {
    view.finalize();
  }
});

test('a date field’s markers leave the time series even though the dates are parsed first', async () => {
  const when: Field = {
    name: 'when', type: 'date', description: null, missingValues: ['1900-01-01'],
    profile: { kind: 'temporal', min: '2020-01-01T00:00:00Z', max: '2021-01-01T00:00:00Z', missing: 1 },
  };
  const view = await draw(starterSpec(table([when, quant(1, 3)]))!, [
    { when: '1900-01-01', v: 1 }, { when: '2020-01-01', v: 2 }, { when: '2021-01-01', v: 3 },
  ]);
  try {
    expect(new Date(view.scale('x').domain()[0]).getUTCFullYear()).toBe(2020);
  } finally {
    view.finalize();
  }
});

describe('integer categories', () => {
  const grade: Field = {
    name: 'grade', type: 'integer', description: null, categoriesOrdered: true,
    categories: [{ value: 3, label: 'High' }, { value: 1, label: 'Low' }, { value: 2, label: 'Mid' }],
    profile: { kind: 'quantitative', min: 1, max: 3, mean: 2, missing: 0, bins: [1, 1, 1] },
  };

  test('keep their documented order when a CSV gives them as text', async () => {
    const spec = starterSpec(table([grade, quant(1, 3)]))!;
    for (const rows of [[{ grade: '1', v: 1 }, { grade: '2', v: 2 }, { grade: '3', v: 3 }], [{ grade: 1, v: 1 }, { grade: 2, v: 2 }, { grade: 3, v: 3 }]]) {
      const view = await draw(spec, rows);
      try {
        expect(view.scale('y').domain().map(String)).toEqual(['3', '1', '2']);
      } finally {
        view.finalize();
      }
    }
  });

  test('in a year-like range are categories, not a time axis', () => {
    const odd: Field = { ...grade, categoriesOrdered: undefined, categories: [{ value: 1100, label: 'Low' }, { value: 2100, label: 'High' }], profile: { kind: 'quantitative', min: 1100, max: 2100, mean: 1600, missing: 0, bins: [1, 1] } };
    const spec = starterSpec(table([odd, quant(1, 3)]))!;
    expect(spec.mark).toEqual({ type: 'bar', tooltip: true });
    expect(enc(spec).y).toMatchObject({ field: 'grade', type: 'nominal' });
  });

  test('ordered text categories that name object properties keep the chart drawable', async () => {
    const values = ['toString', 'b'];
    const kind = nominal('kind', values, { categories: values, categoriesOrdered: true });
    const view = await draw(starterSpec(table([kind, quant(1, 2)]))!, [{ kind: 'toString', v: 1 }, { kind: 'b', v: 2 }]);
    view.finalize();
  });
});

describe('date bounds follow the field’s format and the profile’s UTC wall clock', () => {
  const when = (extra: Partial<Field>, min = '2020-01-15T00:00:00Z', max = '2020-03-01T00:00:00Z'): Field => ({
    name: 'when', type: 'date', description: null, profile: { kind: 'temporal', min, max, missing: 0 }, ...extra,
  });

  test('a strptime format reads day-first bounds', () => {
    const f = when({ format: '%d/%m/%Y', constraints: { minimum: '01/02/2020', maximum: '31/12/2020' } });
    expect(fieldNotes(f)).toEqual(['Documented range 01/02/2020 – 31/12/2020 (some values fall outside)']);
  });

  test('a datetime without a zone is wall-clock time, as the profile is', () => {
    const f = when({ type: 'datetime', constraints: { minimum: '2020-01-15T00:00:00' } });
    expect(fieldNotes(f)).toEqual(['Documented minimum 2020-01-15T00:00:00']);
    expect(fieldNotes({ ...f, constraints: { minimum: '2020-01-15T00:00:01' } })).toEqual(['Documented minimum 2020-01-15T00:00:01 (some values fall outside)']);
  });

  test('a format the site can’t read claims nothing', () => {
    const f = when({ format: '%d %B %Y', constraints: { minimum: '01 February 2020' } });
    expect(fieldNotes(f)).toEqual(['Documented minimum 01 February 2020']);
  });
});

test('a date field’s markers match its text before parsing: the same instant written otherwise stays', async () => {
  const when: Field = {
    name: 'when', type: 'datetime', description: null, missingValues: ['1900-01-01T00:00:00Z'],
    profile: { kind: 'temporal', min: '1899-12-31T19:00:00-05:00', max: '2020-01-01T00:00:00Z', missing: 1 },
  };
  const view = await draw(starterSpec(table([when, quant(1, 3)]))!, [
    { when: '1900-01-01T00:00:00Z', v: 10 }, { when: '1899-12-31T19:00:00-05:00', v: 2 }, { when: '2020-01-01T00:00:00Z', v: 3 },
  ]);
  try {
    // The marker's row (v = 10) is gone; the same instant written with an offset stays.
    expect(view.scale('y').domain()[1]).toBeLessThan(10);
    expect(+view.scale('x').domain()[0]).toBe(Date.UTC(1900, 0, 1));
  } finally {
    view.finalize();
  }
});

test('ordered integer categories sort as one type, whatever mix of numbers and text the file holds', async () => {
  const grade: Field = {
    name: 'grade', type: 'integer', description: null, categoriesOrdered: true,
    categories: [{ value: 3, label: 'High' }, { value: 1, label: 'Low' }, { value: 2, label: 'Mid' }],
    profile: { kind: 'quantitative', min: 1, max: 3, mean: 2, missing: 0, bins: [1, 1, 1] },
  };
  const rows = [{ grade: '1', v: 1, w: 1 }, { grade: 2, v: 2, w: 2 }, { grade: 3, v: 3, w: 3 }];
  const bars = await draw(starterSpec(table([grade, quant(1, 3)]))!, rows);
  try {
    expect(bars.scale('y').domain()).toEqual(['3', '1', '2']);
  } finally {
    bars.finalize();
  }
  const d = table([grade, quant(1, 3), quant(1, 3, { name: 'w' })]);
  const sf = scatterFields(d)!;
  const scatter = await draw(scatterSpec(d, sf, { x: 'v', y: 'w', zoom: false, height: 300 }), rows);
  try {
    expect(scatter.scale('color').domain()).toEqual(['3', '1', '2']);
  } finally {
    scatter.finalize();
  }
});

describe('strptime bounds are read strictly', () => {
  const when = (extra: Partial<Field>, min: string, max: string): Field => ({
    name: 'when', type: 'date', description: null, profile: { kind: 'temporal', min, max, missing: 0 }, ...extra,
  });

  test('%Y is the four digits as written: 0099 is the year 99', () => {
    const f = when({ format: '%Y-%m-%d', constraints: { minimum: '0099-01-01' } }, '0099-06-01T00:00:00Z', '0099-12-01T00:00:00Z');
    expect(fieldNotes(f)).toEqual(['Documented minimum 0099-01-01']);
    expect(insideDocumented(f)).toBe(true);
  });

  test('an impossible date is unreadable, not rolled over', () => {
    const f = when({ format: '%d/%m/%Y', constraints: { maximum: '31/02/2020' } }, '2020-02-10T00:00:00Z', '2020-03-01T00:00:00Z');
    expect(insideDocumented(f)).toBeNull();
    expect(insideDocumented({ ...f, format: undefined, constraints: { maximum: '2020-02-31' } })).toBeNull();
  });

  test('one unreadable bound makes the whole check unknown', () => {
    const f = when({ format: 'any', constraints: { minimum: '2020-01-01', maximum: 'Jan 31, 2020' } }, '2020-01-15T00:00:00Z', '2020-03-01T00:00:00Z');
    expect(insideDocumented(f)).toBeNull();
    expect(insideDocumented(quant(1, 2, { constraints: { minimum: 0, maximum: 'ten' as unknown as number } }))).toBeNull();
  });
});
