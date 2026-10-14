// @vitest-environment jsdom
// @vitest-environment-options {"url": "https://vega.github.io/vega-datasets/?q=horsepower"}
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { afterEach, expect, test, vi } from 'vitest';
import { homeIndex } from '../src/lib/home-model';
import { loadCatalog, REPO } from './catalog';

const mount = vi.hoisted(() => vi.fn());
vi.mock('../src/client/embed', () => ({ loadVega: vi.fn(async () => ({})) }));
vi.mock('../src/client/dom', async (original) => ({ ...await original<typeof import('../src/client/dom')>(), afterPaint: async () => {} }));
vi.mock('../src/client/catalog-chart', () => ({ mountCatalogChart: mount }));
afterEach(() => vi.unstubAllGlobals());

test('failed filters and chart loads can retry without losing the latest search or static chart', async () => {
  const html = readFileSync(path.join(REPO, 'site/dist/index.html'), 'utf8');
  document.body.innerHTML = html.slice(html.indexOf('<body>') + 6, html.lastIndexOf('</body>'));
  vi.stubGlobal('matchMedia', () => ({ matches: false, addEventListener() {} }));
  const fetchIndex = vi.fn().mockResolvedValueOnce(new Response('', { status: 503 }))
    .mockImplementation(async () => new Response(JSON.stringify(homeIndex(loadCatalog()))));
  vi.stubGlobal('fetch', fetchIndex);
  const mounted = { redraw: vi.fn(async () => {}), setMatches: vi.fn(), setGalleries: vi.fn(), clearBrush: vi.fn(), destroy: vi.fn() };
  mount.mockRejectedValueOnce(new Error('temporary render failure')).mockResolvedValue(mounted);
  await import('../src/client/home');
  await vi.waitFor(() => expect(document.querySelector('.browse .status')!.textContent).toContain("Couldn't load filters"));
  expect(mount).not.toHaveBeenCalled();
  expect(document.querySelector('.chart-static')).not.toBeNull();

  document.querySelector<HTMLButtonElement>('.browse .status button')!.click();
  await vi.waitFor(() => expect(document.querySelector('[data-chart] .load-error')).not.toBeNull());
  expect(fetchIndex).toHaveBeenCalledTimes(2);
  expect(document.querySelector<HTMLInputElement>('#home-q')!.value).toBe('horsepower');
  expect([...document.querySelectorAll<HTMLElement>('.card')].filter((c) => !c.hidden).map((c) => c.dataset.name)).toEqual(['cars']);
  expect(document.querySelector('.chart-static')).not.toBeNull();

  document.querySelector<HTMLButtonElement>('[data-chart] .load-error button')!.click();
  await vi.waitFor(() => expect(mounted.setMatches).toHaveBeenLastCalledWith(['cars']));
  expect(mount).toHaveBeenCalledTimes(2);
  expect(fetchIndex).toHaveBeenCalledTimes(2);
  expect(document.querySelector('[data-chart] .load-error')).toBeNull();
});
