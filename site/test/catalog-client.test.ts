// @vitest-environment jsdom
import { beforeEach, expect, test, vi } from 'vitest';
import { mountCatalogChart } from '../src/client/catalog-chart';
import { CATALOG_LAYOUTS, type CatalogLayout } from '../src/lib/catalog-layout';

const mocks = vi.hoisted(() => ({ embed: vi.fn() }));
vi.mock('../src/client/embed', () => ({
  loadVega: async () => ({ View: class {}, vegaEmbed: mocks.embed }),
  embedOptions: () => ({}), labelActions: () => {},
  runView: (view, before) => view.runAsync(undefined, before),
}));
function drawing() {
  const view = {
    signal: vi.fn().mockReturnThis(), addSignalListener: vi.fn(),
    runAsync: vi.fn(async (_encode, before) => { before?.(); }),
  };
  return { view, spec: {}, finalize: vi.fn() };
}
beforeEach(() => {
  mocks.embed.mockReset();
  vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} });
  document.body.innerHTML = '<div data-chart><svg class="chart-static"></svg></div>';
});
const host = () => document.querySelector<HTMLElement>('[data-chart]')!;

test('a burst of filters uses one evaluation with the final values, and a failed run can recover', async () => {
  const result = drawing();
  mocks.embed.mockResolvedValue(result);
  const failed = vi.fn();
  const chart = await mountCatalogChart(host(), [], () => ({ brush: false }), vi.fn(), failed);
  chart.setGalleries(['vega']);
  chart.setMatches(['cars']);
  chart.setMatches(['iris']);
  await vi.waitFor(() => expect(result.view.runAsync).toHaveBeenCalledTimes(1));
  expect(result.view.signal.mock.calls).toEqual([['galleries', ['vega']], ['matched', ['iris']]]);
  result.view.runAsync.mockRejectedValueOnce(new Error('render failed'));
  chart.setMatches(['cars']);
  await vi.waitFor(() => expect(failed).toHaveBeenCalledTimes(1));
  chart.setMatches(null);
  await vi.waitFor(() => expect(result.view.signal).toHaveBeenLastCalledWith('matched', null));
  expect(result.view.runAsync).toHaveBeenCalledTimes(3);
  chart.destroy();
  chart.setMatches(['iris']);
  expect(host().querySelector('.chart-live')).toBeNull();
  expect(result.finalize).toHaveBeenCalledTimes(1);
});

test('a failed replacement retains the working chart and a later redraw succeeds', async () => {
  const first = drawing();
  const next = drawing();
  mocks.embed.mockResolvedValueOnce(first).mockRejectedValueOnce(new Error('failed')).mockResolvedValueOnce(next);
  const chart = await mountCatalogChart(host(), [], () => ({ brush: false }), vi.fn());
  const original = host().querySelector('.chart-live');
  await expect(chart.redraw()).rejects.toThrow('failed');
  expect(first.finalize).not.toHaveBeenCalled();
  expect(host().querySelector('.chart-live')).toBe(original);
  expect(host().querySelector('.pending')).toBeNull();
  await chart.redraw();
  expect(first.finalize).toHaveBeenCalledTimes(1);
  expect(host().querySelectorAll('.chart-live')).toHaveLength(1);
  expect(host().querySelector('.chart-live')).not.toBe(original);
  chart.destroy();
});

test('a failed first render leaves only the usable static drawing', async () => {
  mocks.embed.mockRejectedValueOnce(new Error('failed'));
  await expect(mountCatalogChart(host(), [], () => ({ brush: false }), vi.fn())).rejects.toThrow('failed');
  expect(host().querySelector('.chart-static')).not.toBeNull();
  expect(host().querySelector('.chart-live')).toBeNull();
});

test('page geometry stays fixed within a layout; crossing layouts redraws while the Editor keeps automatic layout', async () => {
  const result = drawing();
  mocks.embed.mockResolvedValue(result);
  let layout: CatalogLayout = CATALOG_LAYOUTS[0];
  const chart = await mountCatalogChart(host(), [], () => ({ brush: false, height: 214, labels: 5, monoFont: 'monospace', layout, matched: ['cars'] }), vi.fn());
  const spec = mocks.embed.mock.calls[0]![1];
  expect(spec.height).toBe(layout.height);
  expect(spec.width).toBe(layout.width);
  expect(spec.autosize).toEqual({ type: 'none', contains: 'padding' });
  expect(spec.params.find((p) => p.name === 'matched').value).toEqual(['cars']);
  expect(result.spec.height).toBe(214);
  expect(result.spec.autosize.type).toBe('fit-x');
  chart.setMatches(['cars']);
  expect(result.view.runAsync).not.toHaveBeenCalled();
  window.dispatchEvent(new Event('resize'));
  await new Promise((resolve) => setTimeout(resolve, 150));
  expect(mocks.embed).toHaveBeenCalledTimes(1);
  expect(result.view.runAsync).not.toHaveBeenCalled();
  layout = CATALOG_LAYOUTS[1];
  window.dispatchEvent(new Event('resize'));
  await vi.waitFor(() => expect(mocks.embed).toHaveBeenCalledTimes(2));
  expect(mocks.embed.mock.calls[1]![1].width).toBe(layout.width);
  expect(result.spec.height).toBe(214);
  chart.destroy();
});
