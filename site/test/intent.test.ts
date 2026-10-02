// @vitest-environment jsdom
import { afterEach, expect, test, vi } from 'vitest';
import { prepareOnIntent } from '../src/client/intent';

afterEach(() => vi.unstubAllGlobals());
function setup(connection = {}) {
  vi.stubGlobal('navigator', { connection });
  const controls = document.createElement('div');
  const chart = document.createElement('div');
  const prepare = vi.fn(async () => {});
  let top = 2000;
  controls.getBoundingClientRect = () => ({ top, bottom: top + 100 } as DOMRect);
  prepareOnIntent(controls, chart, prepare);
  return { controls, chart, prepare, approach: () => { top = 100; window.dispatchEvent(new Event('scroll')); } };
}

test('opening the page and scrolling elsewhere do not download the chart; approaching prepares it once', () => {
  const s = setup();
  expect(s.prepare).not.toHaveBeenCalled();
  window.dispatchEvent(new Event('scroll'));
  expect(s.prepare).not.toHaveBeenCalled();
  s.approach();
  s.controls.dispatchEvent(new Event('focusin'));
  s.chart.dispatchEvent(new Event('pointerdown'));
  expect(s.prepare).toHaveBeenCalledTimes(1);
});

test.each(['pointerover', 'pointerdown', 'focusin'])('%s prepares code without replacing or cancelling a static link', (event) => {
  const s = setup();
  const link = document.createElement('a');
  s.chart.append(link);
  const input = new Event(event, { bubbles: true, cancelable: true });
  link.dispatchEvent(input);
  expect(s.prepare).toHaveBeenCalledTimes(1);
  expect(input.defaultPrevented).toBe(false);
  expect(s.chart.firstChild).toBe(link);
});

test.each([{ saveData: true }, { effectiveType: '2g' }, { effectiveType: 'slow-2g' }])('constrained connections keep loading on demand: %j', (connection) => {
  const s = setup(connection);
  s.approach();
  s.controls.dispatchEvent(new Event('focusin'));
  expect(s.prepare).not.toHaveBeenCalled();
});

test('a failed speculative load is quiet', async () => {
  const s = setup();
  s.prepare.mockRejectedValueOnce(new Error('offline'));
  s.approach();
  await Promise.resolve();
  expect(s.prepare).toHaveBeenCalledTimes(1);
});
