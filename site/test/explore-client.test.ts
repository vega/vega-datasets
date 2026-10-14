// @vitest-environment jsdom
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { enhanceExplore } from '../src/client/explore';
import { loadCatalog } from './catalog';

const mocks = vi.hoisted(() => ({ embed: vi.fn(), theme: vi.fn() }));
vi.mock('../src/client/embed', () => ({
  loadVega: async () => ({ vegaEmbed: mocks.embed }),
  embedOptions: (_v, _renderer, _actions, onError) => ({ onError }), labelActions: () => {},
  runView: async (view, before) => { before(); return view.runAsync(); },
  ChartCodeError: class extends Error {},
}));
vi.mock('../src/client/theme', () => ({ onThemeChange: mocks.theme }));
vi.mock('../src/client/dom', async (original) => ({ ...await original<typeof import('../src/client/dom')>(), afterPaint: async () => {} }));
const catalog = loadCatalog();
let phone: { matches: boolean; addEventListener: ReturnType<typeof vi.fn> };
const section = () => document.querySelector<HTMLElement>('section')!;
const mode = (name: string) => document.querySelector<HTMLButtonElement>(`[data-mode="${name}"]`)!.click();
const settled = () => vi.waitFor(() => expect(document.querySelector('[aria-busy]')).toBeNull());

function drawing() {
  const listeners = new Map<string, (name: string, value: unknown) => void>();
  const view = {
    data: vi.fn(() => new Array(398)), width: vi.fn().mockReturnThis(), container: () => ({ clientWidth: 320 }),
    addSignalListener: vi.fn((name, fn) => listeners.set(name, fn)),
    runAsync: vi.fn(async () => {}),
  };
  return { view, listeners, vgSpec: { marks: [{ type: 'symbol', from: { data: 'points' } }] }, finalize: vi.fn() };
}
beforeEach(() => {
  mocks.embed.mockReset();
  phone = { matches: true, addEventListener: vi.fn() };
  vi.stubGlobal('matchMedia', () => phone);
  document.body.innerHTML = '<section><div class="seg"><button data-mode="scatter">Scatter</button><button data-mode="time">Over Time</button></div><div class="binds"></div><div class="explore-chart"></div><div class="chart-caption"><span class="hint"></span><span class="features"></span></div><a data-editor></a></section>';
  mocks.embed.mockImplementation(async (plot, _spec, opts) => {
    plot.append(document.createElement('svg'));
    opts.bind.append(document.createElement('select'));
    return drawing();
  });
});
afterEach(() => vi.unstubAllGlobals());

test('visited modes reuse their DOM and selections without evaluating or compiling again', async () => {
  enhanceExplore(section(), catalog.dataset('cars')!);
  await settled();
  const firstPlot = document.querySelector('.explore-view');
  const firstInput = document.querySelector('.binds select');
  const first = await mocks.embed.mock.results[0]!.value;
  first.listeners.get('xField')('xField', 'Horsepower');
  first.listeners.get('yField')('yField', 'Weight_in_lbs');
  await Promise.resolve();
  first.view.runAsync.mockClear();
  mode('time'); await settled();
  mode('scatter'); await settled();
  expect(mocks.embed).toHaveBeenCalledTimes(2);
  expect(first.view.runAsync).not.toHaveBeenCalled();
  expect(first.finalize).not.toHaveBeenCalled();
  expect(document.querySelector('.explore-view:not([hidden])')).toBe(firstPlot);
  expect(document.querySelector('.binds select')).toBe(firstInput);
  expect(document.querySelector('.chart-caption .hint')!.textContent).toContain('398 of 406');
  for (let i = 0; i < 3; i++) { mode('time'); await settled(); mode('scatter'); await settled(); }
  expect(section().dataset.draws).toBe('2');
  expect(document.querySelectorAll('.explore-view:not([hidden])')).toHaveLength(1);
});

test('rapid switches coalesce and an obsolete drawing is finalized before the latest choice appears', async () => {
  enhanceExplore(section(), catalog.dataset('cars')!);
  await settled();
  let finish!: (value: ReturnType<typeof drawing>) => void;
  const obsolete = drawing();
  mocks.embed.mockImplementationOnce(() => new Promise((resolve) => { finish = resolve; }));
  mode('time');
  await vi.waitFor(() => expect(mocks.embed).toHaveBeenCalledTimes(2));
  mode('scatter');
  finish(obsolete);
  await settled();
  expect(obsolete.finalize).toHaveBeenCalledTimes(1);
  expect(document.querySelectorAll('.explore-view')).toHaveLength(1);
  mode('time'); mode('scatter');
  await settled();
  expect(mocks.embed).toHaveBeenCalledTimes(2);
});

test('a cached view is refitted after a window resize, and a breakpoint change disposes old views', async () => {
  enhanceExplore(section(), catalog.dataset('cars')!);
  await settled();
  const first = await mocks.embed.mock.results[0]!.value;
  mode('time'); await settled();
  const second = await mocks.embed.mock.results[1]!.value;
  window.dispatchEvent(new Event('resize'));
  mode('scatter'); await settled();
  expect(first.view.width).toHaveBeenCalled();
  expect(first.view.runAsync).toHaveBeenCalledTimes(1);
  phone.matches = false;
  phone.addEventListener.mock.calls.find(([event]) => event === 'change')![1]();
  await settled();
  expect(first.finalize).toHaveBeenCalledTimes(1);
  expect(second.finalize).toHaveBeenCalledTimes(1);
  expect(document.querySelectorAll('.explore-view')).toHaveLength(1);
});

test('a failed data load disposes its view and retry creates a usable chart', async () => {
  const failed = drawing();
  mocks.embed.mockImplementationOnce(async (_host, _spec, opts) => { opts.onError('cars.json'); return failed; });
  enhanceExplore(section(), catalog.dataset('cars')!);
  await settled();
  expect(failed.finalize).toHaveBeenCalledTimes(1);
  expect(document.querySelector('.load-error')!.textContent).toContain("Couldn't load cars.json");
  expect(document.querySelectorAll('.explore-view')).toHaveLength(0);
  document.querySelector<HTMLButtonElement>('[data-retry]')!.click();
  await settled();
  expect(document.querySelector('.load-error')).toBeNull();
  expect(document.querySelector('.explore-view svg')).not.toBeNull();
});

test('large datasets keep only one live view', async () => {
  const cars = { ...catalog.dataset('cars')!, rows: 6000 };
  enhanceExplore(section(), cars);
  await settled();
  const first = await mocks.embed.mock.results[0]!.value;
  mocks.embed.mockImplementationOnce(async () => {
    expect(first.finalize).toHaveBeenCalledTimes(1);
    return drawing();
  });
  mode('time'); await settled();
  expect(first.finalize).toHaveBeenCalledTimes(1);
  expect(document.querySelectorAll('.explore-view')).toHaveLength(1);
});
