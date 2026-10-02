// @vitest-environment jsdom
// The fields table's histograms (client/sparkline.ts): one tab stop whose arrow keys, Home
// and End step through the bins. A modified key is the browser's or the system's (Alt+Left
// is Back, Ctrl+Home goes to the top), so the histogram leaves it alone.
import { beforeEach, expect, test } from 'vitest';
import { enhanceSparkline } from '../src/client/sparkline';

let wrap: HTMLElement;

beforeEach(() => {
  document.body.innerHTML = `<span class="spark-wrap" tabindex="0" role="slider"><svg>${[0, 1, 2]
    .map((i) => `<g class="hist-bin" data-range="${i} – ${i + 1}" data-count="${i + 1}"><rect></rect></g>`)
    .join('')}</svg></span>`;
  wrap = document.querySelector('.spark-wrap')!;
  enhanceSparkline(wrap);
  wrap.focus();
});

/** Press `key` on the histogram; whether the histogram took it (preventDefault). */
function press(key: string, mods: KeyboardEventInit = {}): boolean {
  const e = new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true, ...mods });
  wrap.dispatchEvent(e);
  return e.defaultPrevented;
}

test('the arrow keys, Home and End step through the bins', () => {
  expect(press('ArrowRight')).toBe(true);
  expect(wrap.getAttribute('aria-valuenow')).toBe('2');
  expect(press('End')).toBe(true);
  expect(wrap.getAttribute('aria-valuenow')).toBe('3');
  expect(press('Home')).toBe(true);
  expect(wrap.getAttribute('aria-valuenow')).toBe('1');
});

test('modified keys pass through to the browser (Alt+Left is Back, Ctrl+Home the top)', () => {
  for (const [key, mods] of [
    ['ArrowLeft', { altKey: true }],
    ['ArrowRight', { altKey: true }],
    ['Home', { ctrlKey: true }],
    ['End', { ctrlKey: true }],
    ['ArrowRight', { metaKey: true }],
  ] as const) {
    const before = wrap.getAttribute('aria-valuenow');
    expect(press(key, mods), `${key} ${JSON.stringify(mods)}`).toBe(false);
    expect(wrap.getAttribute('aria-valuenow')).toBe(before);
  }
});
