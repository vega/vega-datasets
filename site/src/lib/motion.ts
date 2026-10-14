/**
 * "In Motion": smooth, eased animation between a dataset's keyframes, built on the
 * easing functions and `interpolateLinear` that Vega 6.4 added to the expression
 * language. Vega-Lite's animation support for these is still in review
 * (vega/vega-lite#9916, #9914), so this is a hand-written Vega spec.
 *
 * Only gapminder has a motion chart today. This module is the spec (no DOM); the
 * page's player is client/motion.ts, which only the gapminder page loads.
 */
import LZString from "lz-string";
import type { Dataset } from "./catalog";

type Spec = Record<string, unknown>;

export interface Country {
  country: string;
  region: string;
  fert: number[];
  life: number[];
  pop: number[];
}

export const REGION: Record<number, string> = {
  0: "South Asia",
  1: "Europe & Central Asia",
  2: "Sub-Saharan Africa",
  3: "America",
  4: "East Asia & Pacific",
  5: "Middle East & North Africa",
};
export const LABELED = ["China", "India", "United States", "Japan", "Nigeria", "Brazil"];
export const FIRST_YEAR = 1955;
export const STEP_YEARS = 5;
export const SEGMENT_MS = 1100;
export const HOLD_MS = 1600;

export interface GapminderRow {
  year: number;
  country: string;
  cluster: number;
  pop: number;
  life_expect: number;
  fertility: number;
}

/** One record per country with its keyframes in year order: the shape `interpolateLinear` reads. */
export function toCountries(rows: GapminderRow[]): Country[] {
  const by = new Map<string, Country>();
  for (const r of [...rows].sort((a, b) => a.year - b.year)) {
    const c = by.get(r.country) ?? { country: r.country, region: REGION[r.cluster] ?? "Other", fert: [], life: [], pop: [] };
    c.fert.push(r.fertility);
    c.life.push(r.life_expect);
    c.pop.push(r.pop);
    by.set(r.country, c);
  }
  return [...by.values()];
}


export interface Colors {
  neutral: string;
  accent: string;
  focus: string;
  surface: string;
  watermark: string;
  /** Forced colors only: the watermark is a system color at full strength, so it's dimmed. */
  watermarkOpacity?: number;
  trail: string;
  label: string;
}


