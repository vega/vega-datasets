/** The tooltips: one floating tip shared by the hand-drawn SVG profiles, and dismissal for both it and the charts' (vega-tooltip). */
import { h } from "./dom";

let tip: HTMLDivElement | null = null;

function el(): HTMLDivElement {
  if (!tip) {
    tip = h("div", { class: "tip", role: "tooltip", hidden: true });
    document.body.append(tip);
  }
  return tip;
}

/** Show `lines` (the first in bold) centred above the point (x, y), kept on screen. */
export function showTipAt(x: number, y: number, lines: string[]): void {
  const t = el();
  t.replaceChildren(...lines.map((line, i) => h(i === 0 ? "strong" : "span", null, line)));
  t.hidden = false;
  const w = t.offsetWidth;
  t.style.left = `${Math.min(Math.max(8, x - w / 2), window.innerWidth - w - 8)}px`;
  t.style.top = `${Math.max(8, y - t.offsetHeight - 12)}px`;
}

export function hideTip(): void {
  if (tip) tip.hidden = true;
}

/** Hide vega-tooltip's element (the charts' tooltip) the way vega-tooltip itself does. */
export function hideChartTip(): void {
  document.getElementById("vg-tooltip-element")?.classList.remove("visible", "custom-theme");
}

let dismissing = false;

/**
 * Tooltips are fixed to the viewport, so one left showing floats over the page as it
 * scrolls. On a phone that happened: a scroll that starts on a chart sends pointermove
 * (vega-tooltip shows) and then pointercancel, never a pointerout on the mark. Hide both
 * tooltips when the page (or a region in it) scrolls, when the browser takes over a
 * gesture, and when a finger or pen lifts. The mouse's hover is untouched. Installed once.
 */
export function dismissTipsOnTouch(): void {
  if (dismissing) return;
  dismissing = true;
  const hide = (): void => {
    hideTip();
    hideChartTip();
  };
  addEventListener("scroll", hide, { capture: true, passive: true });
  addEventListener("pointercancel", hide, { capture: true });
  addEventListener("pointerup", (e) => { if (e.pointerType !== "mouse") hide(); }, { capture: true });
}
