/**
 * Draw a Vega-Lite spec to SVG when the site is built (headless Vega, as the tests do),
 * so a chart is in the page's HTML before any script runs. The browser then takes over
 * with the live view (client/catalog-chart.ts).
 */
import * as vega from "vega";
import { compile, type TopLevelSpec } from "vega-lite";
import { pointSource } from "../lib/vega-data";
import { themeConfig } from "../lib/vega-theme";
import { readDataUrl } from "./repo";
import { lightToken } from "./tokens";

/**
 * Helvetica's advance widths (in em, from its font metrics). Without a canvas Vega guesses
 * 0.8 em per character, which lays legends out far wider than the browser will; these keep
 * the static chart close to the live one.
 */
const HELVETICA: Record<string, number> = {
  " ": 0.278, ".": 0.278, ",": 0.278, ":": 0.278, "/": 0.278, "-": 0.333, "(": 0.333, ")": 0.333, _: 0.556,
  a: 0.556, b: 0.556, c: 0.5, d: 0.556, e: 0.556, f: 0.278, g: 0.556, h: 0.556, i: 0.222, j: 0.222, k: 0.5, l: 0.222, m: 0.833,
  n: 0.556, o: 0.556, p: 0.556, q: 0.556, r: 0.333, s: 0.5, t: 0.278, u: 0.556, v: 0.5, w: 0.722, x: 0.5, y: 0.5, z: 0.5,
  A: 0.667, B: 0.667, C: 0.722, D: 0.722, E: 0.667, F: 0.611, G: 0.778, H: 0.722, I: 0.278, J: 0.5, K: 0.667, L: 0.556, M: 0.833,
  N: 0.722, O: 0.778, P: 0.667, Q: 0.778, R: 0.722, S: 0.667, T: 0.611, U: 0.722, V: 0.667, W: 0.944, X: 0.667, Y: 0.667, Z: 0.611,
};

type TextItem = { fontSize?: number; font?: string; fontWeight?: string | number; text?: unknown };

// vega exports textMetrics (vl-convert overrides it the same way), though its typings don't list it.
const { textMetrics } = vega as unknown as { textMetrics: { width: (item: TextItem, text?: unknown) => number } };
textMetrics.width = (item: TextItem, text?: unknown) => {
  const s = String(text ?? item.text ?? "").trim();
  const size = item.fontSize ?? 11;
  if (/mono/i.test(item.font ?? "")) return 0.6 * s.length * size;
  const bold = item.fontWeight === "bold" || Number(item.fontWeight) >= 600;
  let em = 0;
  for (const ch of s) em += HELVETICA[ch] ?? 0.556;
  return em * size * (bold ? 1.06 : 1);
};

export interface StaticChart {
  svg: string;
  width: number;
  height: number;
}

export async function staticChart(spec: Record<string, unknown>): Promise<StaticChart> {
  const config = themeConfig(lightToken);
  const { spec: vg } = compile(spec as unknown as TopLevelSpec, { config: config as never });
  const view = new vega.View(vega.parse(vg), { renderer: "none" });
  try {
    await view.runAsync();
    let svg = await view.toSVG();
    // Links on the points repeat the cards' links; keep them out of the tab order (as the live view does).
    svg = svg.replace(/<a xlink:href=/g, '<a tabindex="-1" xlink:href=');
    const size = svg.match(/<svg [^>]*width="(\d+(?:\.\d+)?)" height="(\d+(?:\.\d+)?)"/);
    return { svg, width: Number(size?.[1] ?? 0), height: Number(size?.[2] ?? 0) };
  } finally {
    view.finalize();
  }
}

/** What Explore's chart draws, known when the site is built. */
export interface DrawnChart {
  /** Its height in CSS pixels (axes, titles, legend and padding included). */
  height: number;
  /** For a scatter plot, the rows it plots (both values present); null otherwise. */
  plotted: number | null;
}

/**
 * How a chart draws at `width`, from the local data file: the height Explore reserves
 * before it draws, so the page doesn't move when the chart arrives and no gap is left
 * after it, and the scatter caption's row count.
 */
export async function drawnChart(spec: Record<string, unknown>, width: number): Promise<DrawnChart> {
  const config = themeConfig(lightToken);
  const { spec: vg } = compile({ ...spec, width } as unknown as TopLevelSpec, { config: config as never });
  const loader = vega.loader();
  loader.load = async (uri: string) => readDataUrl(uri);
  const view = new vega.View(vega.parse(vg), { renderer: "none", loader });
  try {
    await view.runAsync();
    // The SVG's own height: the plot, its axes and titles, the legend and the padding.
    const svg = await view.toSVG();
    const source = pointSource(vg as never);
    return {
      height: Math.ceil(Number(svg.match(/<svg [^>]*height="(\d+(?:\.\d+)?)"/)?.[1] ?? 0)),
      plotted: source ? (view.data(source) as unknown[]).length : null,
    };
  } finally {
    view.finalize();
  }
}
