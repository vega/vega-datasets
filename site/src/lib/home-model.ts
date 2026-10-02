/**
 * What the home page shows, as plain data: counts, the catalog chart's rows, and
 * the card list after search, filters and sort. No DOM, so it is unit-tested.
 */
import { Catalog, type CatalogFile, type Dataset, type Example, type Gallery, GALLERIES, GALLERY_LABEL } from "./catalog";

/** The chart's color groups: the three common formats, everything else together. */
export const FORMAT_GROUPS = ["JSON", "CSV", "TopoJSON", "Other"] as const;
export type FormatGroup = (typeof FORMAT_GROUPS)[number];

/** tableau10 colors that keep the four format groups distinct. */
export const FORMAT_COLORS: Record<FormatGroup, string> = {
  JSON: "#54a24b",
  CSV: "#b279a2",
  TopoJSON: "#9d755d",
  Other: "#bab0ac",
};

export function formatGroup(d: Dataset): FormatGroup {
  if (d.format === "json") return "JSON";
  if (d.format === "csv") return "CSV";
  if (d.format === "topojson") return "TopoJSON";
  return "Other";
}

export type Sort = "used" | "az" | "size";
export const SORT_LABEL: Record<Sort, string> = { used: "Most Used", az: "A to Z", size: "Largest" };
export const SORT_NOTE: Record<Sort, string> = { used: "Most used first", az: "A to Z", size: "Largest first" };

/** A chart brush, in data units: file size in bytes and gallery examples. */
export interface Brush {
  bytes: [number, number];
  examples: [number, number];
}

export interface Filters {
  query: string;
  formats: ReadonlySet<FormatGroup>;
  galleries: ReadonlySet<Gallery>;
  brush: Brush | null;
  sort: Sort;
}

export const NO_FILTERS: Filters = { query: "", formats: new Set(), galleries: new Set(), brush: null, sort: "used" };

/** No gallery selected means all galleries; multiple selections combine their examples. */
export function usageCount(c: Catalog, d: Dataset, galleries: ReadonlySet<Gallery>): number {
  if (!galleries.size) return d.usedBy.length;
  const usage = c.usage(d);
  return GALLERIES.reduce((n, g) => n + (galleries.has(g) ? usage[g] : 0), 0);
}

export function usageTitle(galleries: ReadonlySet<Gallery>): string {
  return galleries.size && galleries.size < GALLERIES.length
    ? `${GALLERIES.filter((g) => galleries.has(g)).map((g) => GALLERY_LABEL[g]).join(" + ")} examples`
    : "Gallery examples";
}

export function isFiltered(f: Filters): boolean {
  return f.query.trim() !== "" || f.formats.size > 0 || f.brush !== null;
}

function within(v: number, [lo, hi]: [number, number]): boolean {
  return v >= Math.min(lo, hi) && v <= Math.max(lo, hi);
}

/** Search matches a dataset's name, its title, its field names and its description. */
function matches(d: Dataset, needle: string): boolean {
  return d.name.toLowerCase().includes(needle)
    || (d.title?.toLowerCase().includes(needle) ?? false)
    || d.fields.some((f) => f.name.toLowerCase().includes(needle))
    || d.description.toLowerCase().includes(needle);
}

/** Search, format and brush narrow the list. Galleries choose the counts, keeping zeros. */
export function listDatasets(c: Catalog, f: Filters): Dataset[] {
  const needle = f.query.trim().toLowerCase();
  const uses = new Map(c.datasets.map((d) => [d.name, usageCount(c, d, f.galleries)]));
  const list = c.datasets.filter((d) => {
    if (needle && !matches(d, needle)) return false;
    if (f.formats.size && !f.formats.has(formatGroup(d))) return false;
    if (f.brush && !(within(d.bytes ?? 0, f.brush.bytes) && within(uses.get(d.name)!, f.brush.examples))) return false;
    return true;
  });
  // c.datasets is A to Z, and sort() is stable, so ties stay alphabetical.
  if (f.sort === "used") list.sort((a, b) => uses.get(b.name)! - uses.get(a.name)!);
  if (f.sort === "size") list.sort((a, b) => (b.bytes ?? 0) - (a.bytes ?? 0));
  return list;
}

/**
 * The datasets the search and chips match, ignoring the brush: the chart shows these at
 * full strength, and the brush then narrows the cards within them. Search and format
 * chips don't move the axes; changing galleries recomputes the chart and clears its brush.
 */
export function baseMatches(c: Catalog, f: Filters): Dataset[] {
  return listDatasets(c, { ...f, brush: null });
}

export interface HomeCounts {
  datasets: number;
  examples: number;
  /** Examples that load at least one vega-datasets file. */
  examplesWithData: number;
  formats: Record<FormatGroup, number>;
  /** Datasets that each gallery uses at least once. */
  galleries: Record<Gallery, number>;
}

/** Datasets per format group (the format chips' counts). */
export function formatCounts(c: Catalog): Record<FormatGroup, number> {
  const formats = Object.fromEntries(FORMAT_GROUPS.map((g) => [g, 0])) as Record<FormatGroup, number>;
  for (const d of c.datasets) formats[formatGroup(d)]++;
  return formats;
}

