// @vitest-environment jsdom
import { afterAll, beforeAll, beforeEach, expect, test } from 'vitest';
import { enhanceProjectMenu } from '../src/client/project-menu';

let menu: HTMLDetailsElement;
let trigger: HTMLElement;

beforeAll(() => {
  document.body.innerHTML = '<a href="/">Home</a><details><summary>Vega projects</summary><a href="/vega/">Vega</a></details><button>Outside</button>';
  menu = document.querySelector('details')!;
  trigger = menu.querySelector('summary')!;
  enhanceProjectMenu(menu);
});
beforeEach(() => { menu.open = false; });
afterAll(() => { document.body.innerHTML = ''; });

test('Escape closes the menu and returns focus to its trigger', () => {
  menu.open = true;
  const link = menu.querySelector('a')!;
  link.focus();
  link.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));
  expect(menu.open).toBe(false);
  expect(document.activeElement).toBe(trigger);
});

test('clicking within the menu keeps it open; an outside click dismisses it', () => {
  menu.open = true;
  menu.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  expect(menu.open).toBe(true);
  document.querySelector('button')!.click();
  expect(menu.open).toBe(false);
});

test('moving focus out dismisses the menu without stealing focus', () => {
  menu.open = true;
  trigger.focus();
  const link = menu.querySelector('a')!;
  link.focus();
  expect(menu.open).toBe(true);
  const outside = document.querySelector('button')!;
  outside.focus();
  expect(menu.open).toBe(false);
  expect(document.activeElement).toBe(outside);
});