export function gapminderSpec(values: Country[], width: number, height: number, col: Colors, init: { clock: number; playing: boolean; follow: string; hl: string | null }): Spec {
  const n = values[0]?.fert.length ?? 11;
  const labelSet = JSON.stringify(LABELED);
  return {
    $schema: "https://vega.github.io/schema/vega/v6.json",
    description: "Gapminder: life expectancy against fertility, 1955–2005, with eased transitions between five-year snapshots (Vega 6.4 easing functions and interpolateLinear).",
    width,
    height,
    padding: 4,
    autosize: { type: "fit", contains: "padding" },
    signals: [
      { name: "n", value: n },
      { name: "seg", value: SEGMENT_MS },
      { name: "hold", value: HOLD_MS },
      { name: "playing", value: init.playing },
      // Animation clock in ms, advanced on each timer tick while playing; it loops after a short hold on the last frame.
      {
        name: "clock",
        value: init.clock,
        on: [{
          events: { type: "timer", throttle: 16 },
          update: "playing ? (clock + now() - last_tick > (n - 1) * seg + hold ? 0 : clock + now() - last_tick) : clock",
        }],
      },
      { name: "last_tick", init: "now()", on: [{ events: [{ signal: "clock" }, { signal: "playing" }], update: "now()" }] },
      { name: "t", update: "clamp(clock / seg, 0, n - 1)" },
      { name: "k", update: "min(floor(t), n - 2)" },
      // Ease within each five-year segment, then map to [0, 1] across all keyframes.
      { name: "frac", update: "(k + easeCubicInOut(t - k)) / (n - 1)" },
      { name: "year", update: `${FIRST_YEAR} + ${STEP_YEARS} * round(t)` },
      { name: "hl", value: init.hl },
      { name: "follow", value: init.follow, on: [{ events: "@bubble:click", update: "datum.country" }] },
    ],
    data: [
      {
        name: "countries",
        values,
        transform: [
          { type: "formula", as: "x", expr: "interpolateLinear(datum.fert, frac)" },
          { type: "formula", as: "y", expr: "interpolateLinear(datum.life, frac)" },
          { type: "formula", as: "p", expr: "interpolateLinear(datum.pop, frac)" },
          { type: "collect", sort: { field: "p", order: "descending" } },
        ],
      },
      {
        name: "trail",
        source: "countries",
        transform: [
          { type: "filter", expr: "datum.country === follow" },
          { type: "flatten", fields: ["fert", "life"], as: ["tx", "ty"], index: "i" },
          { type: "formula", as: "ty_year", expr: `${FIRST_YEAR} + ${STEP_YEARS} * datum.i` },
        ],
      },
      {
        name: "labeled",
        source: "countries",
        transform: [{ type: "filter", expr: `indexof(${labelSet}, datum.country) >= 0 || datum.country === follow` }],
      },
    ],
    scales: [
      { name: "x", type: "linear", domain: [0, 9], range: "width", nice: false, zero: true },
      { name: "y", type: "linear", domain: [25, 85], range: "height", nice: false, zero: false },
      { name: "size", type: "sqrt", domain: [0, 1.4e9], range: [0, Math.round(Math.min(3600, width * 4))] },
    ],
    axes: [
      { orient: "bottom", scale: "x", title: "Babies per woman", grid: true, tickCount: 9, domain: false, ticks: false },
      { orient: "left", scale: "y", title: "Life expectancy (years)", grid: true, tickCount: 6, domain: false, ticks: false },
    ],
    marks: [
      {
        type: "text",
        interactive: false,
        encode: {
          update: {
            x: { signal: "width - 6" },
            y: { signal: "height - 8" },
            align: { value: "right" },
            baseline: { value: "bottom" },
            text: { signal: "year" },
            fontSize: { signal: "clamp(width / 5, 56, 150)" },
            fontWeight: { value: 600 },
            fill: { value: col.watermark },
            ...(col.watermarkOpacity !== undefined ? { fillOpacity: { value: col.watermarkOpacity } } : {}),
          },
        },
      },
      {
        type: "line",
        from: { data: "trail" },
        interactive: false,
        encode: {
          update: {
            x: { scale: "x", field: "tx" },
            y: { scale: "y", field: "ty" },
            stroke: { value: col.trail },
            strokeWidth: { value: 1.5 },
            strokeOpacity: { value: 0.55 },
            strokeCap: { value: "round" },
          },
        },
      },
      {
        type: "symbol",
        from: { data: "trail" },
        interactive: false,
        encode: {
          update: {
            x: { scale: "x", field: "tx" },
            y: { scale: "y", field: "ty" },
            size: { value: 14 },
            fill: { value: col.trail },
            fillOpacity: { value: 0.55 },
          },
        },
      },
      {
        type: "symbol",
        name: "bubble",
        from: { data: "countries" },
        encode: {
          update: {
            x: { scale: "x", field: "x" },
            y: { scale: "y", field: "y" },
            size: { scale: "size", field: "p" },
            fill: [
              { test: "datum.country === follow", value: col.focus },
              { test: "hl && datum.region === hl", value: col.accent },
              { value: col.neutral },
            ],
            fillOpacity: [{ test: "datum.country === follow", value: 0.95 }, { value: 0.78 }],
            stroke: { value: col.surface },
            strokeWidth: { value: 1.5 },
            cursor: { value: "pointer" },
            tooltip: {
              signal: "{title: datum.country, 'Region': datum.region, 'Year': year, 'Life expectancy': format(datum.y, '.1f'), 'Babies per woman': format(datum.x, '.2f'), 'Population': format(datum.p, ',.0f')}",
            },
          },
        },
      },
      {
        type: "text",
        from: { data: "labeled" },
        interactive: false,
        encode: {
          update: {
            x: { signal: "scale('x', datum.x) + sqrt(scale('size', datum.p)) / 2 + 4" },
            y: { scale: "y", field: "y" },
            baseline: { value: "middle" },
            text: { field: "country" },
            fontSize: { value: 11.5 },
            fontWeight: [{ test: "datum.country === follow", value: 600 }, { value: 400 }],
            fill: { value: col.label },
          },
        },
      },
    ],
  };
}

/** Open a Vega spec in the Vega Editor (the spec travels in the URL, compressed the way the Editor expects). */
export function vegaEditorUrl(spec: Spec): string {
  return `https://vega.github.io/editor/#/url/vega/${LZString.compressToEncodedURIComponent(JSON.stringify(spec, null, 2))}`;
}

export function hasMotion(d: Dataset): boolean {
  return d.name === "gapminder";
}
