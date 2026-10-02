// @vitest-environment jsdom
// Tooltips don't outlive a touch gesture (client/tooltip.ts). Tooltips are fixed to the
// viewport, so one left showing floats over the page as it scrolls: on a phone, a scroll
// that starts on a chart used to leave vega-tooltip's box on screen. The browser check
// site/test/browser/touch-tooltip.mjs plays the gesture on real charts.
import { beforeAll, beforeEach, expect, test } from 'vitest';
import { dismissTipsOnTouch, showTipAt } from '../src/client/tooltip';

let chartTip: HTMLElement;

beforeAll(() => {
  dismissTipsOnTouch();
  dismissTipsOnTouch(); // Installing twice adds no second set of listeners (harmless either way).
});

beforeEach(() => {
  document.getElementById('vg-tooltip-element')?.remove();
  chartTip = document.createElement('div');
  chartTip.id = 'vg-tooltip-element';
  chartTip.className = 'vg-tooltip visible custom-theme';
  document.body.append(chartTip);
  showTipAt(10, 10, ['2 – 3', '5 rows']);
});

const shown = () => ({ chart: chartTip.classList.contains('visible'), profile: !document.querySelector<HTMLElement>('.tip')!.hidden });

function pointer(type: string, pointerType: string): void {
  // jsdom has no PointerEvent: a MouseEvent carrying pointerType stands in for it.
  const e = new MouseEvent(type, { bubbles: true, cancelable: true });
  Object.defineProperty(e, 'pointerType', { value: pointerType });
  document.body.dispatchEvent(e);
}

test('a scroll hides both tooltips, the page or a region inside it', () => {
  window.dispatchEvent(new Event('scroll'));
  expect(shown()).toEqual({ chart: false, profile: false });
  chartTip.classList.add('visible');
  showTipAt(10, 10, ['x']);
  document.body.dispatchEvent(new Event('scroll')); // A scroll region's scroll doesn't bubble: capture hears it.
  expect(shown()).toEqual({ chart: false, profile: false });
});

test('the browser taking over a gesture (pointercancel) hides them', () => {
  pointer('pointercancel', 'touch');
  expect(shown()).toEqual({ chart: false, profile: false });
});

test('a finger or pen lifting hides them', () => {
  for (const kind of ['touch', 'pen']) {
    chartTip.classList.add('visible');
    showTipAt(10, 10, ['x']);
    pointer('pointerup', kind);
    expect(shown()).toEqual({ chart: false, profile: false });
  }
});

test("the mouse's click leaves a hover tooltip alone", () => {
  pointer('pointerup', 'mouse');
  expect(shown()).toEqual({ chart: true, profile: true });
});
