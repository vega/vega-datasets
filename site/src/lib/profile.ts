/**
 * Field profiles for the fields table, from the precomputed summaries in
 * catalog.json: a sparkline histogram for numbers and dates (as geometry, drawn to
 * SVG when the site is built), a one-line summary, and the missing count.
 */
import type { Field } from "./catalog";
import { formatCount, formatDate, formatNumber, parseDate, TYPE_LABEL } from "./format";

function binEdges(lo: number, hi: number, n: number): number[] {
  return Array.from({ length: n + 1 }, (_, i) => lo + ((hi - lo) * i) / n);
}

/** Bars grow from one baseline with a 2px-rounded data end (clipped to the bar width). */
function barPath(x: number, y: number, w: number, hgt: number, r: number): string {
  const rr = Math.min(r, w / 2, hgt);
  const n = (v: number) => Number(v.toFixed(2));
  return `M${n(x)},${n(y + hgt)}V${n(y + rr)}Q${n(x)},${n(y)} ${n(x + rr)},${n(y)}H${n(x + w - rr)}Q${n(x + w)},${n(y)} ${n(x + w)},${n(y + rr)}V${n(y + hgt)}Z`;
}

export interface SparkBin {
  /** Left edge of the bin's full-height hit area, and its width. */
  x: number;
  width: number;
  /** The bar, or null for an empty bin. */
  path: string | null;
  /** The value range, as shown in the tooltip. */
  range: string;
  count: number;
}

export interface Sparkline {
  width: number;
  height: number;
  bins: SparkBin[];
  /** What the sparkline shows, for its accessible name. */
  label: string;
}

function histogram(bins: number[], range: (i: number) => string, width: number, height: number): SparkBin[] {
  const max = Math.max(...bins, 1);
  const gap = 2;
  const bw = (width - gap * (bins.length - 1)) / bins.length;
  return bins.map((count, i) => {
    const x = i * (bw + gap);
    const bh = count === 0 ? 0 : Math.max(1.5, ((height - 2) * count) / max);
    return { x: Number(x.toFixed(2)), width: Number((bw + gap).toFixed(2)), path: bh > 0 ? barPath(x, height - 1 - bh, bw, bh, 2) : null, range: range(i), count };
  });
}

/**
 * The range each histogram bin covers, as text; null for categories and empty fields.
 * A date field's bins read as dates (their edges fall at odd hours, which aren't in the data).
 */
export function binLabels(f: Field): string[] | null {
  const p = f.profile;
  if (p.kind === "quantitative") {
    const edges = binEdges(p.min, p.max, p.bins.length);
    return p.bins.map((_, i) => `${formatNumber(edges[i] ?? p.min)} – ${formatNumber(edges[i + 1] ?? p.max)}`);
  }
  if (p.kind === "temporal" && p.bins?.length) {
    const lo = parseDate(p.min).getTime();
    const hi = parseDate(p.max).getTime();
    const edges = binEdges(lo, hi, p.bins.length);
    const time = f.type === "date" ? false : undefined;
    const text = (t: number) => formatDate(new Date(t).toISOString(), time);
    return p.bins.map((_, i) => `${text(edges[i] ?? lo)} – ${text(edges[i + 1] ?? hi)}`);
  }
  return null;
}

/** A small histogram for the fields table, or null for categories and empty fields. */
export function sparkline(f: Field, width = 120, height = 26): Sparkline | null {
  const p = f.profile;
  const label = `${f.name} distribution, ${p.kind === "temporal" ? "by date" : "by value"}`;
  const ranges = binLabels(f);
  if (!ranges || (p.kind !== "quantitative" && p.kind !== "temporal") || !p.bins) return null;
  return { width, height, label, bins: histogram(p.bins, (i) => ranges[i]!, width, height) };
}

/** Dates on January 1 at midnight are years (a "Year" column stored as a date). */
function yearsOnly(iso: string): boolean {
  return /^\d{4}-01-01(T00:00:00(\.0+)?Z?)?$/.test(iso);
}

/** One line about a field's values: range and mean, date span, or the most common values. */
export function profileSummary(f: Field): string {
  const p = f.profile;
  switch (p.kind) {
    case "quantitative":
      return `${formatNumber(p.min)} – ${formatNumber(p.max)} · mean ${formatNumber(p.mean)}`;
    case "temporal":
      return yearsOnly(p.min) && yearsOnly(p.max)
        ? `${p.min.slice(0, 4)} – ${p.max.slice(0, 4)}`
        : `${formatDate(p.min)} – ${formatDate(p.max)}`;
    case "nominal":
      return p.top.slice(0, 3).map(([v, n]) => `${v} ${formatCount(n)}`).join(" · ");
    default:
      return "No values";
  }
}

/** Missing values as "8 · 2.0%", or "0". */
export function missingCount(f: Field, rows: number | null): { text: string; any: boolean } {
  const m = f.profile.missing ?? 0;
  if (!m || !rows) return { text: "0", any: false };
  return { text: `${formatCount(m)} · ${((100 * m) / rows).toFixed(1)}%`, any: true };
}

export function typeLabel(f: Field): string {
  return TYPE_LABEL[f.type] ?? f.type;
}
