/**
 * Fixture datasets for the metadata tests: one fully described (every standard Data Package
 * and Table Schema property the site renders), and the same table with that metadata
 * stripped, which must render exactly as an undescribed dataset always has.
 */
import type { Dataset, Field } from '../src/lib/catalog';

const URL = 'https://vega.github.io/vega-datasets/data/fixture.csv';

/** The rows the fixture's profiles describe, for drawing its charts offline. */
export const ROWS = [
  { id: 1, parent: null, hp: 130, mpg: 18, grade: 'high', side: 'left', origin: 'usa', when: '2020/01/02' },
  { id: 2, parent: 1, hp: 165, mpg: 15, grade: 'mid', side: 'right', origin: 'usa', when: '2020/02/02' },
  { id: 3, parent: 1, hp: 46, mpg: 46.6, grade: 'low', side: 'left', origin: 'japan', when: '2020/03/02' },
  { id: 4, parent: 2, hp: 230, mpg: 12, grade: 'high', side: 'right', origin: 'europe', when: '2020/04/02' },
  { id: 5, parent: 2, hp: 95, mpg: 26, grade: 'low', side: 'left', origin: 'japan', when: '2020/05/02' },
];

const quant = (min: number, max: number, mean: number) => ({ kind: 'quantitative' as const, min, max, mean, missing: 0, bins: [1, 1, 1, 1, 1] });
const nominal = (top: [string, number][]) => ({ kind: 'nominal' as const, distinct: top.length, top, missing: 0 });

/** The fully described table. */
export function described(): Dataset {
  const fields: Field[] = [
    { name: 'id', type: 'integer', description: null, title: 'Identifier', constraints: { required: true, unique: true }, profile: quant(1, 5, 3) },
    { name: 'parent', type: 'integer', description: 'The row this one belongs to.', profile: { ...quant(1, 2, 1.5), missing: 1 } },
    {
      name: 'hp', type: 'number', description: 'Engine power.', title: 'Horsepower (hp)',
      constraints: { minimum: 0, maximum: 500 }, missingValues: ['-99'], profile: quant(46, 230, 133.2),
    },
    // Documented as at most 40 mpg, but one car does better: the axis keeps the data's own extent.
    { name: 'mpg', type: 'number', description: null, title: 'Miles per Gallon', constraints: { minimum: 0, maximum: 40 }, profile: quant(12, 46.6, 23.5) },
    {
      name: 'grade', type: 'string', description: null, title: 'Trim Grade',
      categories: [{ value: 'low', label: 'Low' }, { value: 'mid', label: 'Medium' }, { value: 'high', label: 'High' }],
      categoriesOrdered: true, profile: nominal([['high', 2], ['low', 2], ['mid', 1]]),
    },
    { name: 'side', type: 'string', description: null, categories: ['left', 'right'], profile: nominal([['left', 3], ['right', 2]]) },
    { name: 'origin', type: 'string', description: null, constraints: { enum: ['usa', 'japan', 'europe'] }, profile: nominal([['japan', 2], ['usa', 2], ['europe', 1]]) },
    {
      name: 'when', type: 'date', description: null, title: 'Date Sold', format: '%Y/%m/%d',
      profile: { kind: 'temporal', min: '2020-01-02T00:00:00Z', max: '2020-05-02T00:00:00Z', missing: 0, bins: [1, 1, 1, 1, 1] },
    },
  ];
  return {
    name: 'fixture',
    title: 'Five cars, fully described',
    file: 'fixture.csv',
    url: URL,
    format: 'csv',
    kind: 'table',
    bytes: 400,
    description: 'A small table for testing.\n\nIts second paragraph.',
    licenses: [{ name: 'CC0-1.0' }],
    sources: [{ title: 'Made up' }],
    usedBy: [],
    fields,
    rows: 5,
    preview: null,
    primaryKey: 'id',
    foreignKeys: [
      { fields: 'parent', reference: { resource: '', fields: 'id' } },
      { fields: ['origin'], reference: { resource: 'origins', fields: ['name'] } },
    ],
    missingValues: ['', 'NA'],
  };
}

const DATASET_KEYS = ['title', 'primaryKey', 'foreignKeys', 'missingValues'] as const;
const FIELD_KEYS = ['title', 'categories', 'categoriesOrdered', 'constraints', 'format', 'missingValues'] as const;

/** A dataset as the builder writes it when the metadata has none of the new properties. */
export function strip(d: Dataset): Dataset {
  const out: Record<string, unknown> = { ...d, fields: d.fields.map((f) => {
    const g: Record<string, unknown> = { ...f };
    for (const k of FIELD_KEYS) delete g[k];
    return g;
  }) };
  for (const k of DATASET_KEYS) delete out[k];
  return out as unknown as Dataset;
}

/** The described fixture with only the fields named (in that order), for steering the starter rules. */
export function only(d: Dataset, names: string[]): Dataset {
  return { ...d, fields: names.map((n) => d.fields.find((f) => f.name === n)!) };
}
