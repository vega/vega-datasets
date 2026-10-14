// @vitest-environment jsdom
// @vitest-environment-options {"url": "https://vega.github.io/vega-datasets/"}
// The home page's script (client/home.ts) run on the built page (site/dist/index.html, from
// `npm run site:build`): a list update keeps focus on the card, and a legacy #name set after
// load opens the dataset while About anchors open their item.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { afterAll, beforeAll, expect, test, vi } from 'vitest';
import { homeIndex } from '../src/lib/home-model';
import { exampleCount, loadCatalog, REPO } from './catalog';

const catalog = loadCatalog();
// jsdom can't navigate, and its location can't be spied on: the script gets this one instead.
const here = {
  hash: '',
  search: '',
  pathname: '/vega-datasets/',
  href: 'https://vega.github.io/vega-datasets/',
  replace: vi.fn(),
};
const order = () => [...document.querySelectorAll<HTMLElement>('.cards a.card')].map((a) => a.dataset.name);
const card = (name: string) => document.querySelector<HTMLAnchorElement>(`.cards a.card[data-name="${name}"]`)!;
// Let the event handlers' promise continuations finish, without a fixed UI delay.
const settle = () => new Promise((r) => setTimeout(r, 0));
const scrollIntoView = vi.fn();
const mounted = vi.hoisted(() => ({ redraw: vi.fn(async () => {}), setMatches: vi.fn(), setGalleries: vi.fn(), clearBrush: vi.fn(), destroy: vi.fn() }));
vi.mock('../src/client/embed', () => ({ loadVega: vi.fn(async () => ({})) }));
vi.mock('../src/client/dom', async (original) => ({ ...await original<typeof import('../src/client/dom')>(), afterPaint: async () => {} }));
let brushChange: (b: import('../src/lib/home-model').Brush | null) => void;
vi.mock('../src/client/catalog-chart', () => ({
  mountCatalogChart: vi.fn(async (_host, _rows, _options, onBrush) => {
    brushChange = onBrush;
    return mounted;
  }),
}));

beforeAll(async () => {
  const html = readFileSync(path.join(REPO, 'site', 'dist', 'index.html'), 'utf8');
  document.body.innerHTML = html.slice(html.indexOf('<body>') + 6, html.lastIndexOf('</body>'));
  vi.stubGlobal('location', here);
  vi.stubGlobal('matchMedia', (query: string) => ({ matches: false, media: query, addEventListener() {}, removeEventListener() {} }));
  vi.stubGlobal('fetch', async () => new Response(JSON.stringify(homeIndex(catalog))));
  // jsdom has no layout/scrolling; the browser check covers the actual position.
  document.querySelectorAll('.about-item').forEach((item) => {
    Object.defineProperty(item, 'scrollIntoView', { value: scrollIntoView });
  });
  await import('../src/client/home');
  await settle();
});

afterAll(() => vi.unstubAllGlobals());

test('a card that has to move keeps focus when the list is re-sorted', async () => {
  // Every card shown, so the focused one stays visible in either order.
  document.querySelector<HTMLButtonElement>('.browse-foot .more')!.click();
  await settle();
  const moved = card('airports');
  const before = order();
  moved.focus();
  expect(document.activeElement).toBe(moved);
  const removed: Node[] = [];
  const observer = new MutationObserver((records) => records.forEach((r) => removed.push(...r.removedNodes)));
  observer.observe(document.querySelector('.cards')!, { childList: true });
  const sort = document.querySelector<HTMLSelectElement>('#home-sort')!;
  sort.value = 'az';
  sort.dispatchEvent(new Event('change'));
  await settle();
  removed.push(...observer.takeRecords().flatMap((r) => [...r.removedNodes]));
  observer.disconnect();
  const after = order();
  expect(after).toEqual([...after].sort((x, y) => x!.localeCompare(y!)));
  // airports goes from further down (by use) to first (A to Z): it is detached and put back,
  // which blurs it, so its focus has to be restored.
  expect(before.indexOf('airports')).toBeGreaterThan(0);
  expect(after.indexOf('airports')).toBe(0);
  expect(removed).toContain(moved);
  expect(moved.hidden).toBe(false);
  expect(document.activeElement).toBe(moved);
});

test('an About anchor set after load opens its item and stays on the page', () => {
  here.hash = '#about-versioning';
  window.dispatchEvent(new HashChangeEvent('hashchange'));
  expect(here.replace).not.toHaveBeenCalled();
  expect(document.querySelector<HTMLDetailsElement>('#about-versioning')!.open).toBe(true);
  expect(document.activeElement).toBe(document.querySelector('#about-versioning summary'));
  expect(scrollIntoView).toHaveBeenCalledWith({ block: 'start', behavior: 'instant' });
});

test('following the same About link again reopens the item before native navigation', () => {
  const item = document.querySelector<HTMLDetailsElement>('#about-versioning')!;
  item.open = false;
  const link = document.querySelector<HTMLAnchorElement>('[data-open-details]')!;
  const click = new MouseEvent('click', { bubbles: true, cancelable: true });
  link.dispatchEvent(click);
  expect(item.open).toBe(true);
  expect(item.classList.contains('about-reveal')).toBe(false);
  expect(document.activeElement).toBe(item.querySelector('summary'));
  expect(click.defaultPrevented).toBe(false);
});

