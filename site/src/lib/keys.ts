/** Stepping between dataset pages from the keyboard (no DOM, so it is unit-tested). */

type Key = Pick<KeyboardEvent, "key" | "defaultPrevented" | "metaKey" | "ctrlKey" | "altKey" | "shiftKey">;

/**
 * Which way a key press steps between datasets: +1, -1 or 0. Only the Left and Right
 * arrows step, with no modifier, and only when focus is on the page itself (`onPage`):
 * a focused widget — a scroll region, a sparkline, tabs, a link — keeps its arrow keys.
 * There are no letter shortcuts, which speech-input users could trigger by accident
 * (WCAG 2.1.4).
 */
export function datasetStep(e: Key, onPage: boolean): -1 | 0 | 1 {
  if (!onPage || e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey || e.shiftKey) return 0;
  if (e.key === "ArrowRight") return 1;
  if (e.key === "ArrowLeft") return -1;
  return 0;
}
