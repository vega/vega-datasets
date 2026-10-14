// The status page's table (components/StatusTable.astro), rendered as the site builds it,
// for fixture datasets: most gaps first, a row id per dataset (the dataset pages' footer
// links to it), each dataset-level item as present or missing, the field descriptions
// counted, what applies only where it fits listed as documented, and links to the dataset
// page and to its metadata entry.
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { JSDOM } from 'jsdom';
import { beforeAll, expect, test } from 'vitest';
import StatusTable from '../src/components/StatusTable.astro';
import type { Dataset } from '../src/lib/catalog';
import { described, strip } from './fixtures';

let container: AstroContainer;
beforeAll(async () => {
  container = await AstroContainer.create();
});

const text = (el: Element | null | undefined) => el?.textContent?.replace(/\s+/g, ' ').trim() ?? null;

function datasets(): Dataset[] {
  const full = described();
  const complete: Dataset = { ...full, name: 'complete', sources: [{ title: 'Made up', path: 'https://example.org/' }], fields: full.fields.map((f) => ({ ...f, description: f.description ?? 'Described.' })) };
  const image: Dataset = { ...strip(full), name: 'image', kind: 'file', format: 'png', fields: [], rows: null, licenses: [{ name: 'notspecified' }], sources: [] };
  return [complete, { ...full, name: 'fixture' }, image];
}

async function render(): Promise<Document> {
  const html = await container.renderToString(StatusTable, { props: { datasets: datasets(), entry: (d: Dataset) => `https://github.com/o/r/blob/main/x.toml#L${d.name.length}` } });
  return new JSDOM(`<!doctype html><body>${html}</body>`).window.document;
}

test('rows, most gaps first, each with a namespaced id (ds-<name>)', async () => {
  const doc = await render();
  const rows = [...doc.querySelectorAll('tbody tr')];
  // fixture: 6 undescribed fields; image: title, source, license; complete: none.
  // Namespaced: a dataset named "page" must not share the layout's main#page.
  expect(rows.map((r) => r.id)).toEqual(['ds-fixture', 'ds-image', 'ds-complete']);
  expect(rows.map((r) => text(r.querySelector('.st-num')))).toEqual(['6', '3', '0']);
});

test('each item reads as present or missing, in words a screen reader says', async () => {
  const doc = await render();
  const cells = (id: string) => [...doc.getElementById(`ds-${id}`)!.querySelectorAll('td')].map(text);
  expect([...doc.querySelectorAll('thead th')].map(text)).toEqual(['Dataset', 'Gaps', 'Title', 'Description', 'Source', 'License', 'Field Descriptions', 'Also Documented', 'Metadata entry']);
  expect(cells('image')).toEqual(['3', 'Missing', '✓Yes', 'Missing', 'Not specified', '–No fields', '–None', 'Edit the image entry']);
  expect(cells('fixture')).toEqual([
    '6', '✓Yes', '✓Yes', '✓Yes (no link)', '✓Yes', '2 of 8',
    'Field titles (5 fields), Categories (2 fields), Constraints (4 fields), Missing values, Primary key, Foreign keys (2)',
    'Edit the fixture entry',
  ]);
  expect(cells('complete').slice(0, 6)).toEqual(['0', '✓Yes', '✓Yes', '✓Yes', '✓Yes', '8 of 8']);
  // The marks are decoration; the words are hidden only visually.
  for (const mark of doc.querySelectorAll('td > span[aria-hidden="true"]')) expect(mark.nextElementSibling?.className).toBe('visually-hidden');
});

test('each row links to its dataset page and its metadata entry; the table scrolls in a focusable region', async () => {
  const doc = await render();
  const row = doc.getElementById('ds-fixture')!;
  expect(row.querySelector('th[scope="row"] a')!.getAttribute('href')).toMatch(/datasets\/fixture\/$/);
  expect(row.querySelector('td:last-child a')!.getAttribute('href')).toBe('https://github.com/o/r/blob/main/x.toml#L7');
  const region = doc.querySelector('.table-scroll')!;
  expect(region.getAttribute('tabindex')).toBe('0');
  expect(region.getAttribute('role')).toBe('region');
  expect(region.getAttribute('aria-label')).toBeTruthy();
});