export function homeCounts(c: Catalog): HomeCounts {
  const formats = formatCounts(c);
  const galleries: Record<Gallery, number> = { vega: 0, "vega-lite": 0, altair: 0 };
  for (const d of c.datasets) {
    const usage = c.usage(d);
    for (const g of GALLERIES) if (usage[g] > 0) galleries[g]++;
  }
  return {
    datasets: c.datasets.length,
    examples: c.examples.length,
    examplesWithData: c.examples.filter((e) => e.datasets.length > 0).length,
    formats,
    galleries,
  };
}

export interface ChartRow {
  name: string;
  bytes: number;
  size: string;
  total: number;
  usage: Record<Gallery, number>;
  format: FormatGroup;
  href: string;
}

/** Each dataset's point on the catalog chart; `href` opens its page (relative to the home page). */
export function chartRows(c: Catalog, size: (bytes: number) => string): ChartRow[] {
  return c.datasets
    .filter((d) => d.bytes !== null && d.bytes > 0)
    .map((d) => ({
      name: d.name,
      bytes: d.bytes!,
      size: size(d.bytes!),
      total: d.usedBy.length,
      usage: c.usage(d),
      format: formatGroup(d),
      href: `datasets/${encodeURIComponent(d.name)}/`,
    }));
}

/**
 * The catalog, cut down to what the home page's search, chips, sort and chart read
 * (served as home-index.json): each dataset's name, format, size, row count, title (when it
 * has one), description, field names and the examples that use it, and each such example's gallery.
 */
export interface HomeIndex {
  package: CatalogFile["package"];
  datasets: (Pick<Dataset, "name" | "title" | "format" | "kind" | "bytes" | "rows" | "description" | "usedBy"> & { fields: { name: string }[] })[];
  examples: Pick<Example, "id" | "gallery">[];
}

export function homeIndex(c: Catalog): HomeIndex {
  const used = new Set(c.datasets.flatMap((d) => d.usedBy));
  return {
    package: c.package,
    datasets: c.datasets.map((d) => ({
      name: d.name,
      format: d.format,
      kind: d.kind,
      bytes: d.bytes,
      rows: d.rows,
      ...(d.title ? { title: d.title } : {}),
      description: d.description,
      usedBy: d.usedBy,
      fields: d.fields.map((f) => ({ name: f.name })),
    })),
    examples: c.examples.filter((e) => used.has(e.id)).map((e) => ({ id: e.id, gallery: e.gallery })),
  };
}

/**
 * A Catalog over a HomeIndex: enough for listDatasets, baseMatches, usage, formatCounts
 * and chartRows (the functions the home page's script runs; not homeCounts, which needs
 * every example).
 */
export function indexCatalog(index: HomeIndex): Catalog {
  return new Catalog({ ...index, readme: "" } as unknown as CatalogFile);
}

/** A featured example and the dataset its thumbnail links to. */
export interface ShowcasePick {
  example: Example;
  dataset: string;
}

/**
 * Deliberately varied charts, rather than the first example of each popular dataset.
 * The first four also form the phone layout; the first six form the tablet layout.
 */
const FEATURED_EXAMPLES = [
  ["cars", "altair/scatter_matrix"],
  ["us_10m", "vega/county-unemployment"],
  ["stocks", "altair/line_chart_with_custom_legend"],
  ["penguins", "vega/violin-plot"],
  ["seattle_weather", "vega-lite/rect_heatmap_weather"],
  ["population", "vega/population-pyramid"],
  ["unemployment_across_industries", "vega-lite/stacked_area_stream"],
  ["movies", "altair/histogram_heatmap"],
  ["miserables", "vega/force-directed-layout"],
  ["barley", "altair/comet_chart"],
] as const;

/** Keep a useful link if a gallery removes a preferred example; never emit an empty image. */
export function showcase(c: Catalog): ShowcasePick[] {
  return FEATURED_EXAMPLES.flatMap(([dataset, id]) => {
    const d = c.dataset(dataset);
    if (!d) return [];
    const available = c.examplesFor(d).filter((e) => e.thumb && e.thumbSize);
    const example = available.find((e) => e.id === id) ?? available[0];
    return example ? [{ dataset, example }] : [];
  });
}

/** The first paragraph of a Markdown description as plain text, for a card. */
export function plainSummary(markdown: string): string {
  const first = markdown.trim().split(/\n\s*\n/)[0] ?? "";
  return first
    .replace(/!?\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/[*_`]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

/** One `## Heading` section of the README (without the heading), or null if it is gone. */
export function readmeSection(readme: string, heading: string): string | null {
  const lines = readme.split("\n");
  const start = lines.findIndex((l) => l.trim() === `## ${heading}`);
  if (start < 0) return null;
  const end = lines.findIndex((l, i) => i > start && l.startsWith("## "));
  return lines.slice(start + 1, end < 0 ? undefined : end).join("\n").trim();
}

/**
 * The dataset a legacy link names (`#cars`, from before each dataset had a page), or null:
 * for no fragment, a malformed one, or one that names no dataset (an About item's anchor).
 */
export function legacyDataset(hash: string, names: ReadonlySet<string>): string | null {
  let name: string;
  try {
    name = decodeURIComponent(hash.replace(/^#/, ""));
  } catch {
    return null;
  }
  return name && names.has(name) ? name : null;
}
