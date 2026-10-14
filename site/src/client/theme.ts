/**
 * Resolve page tokens and notify when forced colors (such as Windows High Contrast)
 * turn on, off or switch palettes. The site itself uses one light palette.
 */
import { type ChartInk, forcedInk, type SystemColors, tokenInk } from "../lib/vega-theme";

export function token(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

const FORCED = "(forced-colors: active)";

/** Whether a forced-colors mode (Windows High Contrast) has replaced the page's colors. */
export function forcedColors(): boolean {
  return matchMedia(FORCED).matches;
}

/**
 * Read the system colors off a hidden probe. Charts need them as values: the mode recolors
 * the page's CSS, but not a canvas's pixels or the colors Vega writes into SVG attributes.
 */
export function systemColors(): SystemColors {
  const probe = document.createElement("span");
  const set = (property: string, value: string) => probe.style.setProperty(property, value);
  set("position", "absolute");
  set("visibility", "hidden");
  set("forced-color-adjust", "none");
  set("color", "CanvasText");
  set("background-color", "Canvas");
  set("border-top-color", "GrayText");
  set("border-bottom-color", "Highlight");
  document.body.append(probe);
  const style = getComputedStyle(probe);
  const colors = {
    canvasText: style.color,
    canvas: style.backgroundColor,
    grayText: style.borderTopColor,
    highlight: style.borderBottomColor,
  };
  probe.remove();
  return colors;
}

/** The chart chrome for the page as it is now. */
export function chartInk(): ChartInk {
  return forcedColors() ? forcedInk(systemColors()) : tokenInk(token);
}

/** Only forced colors can change the charts' palette. */
function themeState(): string {
  return forcedColors() ? `forced ${JSON.stringify(systemColors())}` : "light";
}

/**
 * Call `fn` when forced colors turn on or off or switch palettes. Keep the OS scheme
 * listener because switching between light and dark high-contrast palettes changes it;
 * ordinary OS scheme changes leave themeState unchanged and never redraw a chart.
 */
export function onThemeChange(fn: () => void): () => void {
  let last = themeState();
  const check = () => {
    const now = themeState();
    if (now !== last) {
      last = now;
      fn();
    }
  };
  const media = [matchMedia("(prefers-color-scheme: dark)"), matchMedia(FORCED)];
  for (const m of media) m.addEventListener("change", check);
  return () => {
    for (const m of media) m.removeEventListener("change", check);
  };
}

export function reducedMotion(): boolean {
  return matchMedia("(prefers-reduced-motion: reduce)").matches;
}
