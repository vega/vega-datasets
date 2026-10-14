// @vitest-environment jsdom
// The home page's list update (client/home.ts) reorders the cards already in the page:
// placeInOrder moves only the cards out of place, so a focused card that stays keeps focus.
import { beforeEach, expect, test } from 'vitest';
import { placeInOrder } from '../src/client/dom';

let parent: HTMLElement;
const card = (name: string) => parent.querySelector<HTMLAnchorElement>(`[data-name="${name}"]`)!;
const order = () => [...parent.children].map((c) => (c as HTMLElement).dataset.name);

beforeEach(() => {
  document.body.innerHTML = '<div class="cards">' + ['a', 'b', 'c', 'd', 'e'].map((n) => `<a class="card" href="#${n}" data-name="${n}">${n}</a>`).join('') + '</div>';
  parent = document.querySelector('.cards')!;
});

/** How many nodes were removed from `parent` while `fn` ran (a removed node loses focus). */
function removals(fn: () => void): number {
  const observer = new MutationObserver(() => {});
  observer.observe(parent, { childList: true });
  fn();
  const n = observer.takeRecords().reduce((sum, r) => sum + r.removedNodes.length, 0);
  observer.disconnect();
  return n;
}

test('the same order moves nothing, so the focused card keeps focus', () => {
  card('c').focus();
  expect(removals(() => expect(placeInOrder(parent, ['a', 'b', 'c', 'd', 'e'].map(card))).toBe(0))).toBe(0);
  expect(document.activeElement).toBe(card('c'));
});

test('a filtered list moves nothing when its cards are already in order among the others', () => {
  card('d').focus();
  expect(removals(() => placeInOrder(parent, ['b', 'd'].map(card)))).toBe(0);
  expect(document.activeElement).toBe(card('d'));
});

test('a new order is applied, moving only what has to move', () => {
  expect(placeInOrder(parent, ['e', 'a', 'b', 'c', 'd'].map(card))).toBe(1);
  expect(order()).toEqual(['e', 'a', 'b', 'c', 'd']);
  expect(placeInOrder(parent, ['d', 'c', 'b'].map(card))).toBeGreaterThan(0);
  const listed = order().filter((n) => ['d', 'c', 'b'].includes(n!));
  expect(listed).toEqual(['d', 'c', 'b']);
});
