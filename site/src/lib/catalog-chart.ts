/**
 * The home page's catalog chart: every dataset by file size and gallery use,
 * colored by format. A real Vega-Lite spec, so "Open in Vega Editor" shows how
 * it is made. On wide screens an interval brush filters the cards below; on
 * phones a tap opens the dataset (href channel), with no brush to fight scrolling.
 *
 * The spec is drawn twice: to static SVG when the site is built (so the chart is
 * in the HTML), then live in the browser (client/catalog-chart.ts).
 */
import type { Brush, ChartRow } from "./home-model";
import { FORMAT_COLORS, FORMAT_GROUPS } from "./home-model";
import { GALLERIES, type Gallery } from "./catalog";
import type { CatalogLayout } from "./catalog-layout";

type Spec = Record<string, unknown>;

export interface ChartOptions {
  /** Offer the interval brush (wide screens only). */
  brush: boolean;
  height: number;
  /** Maximum number of the most used datasets to label; omit crowded labels. */
  labels: number;
  /** Initial parameter values, also used by standalone exports and the Editor. */
  galleries?: Gallery[];
  matched?: string[] | null;
  initialBrush?: Brush | null;
  /** The page uses format chips as its key; standalone charts need their own legend. */
  legend?: boolean;
  /** Font for the name labels (the page's mono stack). */
  monoFont: string;
  /** Page-only fixed geometry. Standalone charts retain native automatic layout. */
  layout?: CatalogLayout;
}

/** File sizes on the axis: decimal units at powers of ten. */
const BYTES_LABEL = "datum.value >= 1e6 ? datum.value / 1e6 + ' MB' : datum.value >= 1e3 ? datum.value / 1e3 + ' KB' : datum.value + ' B'";

/** Labels right of their point, or left of it near the right edge. */
const LABEL_FLIP = 5e5;

export function catalogSpec(rows: ChartRow[], o: ChartOptions): Spec {
  const fontSize = o.layout?.fontSize ?? 11;
  const selectedCount = GALLERIES.map((g) => `(indexof(galleries, '${g}') >= 0 ? datum.usage['${g}'] : 0)`).join(" + ");
  // Points outside the search and chip filters fade (the `matched` param, set by the page);
  // on wide screens, so do points outside the brush.
  const dim = {
    opacity: {
      condition: [
        { test: "matched && indexof(matched, datum.name) < 0", value: 0.1 },
        ...(o.brush ? [{ param: "brush", empty: true, value: 1 }] : []),
      ],
      value: o.brush ? 0.18 : 1,
    },
  };
  const x = {
    field: "bytes",
    type: "quantitative",
    scale: { type: "log", domain: [50, 2e7] },
    axis: { title: "File size (log scale)", values: [1e2, 1e3, 1e4, 1e5, 1e6, 1e7], labelExpr: BYTES_LABEL, grid: false, labelFontSize: fontSize, titleFontSize: fontSize },
  };
  const y = {
    field: "examples",
    type: "quantitative",
    scale: { type: "sqrt", zero: true },
    axis: { title: { expr: "[galleryTitle, '(square root scale)']" }, tickMinStep: 1, labelFontSize: fontSize, titleFontSize: fontSize },
  };
  const label = (test: string, align: "left" | "right") => ({
    transform: [{ filter: `datum.usageRank <= ${o.labels} && ${test}` }],
    // Names repeat the points' descriptions, so screen readers skip them.
    mark: { type: "text", align, dx: align === "left" ? 8 : -8, baseline: "middle", fontSize, font: o.monoFont, aria: false },
    encoding: {
      x, y,
      // Leave a text line between labels as the plot resizes. Compare consecutive
      // ranks across BOTH layers so equal counts and left/right labels cannot collide.
      // This stays in the public Vega-Lite spec, including exported/Editor charts.
      text: {
        condition: { test: `datum.usageRank === 1 || abs(scale('y', datum.previousExamples) - scale('y', datum.examples)) >= ${fontSize + 3}`, field: "name" },
        value: "",
      },
      href: { field: "href" }, ...dim,
    },
  });
  return {
    $schema: "https://vega.github.io/schema/vega-lite/v6.json",
    description: "Datasets by file size and example counts in the selected galleries, colored by format. Drag to filter the list; click a point to open its dataset.",
    width: "container",
    height: o.height,
    autosize: { type: "fit-x", contains: "padding" },
    // Fixed public Vega-Lite geometry removes server/browser font-metric differences.
    // Both renderers draw the same coordinates; CSS scales the entire SVG. Generous
    // padding includes two-line y titles, ticks, and the uppermost dataset label.
    ...(o.layout ? {
      width: o.layout.width,
      height: o.layout.height,
      padding: { left: 76, right: 12, top: 18, bottom: 48 },
      autosize: { type: "none", contains: "padding" },
    } : {}),
    data: { values: rows },
    params: [
      { name: "galleries", value: o.galleries ?? [] },
      { name: "galleryTitle", expr: "!length(galleries) || length(galleries) === 3 ? 'Gallery examples' : replace(replace(replace(join(galleries, ' + '), 'vega-lite', 'Vega-Lite'), 'vega', 'Vega'), 'altair', 'Altair') + ' examples'" },
      { name: "matched", value: o.matched ?? null },
    ],
    // Vega owns the recount, ranking and accessible descriptions, including zero-use datasets.
    transform: [
      { calculate: `!length(galleries) ? datum.total : ${selectedCount}`, as: "examples" },
      { window: [{ op: "row_number", as: "usageRank" }, { op: "lag", field: "examples", as: "previousExamples" }], sort: [{ field: "examples", order: "descending" }, { field: "name", order: "ascending" }] },
      { calculate: "galleryTitle", as: "scope" },
      { calculate: "datum.name + ': ' + datum.format + ', ' + datum.size + ', ' + galleryTitle + ': ' + datum.examples", as: "description" },
    ],
    layer: [
      {
        ...(o.brush ? { params: [{
          name: "brush",
          select: {
            type: "interval", encodings: ["x", "y"],
            clear: "dblclick, window:catalogclear",
          },
          ...(o.initialBrush ? { value: { x: o.initialBrush.bytes, y: o.initialBrush.examples } } : {}),
        }] } : {}),
        mark: { type: "circle", size: 64, opacity: 1 },
        encoding: {
          x,
          y,
          color: {
            field: "format",
            type: "nominal",
            title: "Format",
            scale: { domain: [...FORMAT_GROUPS], range: FORMAT_GROUPS.map((g) => FORMAT_COLORS[g]) },
            legend: o.legend ? { orient: "top", direction: "horizontal", columns: 2, title: "Format" } : null,
          },
          ...dim,
          href: { field: "href" },
          description: { field: "description" },
          tooltip: [
            { field: "name", title: "Dataset" },
            { field: "format", title: "Format" },
            { field: "size", title: "Size" },
            { field: "scope", title: "Counting" },
            { field: "examples", title: "Examples" },
          ],
        },
      },
      label(`datum.bytes <= ${LABEL_FLIP}`, "left"),
      label(`datum.bytes > ${LABEL_FLIP}`, "right"),
    ],
  };
}

/** The brush signal's value ({} when cleared) as a Brush, or null. */
export function toBrush(value: unknown): Brush | null {
  const v = value as { bytes?: number[]; examples?: number[] } | null;
  if (!v?.bytes || !v.examples || v.bytes.length !== 2 || v.examples.length !== 2) return null;
  return { bytes: [v.bytes[0]!, v.bytes[1]!], examples: [v.examples[0]!, v.examples[1]!] };
}