test('modified About links leave this page alone', () => {
  const item = document.querySelector<HTMLDetailsElement>('#about-versioning')!;
  item.open = false;
  const link = document.querySelector<HTMLAnchorElement>('[data-open-details]')!;
  link.dispatchEvent(new MouseEvent('click', { bubbles: true, ctrlKey: true }));
  expect(item.open).toBe(false);
});

test('malformed and unrelated fragments leave the disclosures alone', () => {
  const open = [...document.querySelectorAll<HTMLDetailsElement>('.about-item')].map((item) => item.open);
  for (const hash of ['#%E0%A4%A', '#does-not-exist', '#browse']) {
    here.hash = hash;
    window.dispatchEvent(new HashChangeEvent('hashchange'));
  }
  expect([...document.querySelectorAll<HTMLDetailsElement>('.about-item')].map((item) => item.open)).toEqual(open);
});

test('a legacy #name set after load opens that dataset\'s page', () => {
  here.hash = '#cars';
  window.dispatchEvent(new HashChangeEvent('hashchange'));
  expect(here.replace).toHaveBeenCalledTimes(1);
  expect(here.replace).toHaveBeenCalledWith('https://vega.github.io/vega-datasets/datasets/cars/');
});

test('gallery selection keeps card counts, ranking, chart parameters and brush scope consistent', async () => {
  here.hash = '';
  const sort = document.querySelector<HTMLSelectElement>('#home-sort')!;
  sort.value = 'used';
  sort.dispatchEvent(new Event('change'));
  document.querySelector<HTMLButtonElement>('[data-gallery="vega"]')!.click();
  await settle();
  expect(mounted.setGalleries).toHaveBeenLastCalledWith(['vega']);
  expect(card('cars').querySelector('[data-usage-count]')!.textContent).toBe(String(exampleCount(catalog, 'cars', ['vega'])));
  expect(card('cars').querySelector<HTMLElement>('[data-usage-gallery="altair"]')!.hidden).toBe(true);
  expect(document.querySelector('[data-usage-scope]')!.textContent).toBe('Vega examples');
  expect(document.querySelector('.status')!.textContent).toBe('Most used first  ·  Clear');
  expect(mounted.setMatches).toHaveBeenLastCalledWith(null);
  const shown = () => [...document.querySelectorAll<HTMLAnchorElement>('.cards .card')].filter((a) => !a.hidden);
  const counts = shown().map((a) => Number(a.querySelector('[data-usage-count]')!.textContent));
  expect(counts).toEqual([...counts].sort((a, b) => b - a));

  brushChange({ bytes: [0, 1], examples: [0, 1] });
  expect(shown()).toHaveLength(0);
  document.querySelector<HTMLButtonElement>('[data-gallery="altair"]')!.click();
  await settle();
  expect(shown().length).toBeGreaterThan(0);
  expect(mounted.setGalleries).toHaveBeenLastCalledWith(['vega', 'altair']);
  expect(card('cars').querySelector('[data-usage-count]')!.textContent).toBe(String(exampleCount(catalog, 'cars', ['vega', 'altair'])));
  expect(document.querySelector('.status')!.textContent).not.toContain('filtered by chart');

  document.querySelector<HTMLButtonElement>('.status button')!.click();
  await settle();
  expect(mounted.setGalleries).toHaveBeenLastCalledWith([]);
  expect(card('cars').querySelector('[data-usage-count]')!.textContent).toBe(String(exampleCount(catalog, 'cars')));
  expect(card('cars').querySelector<HTMLElement>('[data-usage-gallery="altair"]')!.hidden).toBe(false);
});

test('zero-use datasets stay visible, searchable and expanded when changing the count scope', async () => {
  const shown = () => [...document.querySelectorAll<HTMLAnchorElement>('.cards .card')].filter((a) => !a.hidden);
  document.querySelector<HTMLButtonElement>('[data-gallery="vega"]')!.click();
  await settle();
  document.querySelector<HTMLButtonElement>('.browse-foot .more')!.click();
  expect(shown()).toHaveLength(catalog.datasets.length);
  expect(card('birdstrikes').hidden).toBe(false);
  expect(card('birdstrikes').querySelector('[data-usage-count]')!.textContent).toBe('0');

  document.querySelector<HTMLButtonElement>('[data-gallery="vega-lite"]')!.click();
  await settle();
  expect(shown()).toHaveLength(catalog.datasets.length);
  expect(card('cars').querySelector('[data-usage-count]')!.textContent).toBe(String(exampleCount(catalog, 'cars', ['vega', 'vega-lite'])));

  const search = document.querySelector<HTMLInputElement>('#home-q')!;
  search.value = 'birdstrikes';
  search.dispatchEvent(new Event('input'));
  await settle();
  expect(shown().map((a) => a.dataset.name)).toEqual(['birdstrikes']);
  expect(card('birdstrikes').querySelector('[data-usage-count]')!.textContent).toBe('0');
  document.querySelector<HTMLButtonElement>('.status button')!.click();
  await settle();
});
