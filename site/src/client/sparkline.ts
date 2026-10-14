/**
 * The fields table's histograms (components/Sparkline.astro): each is one tab stop, a
 * slider over its bins. Arrow keys, Home and End move between bins and read each one
 * out (aria-valuetext); the pointer shows the same tooltip on hover.
 */
import { formatCount } from "../lib/format";
import { hideTip, showTipAt } from "./tooltip";

function binText(bin: Element): [string, string] {
  const count = Number(bin.getAttribute("data-count") ?? 0);
  return [bin.getAttribute("data-range") ?? "", `${formatCount(count)} ${count === 1 ? "row" : "rows"}`];
}

export function enhanceSparkline(wrap: HTMLElement): void {
  const bins = [...wrap.querySelectorAll<SVGGElement>(".hist-bin")];
  if (!bins.length) return;
  let active = -1;
  const show = (i: number, at?: { x: number; y: number }) => {
    active = i;
    bins.forEach((b, j) => b.classList.toggle("active", j === i));
    const bin = bins[i]!;
    const [range, rows] = binText(bin);
    wrap.setAttribute("aria-valuenow", String(i + 1));
    wrap.setAttribute("aria-valuetext", `${range}: ${rows}`);
    const r = bin.getBoundingClientRect();
    showTipAt(at?.x ?? r.left + r.width / 2, at?.y ?? r.top, [range, rows]);
  };
  const clear = () => {
    bins.forEach((b) => b.classList.remove("active"));
    hideTip();
  };
  bins.forEach((b, i) => {
    const onPointer = (e: PointerEvent) => show(i, { x: e.clientX, y: e.clientY });
    b.addEventListener("pointerenter", onPointer);
    b.addEventListener("pointermove", onPointer);
  });
  wrap.addEventListener("pointerleave", () => {
    if (document.activeElement !== wrap) clear();
  });
  wrap.addEventListener("focus", () => show(active < 0 ? 0 : active));
  wrap.addEventListener("blur", clear);
  wrap.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      clear();
      return;
    }
    const moves: Record<string, number> = { ArrowRight: active + 1, ArrowUp: active + 1, ArrowLeft: active - 1, ArrowDown: active - 1, Home: 0, End: bins.length - 1 };
    const next = moves[e.key];
    // A modified key is the browser's (Alt+Left is Back, Ctrl+Home the top of the page).
    if (next === undefined || e.altKey || e.ctrlKey || e.metaKey) return;
    e.preventDefault();
    show(Math.min(bins.length - 1, Math.max(0, next)));
  });
}
