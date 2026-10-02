// Stepping between datasets with the keyboard: the arrow keys, from the page only, no letters.
import { expect, test } from 'vitest';
import { datasetStep } from '../src/lib/keys';

const key = (k: string, mods: Partial<KeyboardEvent> = {}) =>
  ({ key: k, defaultPrevented: false, metaKey: false, ctrlKey: false, altKey: false, shiftKey: false, ...mods }) as KeyboardEvent;

test('the arrow keys step when focus is on the page', () => {
  expect(datasetStep(key('ArrowRight'), true)).toBe(1);
  expect(datasetStep(key('ArrowLeft'), true)).toBe(-1);
});

test('a focused widget keeps its arrow keys (scroll regions, sparklines, tabs, links)', () => {
  expect(datasetStep(key('ArrowRight'), false)).toBe(0);
  expect(datasetStep(key('ArrowLeft'), false)).toBe(0);
  expect(datasetStep(key('ArrowRight', { defaultPrevented: true }), true)).toBe(0);
});

test('no single-letter shortcuts (WCAG 2.1.4) and no modified arrows', () => {
  for (const k of ['j', 'k', 'n', 'p']) expect(datasetStep(key(k), true)).toBe(0);
  for (const mod of ['metaKey', 'ctrlKey', 'altKey', 'shiftKey'] as const) {
    expect(datasetStep(key('ArrowRight', { [mod]: true }), true)).toBe(0);
  }
});
