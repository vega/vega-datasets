/**
 * How the page runs the exact spec it shows, public data URL included, under its CSP
 * (connect-src 'self', no 'unsafe-eval'). Two documented Vega hooks, with no DOM here so
 * they are unit-tested; client/embed.ts installs them:
 * - `vega.formats()`: CSV and TSV readers that build rows without compiling code. Vega's
 *   own readers use d3-dsv's `parse`, which compiles a row converter with `new Function`.
 * - a Vega loader that fetches a public vega-datasets URL from the site's own `data/`.
 */
import { dsvFormat } from "d3-dsv";

type Row = Record<string, string>;

/** The format options Vega's delimited readers take (`parse` is applied by Vega after reading). */
export interface DsvOptions {
  delimiter?: string;
  /** Column names for a file without a header row. */
  header?: readonly string[];
}

/**
 * Rows as objects, as Vega's delimited reader returns them (d3-dsv's `parse`), but built
 * without `new Function`: `parseRows` compiles nothing. With `header`, every line is a row.
 */
export function dsvRows(text: string, delimiter: string, header?: readonly string[]): Row[] {
  const lines = dsvFormat(delimiter).parseRows(text);
  const [columns = [], ...rows] = header ? [header.map(String), ...lines] : lines;
  return rows.map((r) => Object.fromEntries(columns.map((c, i) => [c, r[i] ?? ""])));
}

type Reader = ((text: string, format?: DsvOptions) => Row[]) & { responseType: "text" };

/** A reader for `vega.formats(name, reader)` that asks the loader for text, as Vega's do. */
function reader(read: (text: string, format: DsvOptions) => Row[]): Reader {
  return Object.assign((text: string, format: DsvOptions = {}) => read(String(text), format), { responseType: "text" as const });
}

/**
 * The readers to register. As in Vega, "csv" and "tsv" fix their delimiter (a `delimiter`
 * option is ignored), and "dsv" takes it from the format.
 */
export function readers(): Record<"csv" | "tsv" | "dsv", Reader> {
  return {
    csv: reader((text, f) => dsvRows(text, ",", f.header)),
    tsv: reader((text, f) => dsvRows(text, "	", f.header)),
    dsv: reader((text, f) => dsvRows(text, f.delimiter ?? ",", f.header)),
  };
}

/** A vega-datasets data URL as specs publish it: a jsDelivr release, or GitHub Pages. */
export const PUBLIC_DATA = /^https:\/\/(?:cdn\.jsdelivr\.net\/npm\/vega-datasets@[^/]+|vega\.github\.io\/vega-datasets)\/data\//;

/**
 * Where the page fetches `uri` from: a public vega-datasets data URL becomes the same file
 * under `siteData` (the site's own `data/`, an absolute URL ending in a slash); any other
 * URI is left as it is.
 */
export function siteDataUri(uri: string, siteData: string): string {
  return uri.replace(PUBLIC_DATA, siteData);
}

interface VegaMark {
  type?: string;
  from?: { data?: string; facet?: unknown };
  marks?: VegaMark[];
}

/**
 * The dataset the scatter plot's points draw from, in the compiled Vega spec: the rows
 * left after its filters (both values present), whose length is the caption's count.
 */
export function pointSource(vg: { marks?: VegaMark[] }): string | null {
  for (const m of vg.marks ?? []) {
    if (m.type === "symbol" && m.from?.data) return m.from.data;
    const inner = pointSource(m);
    if (inner) return inner;
  }
  return null;
}
