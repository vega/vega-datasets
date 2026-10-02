// Components rendered as the site builds them, for a fully described dataset: the fields
// table (components/FieldsTable.astro) shows each field's title, key mark, documented
// metadata and format, the schema's missing markers and its joins, and the home page's
// card (components/DatasetCard.astro) summarizes it by its title. Without that metadata
// both render exactly what an undescribed dataset always had.
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { JSDOM } from 'jsdom';
import { beforeAll, expect, test } from 'vitest';
import DatasetCard from '../src/components/DatasetCard.astro';
import FieldsTable from '../src/components/FieldsTable.astro';
import { Catalog, type CatalogFile, type Dataset } from '../src/lib/catalog';
import { described, strip } from './fixtures';

const METADATA = 'https://github.com/vega/vega-datasets/blob/main/_data/datapackage_additions.toml#L42';

let container: AstroContainer;
beforeAll(async () => {
  container = await AstroContainer.create();
});

async function render(d: Dataset, names: string[] = ['fixture', 'origins']): Promise<{ html: string; doc: Document }> {
  const html = await container.renderToString(FieldsTable, { props: { dataset: d, metadata: METADATA, names: new Set(names) } });
  // Rendered on the server side, as the build does (Astro compiles components for SSR there), then parsed.
  const doc = new JSDOM(`<!doctype html><body>${html}</body>`).window.document;
  return { html, doc };
}

const row = (doc: Document, name: string) =>
  [...doc.querySelectorAll('tbody tr')].find((tr) => tr.querySelector('.f-name code')?.textContent === name)!;
const text = (el: Element | null | undefined) => el?.textContent?.replace(/\s+/g, ' ').trim() ?? null;

test('a fully described table shows its metadata beside each field', async () => {
  const { doc } = await render(described());
  const hp = row(doc, 'hp');
  expect(text(hp.querySelector('.f-title'))).toBe('Horsepower (hp)');
  expect(text(hp.querySelector('.f-desc'))).toBe('Engine power.');
  expect(text(hp.querySelector('.f-meta'))).toBe('Documented range 0 – 500 · Counted as missing: -99');
  expect(text(row(doc, 'mpg').querySelector('.f-meta'))).toBe('Documented range 0 – 40 (some values fall outside)');
  expect(text(row(doc, 'grade').querySelector('.f-meta'))).toBe('Values, in order: low (Low), mid (Medium), high (High)');
  expect(text(row(doc, 'side').querySelector('.f-meta'))).toBe('Values: left, right');
  expect(text(row(doc, 'origin').querySelector('.f-meta'))).toBe('Allowed values: usa, japan, europe');
  expect(text(row(doc, 'id').querySelector('.f-meta'))).toBe('Required · Unique');
  // The primary key is marked; only its field.
  expect([...doc.querySelectorAll('.f-key')].map((k) => text(k.closest('tr')!.querySelector('code')))).toEqual(['id']);
  // The format sits quietly under the type.
  expect(text(row(doc, 'when').querySelector('.f-type .f-format'))).toBe('%Y/%m/%d');
  expect(row(doc, 'hp').querySelector('.f-format')).toBeNull();
  // A field with nothing documented shows only what it always did.
  expect(row(doc, 'parent').querySelector('.f-title, .f-meta, .f-key, .f-format')).toBeNull();
});

test('the notes under the table: missing markers and the joins, linking pages that exist', async () => {
  const { doc } = await render(described());
  const notes = [...doc.querySelectorAll('.sec-note')].map(text);
  expect(notes).toEqual([
    'Profiled across all 5 rows. Empty cells and “NA” count as missing, except in fields that list their own markers.',
    'Rows refer to other rows of this table: parent → id.',
    'Joins with origins: origin → name.',
  ]);
  const link = doc.querySelector<HTMLAnchorElement>('.joins a')!;
  expect(link.textContent).toBe('origins');
  expect(link.getAttribute('href')).toMatch(/datasets\/origins\/$/);
  // A referenced dataset without a page is named, not linked.
  const { doc: unlinked } = await render(described(), ['fixture']);
  expect(unlinked.querySelector('.joins a')).toBeNull();
  expect(text(unlinked.querySelectorAll('.joins')[1]!)).toBe('Joins with origins: origin → name.');
});

test('without the metadata the table is the markup it always was', async () => {
  const { html, doc } = await render(strip(described()));
  expect(doc.querySelector('.f-title, .f-meta, .f-key, .f-format, .joins')).toBeNull();
  expect(doc.querySelectorAll('.sec-note')).toHaveLength(1);
  expect(text(doc.querySelector('.sec-note'))).toBe('Profiled across all 5 rows.');
  // The markup, sparklines aside (the 6a HTML diff checked every built page against 56ba567),
  // plus the "Add" link beside each undescribed field (6b).
  expect(html.replace(/<svg[\s\S]*?<\/svg>/g, '<svg/>')).toMatchSnapshot();
});

test('each undescribed field has a quiet "Add" link to the metadata entry, named for screen readers', async () => {
  const { doc } = await render(described());
  const adds = [...doc.querySelectorAll<HTMLAnchorElement>('.f-name a.f-add')];
  // Visually "Add"; its accessible name says what it adds (the rest is visually hidden).
  expect(adds.map((a) => text(a))).toEqual(['id', 'mpg', 'grade', 'side', 'origin', 'when'].map((n) => `Add a description for ${n}`));
  expect(adds.map((a) => a.firstChild?.textContent)).toEqual(Array(6).fill('Add'));
  expect(adds.every((a) => a.querySelector('.visually-hidden') && a.getAttribute('href') === METADATA)).toBe(true);
  expect(row(doc, 'hp').querySelector('.f-add')).toBeNull();
  // With no description at all, the note under the table links to the same entry.
  const { doc: none } = await render({ ...described(), fields: described().fields.map((f) => ({ ...f, description: '  ' })) });
  expect(none.querySelectorAll('.f-add')).toHaveLength(8);
  const note = none.querySelector<HTMLAnchorElement>('.sec-note a')!;
  expect(text(note)).toBe('Add them');
  expect(note.getAttribute('href')).toBe(METADATA);
  // Columns read from the data (no declared schema) aren't the metadata's fields: no "Add" beside them.
  const { doc: inferred } = await render({ ...described(), fieldsInferred: true, fields: described().fields.map((f) => ({ ...f, description: null })) });
  expect(inferred.querySelectorAll('.f-add')).toHaveLength(0);
});

test('a card summarizes the dataset by its title, else by its description', async () => {
  const card = async (d: Dataset) => {
    const catalog = new Catalog({ package: { name: 'x', version: '1', commit: 'c' }, readme: '', datasets: [d], examples: [] } as unknown as CatalogFile);
    const html = await container.renderToString(DatasetCard, { props: { catalog, dataset: d, max: 1 } });
    return new JSDOM(html).window.document.querySelector('.card-desc')!.textContent;
  };
  expect(await card(described())).toBe('Five cars, fully described');
  expect(await card(strip(described()))).toBe('A small table for testing.');
});
