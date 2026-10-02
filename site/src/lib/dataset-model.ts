/** What a dataset page says about loading and describing a file, as plain data (unit-tested). */
import type { Dataset, Example, Gallery } from "./catalog";
import { GALLERIES } from "./catalog";
import { formatBytes, formatCount, FORMAT_LABEL } from "./format";

/** A tool's code snippet behind a tab (Use This Dataset, Quick Start). */
export interface Snippet {
  name: string;
  code: string;
}

/** Released files are on jsDelivr (npm); newer ones are only on GitHub Pages so far. */
export function isReleased(d: Dataset): boolean {
  const url = new URL(d.url);
  return url.hostname === "cdn.jsdelivr.net" && url.pathname.startsWith("/npm/vega-datasets@");
}

/** A variable name for the loaded data. */
function variable(d: Dataset): string {
  const id = d.name.replace(/[^A-Za-z0-9_$]/g, "_");
  return /^[0-9]/.test(id) ? `_${id}` : id;
}

/** The files Vega-Lite and Vega read with a `data` url. */
const VL_FORMATS = new Set(["csv", "tsv", "json", "topojson", "geojson"]);

/** JSON on one line, spaced as people write it: `{"type": "csv", "parse": "auto"}`. */
function inline(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(inline).join(", ")}]`;
  if (value !== null && typeof value === "object") {
    return `{${Object.entries(value).map(([k, v]) => `${JSON.stringify(k)}: ${inline(v)}`).join(", ")}}`;
  }
  return JSON.stringify(value);
}

/** An object inline when it has one key, else one key per line with inline values. */
function block(o: Record<string, unknown>): string {
  const keys = Object.keys(o);
  if (keys.length <= 1) return inline(o);
  return `{\n${keys.map((k) => `  ${JSON.stringify(k)}: ${inline(o[k])}`).join(",\n")}\n}`;
}

/** The `format` a Vega or Vega-Lite `data` entry needs to read the file, if any. */
function dataFormat(d: Dataset, vega: boolean): Record<string, unknown> | undefined {
  if (d.format === "topojson" && d.objects?.[0]) return { type: "topojson", feature: d.objects[0] };
  if (d.format === "geojson") return { type: "json", property: "features" };
  // Vega-Lite parses CSV and TSV types by itself; Vega reads them as text unless told.
  if (vega && (d.format === "csv" || d.format === "tsv")) return { type: d.format, parse: "auto" };
  return undefined;
}

/**
 * How to load the file, one snippet per tool (the URL shows above them): Vega-Lite and
 * Vega `data` entries (formats they read); Altair and the npm package (released files
 * only, since both follow npm releases).
 */
export function useSnippets(d: Dataset): Snippet[] {
  const out: Snippet[] = [];
  const v = variable(d);
  if (VL_FORMATS.has(d.format)) {
    const vl = dataFormat(d, false);
    out.push({ name: "Vega-Lite", code: `"data": ${block({ url: d.url, ...(vl ? { format: vl } : {}) })}` });
    const vg = dataFormat(d, true);
    out.push({ name: "Vega", code: `"data": [${block({ name: d.name, url: d.url, ...(vg ? { format: vg } : {}) })}]` });
  }
  if (isReleased(d)) {
    out.push({
      name: "Altair",
      code: `from altair.datasets import data\n\n${d.kind === "table" ? `${v} = data.${d.name}()` : `url = data.${d.name}.url`}`,
    });
    const parsed = d.format === "json" || d.format === "csv";
    out.push({
      name: "JavaScript",
      code: `import data from 'vega-datasets';\n\n${parsed ?`const ${v} = await data['${d.file}']();` : `const url = data['${d.file}'].url;`}`,
    });
  }
  return out;
}

export function fileName(d: Dataset): string {
  return d.file.split("/").pop() ?? d.file;
}

export function formatDescription(d: Dataset): string {
  const label = FORMAT_LABEL[d.format] ?? d.format.toUpperCase();
  if (d.format === "json" && d.kind === "table") return "JSON, array of records";
  if (d.kind === "file") return `${label} image`;
  return label;
}

export function sizeDescription(d: Dataset): string {
  return [formatBytes(d.bytes), d.rows !== null ? `${formatCount(d.rows)} rows` : null].filter(Boolean).join(" · ");
}

/** Link text for a URL: its file name if it has one, else its host. */
export function linkText(url: string): string {
  try {
    const u = new URL(url);
    const last = u.pathname.split("/").filter(Boolean).pop() ?? "";
    return last.includes(".") ? last : u.hostname;
  } catch {
    return url;
  }
}

/** Examples in gallery turns (Vega-Lite, Vega, Altair, Vega-Lite, …) so "All" shows every gallery up front. */
export function interleave(examples: Example[], galleries: readonly Gallery[] = GALLERIES): Example[] {
  const queues = galleries.map((g) => examples.filter((e) => e.gallery === g));
  const out: Example[] = [];
  for (let i = 0; out.length < examples.length; i++) {
    for (const q of queues) if (q[i]) out.push(q[i]!);
  }
  return out;
}
