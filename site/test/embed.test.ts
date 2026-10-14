// @vitest-environment jsdom
// Loading Vega on demand (client/embed.ts): the import is shared by every chart on the page,
// but a failed import (a dropped connection) isn't kept, so a Retry imports again.
import { describe, expect, test, vi } from 'vitest';
import { ChartCodeError, runView, vegaLoader } from '../src/client/embed';
import { parse, View } from 'vega';
import { compile } from 'vega-lite';
import { onceUnlessFailed } from '../src/lib/once';

/** Stand-ins for vega-embed, vega-interpreter and vega: just what setting up reads. */
function fakeModules() {
  const formats = vi.fn();
  const vega = { formats, loader: () => ({ load: async () => '' }) };
  return { formats, modules: [{ default: vi.fn() }, { expressionInterpreter: {} }, vega] as never };
}

test('the documented prerun callback updates dependent signals in the same Vega evaluation', async () => {
  const view = new View(parse({ signals: [{ name: 'input', value: 1 }, { name: 'output', update: 'input * 2' }] }), { renderer: 'none' });
  try {
    await view.runAsync();
    await runView(view, () => { view.signal('input', 3); });
    expect(view.signal('output')).toBe(6);
  } finally { view.finalize(); }
});

test('switching to wider axis numbers remeasures the SVG margin instead of clipping digits', async () => {
  const { spec } = compile({
    width: 320, height: 240, autosize: { type: 'fit-x', contains: 'padding' },
    data: { values: [{ x: 1, small: 12, large: 1500 }, { x: 2, small: 34, large: 5500 }] },
    params: [{ name: 'field', value: 'small' }],
    transform: [{ calculate: 'datum[field]', as: 'y' }],
    mark: 'point', encoding: { x: { field: 'x', type: 'quantitative' }, y: { field: 'y', type: 'quantitative', scale: { zero: false } } },
  });
  const view = new View(parse(spec), { renderer: 'none' });
  const margin = async () => {
    const svg = new DOMParser().parseFromString(await view.toSVG(), 'image/svg+xml');
    return Number(svg.querySelector('svg > g')!.getAttribute('transform')!.match(/translate\(([-\d.]+)/)![1]);
  };
  try {
    await view.runAsync();
    const narrow = await margin();
    await runView(view, () => { view.signal('field', 'large'); });
    expect(await margin()).toBeGreaterThan(narrow);
    expect(await view.toSVG()).toContain('5,000');
  } finally { view.finalize(); }
});

describe('loading Vega', () => {
  test('a failed import rejects with ChartCodeError, and the next call imports again', async () => {
    const { formats, modules } = fakeModules();
    const importer = vi.fn()
      .mockRejectedValueOnce(new TypeError('Failed to fetch dynamically imported module'))
      .mockResolvedValue(modules);
    const load = vegaLoader(importer);
    const first = load();
    await expect(first).rejects.toBeInstanceOf(ChartCodeError);
    await expect(first).rejects.toThrow("Couldn't load the chart code.");
    const v = await load();
    expect(importer).toHaveBeenCalledTimes(2);
    expect(typeof v.loader).toBe('function');
    // The CSP-safe readers are registered once the modules are in.
    expect(formats.mock.calls.map(([name]) => name).sort()).toEqual(['csv', 'dsv', 'tsv']);
    // Once in, every later chart shares the same modules.
    expect(await load()).toBe(v);
    expect(importer).toHaveBeenCalledTimes(2);
  });

  test('callers waiting on the same attempt share it', async () => {
    let resolve!: (x: number) => void;
    const loadOnce = vi.fn(() => new Promise<number>((r) => (resolve = r)));
    const load = onceUnlessFailed(loadOnce);
    const [a, b] = [load(), load()];
    resolve(7);
    expect(await a).toBe(7);
    expect(await b).toBe(7);
    expect(loadOnce).toHaveBeenCalledTimes(1);
  });
});
