/**
 * The Explore section's charts, as Vega-Lite specs (no DOM, so they are unit-tested):
 * a scatter plot of two measures picked with input bindings, and the starter chart
 * (starter.ts) for everything else — "Over Time" when it is a time series.
 */
import { type Dataset, documentedRange, effectiveMissing, type Field, fieldTitle } from "./catalog";
import { formatCount } from "./format";
import { BAND_POLICY, rowBand } from "./large-data";
import { category, categoryAsText, fieldRef, isMeasure, isYear, markerForms, missingFilter, nominal, starterSpec, tag, tagged, titled, untag } from "./starter";

type Spec = Record<string, unknown>;

export type Mode = "scatter" | "time" | "starter";
export const MODE_LABEL: Record<Mode, string> = { scatter: "Scatter", time: "Over Time", starter: "Chart" };

const SCHEMA = "https://vega.github.io/schema/vega-lite/v6.json";

export interface ScatterFields {
  measures: Field[];
  /** Colored, and isolated from the legend: a category with at most 10 values. */
  color: Field | undefined;
  /** Names the point in the tooltip: a category with many values (a car's name). */
  label: Field | undefined;
  /** A date or year column, shown in the tooltip. */
  time: Field | undefined;
}

export function scatterFields(d: Dataset): ScatterFields | null {
  if (d.kind !== "table" || d.format === "parquet" || d.format === "arrow") return null;
  const fields = d.fields.filter((f) => f.type !== "array");
  const measures = fields.filter(isMeasure);
  if (measures.length < 2) return null;
  return {
    measures,
    color: fields.find((f) => nominal(f, 10)),
    label: fields.find((f) => f.profile.kind === "nominal" && f.profile.distinct > 10),
    time: fields.find((f) => f.profile.kind === "temporal" || isYear(f)),
  };
}

/** A starter chart that is a line over dates or years. */
function isTimeSeries(spec: Spec | null): boolean {
  const mark = spec?.mark as { type?: string } | undefined;
  return mark?.type === "line";
}

/** The charts Explore offers for a dataset, in switch order; empty when none is possible. */
export function exploreModes(d: Dataset): Mode[] {
  const starter = starterSpec(d);
  // Maps (geographic files, latitude/longitude columns) show the map.
  if (starter?.projection) return ["starter"];
  if (scatterFields(d)) return isTimeSeries(starter) ? ["scatter", "time"] : ["scatter"];
  return starter ? ["starter"] : [];
}

export interface ScatterOptions {
  x: string;
  y: string;
  /** Scroll to zoom and drag to pan (not on phones, where it would trap page scrolling). */
  zoom: boolean;
  height: number;
}

/** The measures to start with: fields named x and y when there are both, else the first two, the first on y. */
export function defaultAxes(f: ScatterFields): { x: string; y: string } {
  const named = (axis: string) => f.measures.find((m) => m.name.toLowerCase() === axis);
  const [x, y] = [named("x"), named("y")];
  if (x && y) return { x: x.name, y: y.name };
  return { x: f.measures[1]!.name, y: f.measures[0]!.name };
}

/**
 * What the measures' metadata adds to the scatter plot, looked up by the picked field's
 * position among the measures in expressions (arrays, which the CSP-safe interpreter reads,
 * and which take any field name): their titles, and the documented ranges that every value
 * lies inside. A measure without a range keeps Vega-Lite's own "nice" domain, as it has
 * without metadata. Empty when no measure has either, so the spec stays as it was.
 */
function measureLookups(d: Dataset, measures: Field[]) {
  const at = (param: string) => `indexof(${tagged(measures.map((m) => m.name))}, ${tag(param)})`;
  const ranges = measures.map((m) => documentedRange(m)).map((r) => (r?.fits ? r : null));
  const mins = ranges.map((r) => r?.min ?? null);
  const maxs = ranges.map((r) => r?.max ?? null);
  const lookup = (values: unknown[], param: string) => `${JSON.stringify(values)}[${at(param)}]`;
  const titled = measures.some((m) => m.title);
  const markers = measures.map((m) => markerForms(m, effectiveMissing(d, m) ?? []));
  const drop = (param: string) => `indexof([${markers.map(tagged).join(", ")}][${at(param)}], ${tag(`datum[${param}]`)}) < 0`;
  return {
    /** Leaves out the rows whose picked measures hold a documented missing-value marker. */
    missing: markers.some((m) => m.length) ? { filter: `${drop("xField")} && ${drop("yField")}` } : null,
    labels: titled ? measures.map(fieldTitle) : null,
    title: (param: string) => (titled ? untag(`${tagged(measures.map(fieldTitle))}[${at(param)}]`) : param),
    bounds: (param: string): Spec => ({
      ...(mins.some((v) => v !== null) ? { domainMin: { expr: lookup(mins, param) } } : {}),
      ...(maxs.some((v) => v !== null) ? { domainMax: { expr: lookup(maxs, param) } } : {}),
      // Setting a bound turns Vega-Lite's default nice off for every pick; keep it for the unbounded.
      ...(ranges.some((r) => r) ? { nice: { expr: `!${lookup(ranges.map((r) => r !== null), param)}` } } : {}),
    }),
  };
}

/**
 * Two measures against each other. The x and y pickers are input bindings on the
 * xField and yField params, so they work the same in the Vega Editor; the axis titles
 * are text marks that read those params (an axis title can't).
 */
export function scatterSpec(d: Dataset, f: ScatterFields, o: ScatterOptions): Spec {
  const options = f.measures.map((m) => m.name);
  const meta = measureLookups(d, f.measures);
  const prepare = [meta.missing, f.color ? missingFilter(d, [f.color]) : null, f.color ? categoryAsText(f.color) : null].filter((t) => t !== null);
  const labels = meta.labels ? { labels: meta.labels } : {};
  const title = (param: string, place: Spec) => ({
    data: { values: [{}] },
    // Zoom (scale binding) clips every mark in the view; the titles sit outside the plot.
    mark: { type: "text", text: { expr: meta.title(param) }, fontWeight: "bold", fontSize: 11, clip: false, ...place },
  });
  const { opacity } = BAND_POLICY[rowBand(d.rows ?? 0)];
  const params: Spec[] = [];
  if (o.zoom) params.push({ name: "zoom", select: "interval", bind: "scales" });
  if (f.color) params.push({ name: "pick", select: { type: "point", fields: [f.color.name] }, bind: "legend" });
  // The plotted values need names no field of the file has: a calculate `as: "x"` would overwrite a
  // field called x (platformer_terrain) before the next calculate reads it.
  const taken = new Set(d.fields.map((m) => m.name));
  const free = (name: string): string => (taken.has(name) ? free(`_${name}`) : name);
  const [px, py] = [free("x"), free("y")];
  return {
    $schema: SCHEMA,
    description: `Two measures of ${d.name} from vega-datasets, picked with the x and y menus.`,
    width: "container",
    height: o.height,
    autosize: { type: "fit-x", contains: "padding" },
    data: { url: d.url },
    params: [
      { name: "xField", value: o.x, bind: { input: "select", options, ...labels, name: "x " } },
      { name: "yField", value: o.y, bind: { input: "select", options, ...labels, name: "y " } },
    ],
    layer: [
      {
        // The field is picked at run time, so Vega-Lite can't parse it up front (CSV values are strings).
        transform: [
          ...prepare,
          { calculate: "toNumber(datum[xField])", as: px },
          { calculate: "toNumber(datum[yField])", as: py },
          { filter: `isValid(datum.${px}) && isValid(datum.${py}) && isFinite(datum.${px}) && isFinite(datum.${py})` },
        ],
        params,
        mark: { type: "point", opacity: opacity },
        encoding: {
          x: { field: px, type: "quantitative", scale: { zero: false, ...meta.bounds("xField") }, axis: { title: null } },
          y: { field: py, type: "quantitative", scale: { zero: false, ...meta.bounds("yField") }, axis: { title: null } },
          ...(f.color
            ? {
                color: category(f.color),
                opacity: { condition: { param: "pick", empty: true, value: opacity }, value: 0.08 },
              }
            : {}),
          tooltip: [
            ...(f.label ? [{ field: fieldRef(f.label.name), type: "nominal", ...titled(f.label) }] : []),
            { field: px, type: "quantitative", title: "x" },
            { field: py, type: "quantitative", title: "y" },
            ...(f.color ? [{ field: fieldRef(f.color.name), type: "nominal", ...titled(f.color) }] : []),
            ...(f.time
              ? [{ field: fieldRef(f.time.name), type: f.time.profile.kind === "temporal" ? "temporal" : "quantitative", ...(isYear(f.time) ? { format: "d" } : {}), ...titled(f.time) }]
              : []),
          ],
        },
      },
      title("xField", { x: { expr: "width / 2" }, y: { expr: "height + 32" }, align: "center", baseline: "top" }),
      title("yField", { x: 0, y: -10, align: "left", baseline: "bottom" }),
    ],
  };
}

/** Does this dataset open on the density overview (a table past the points bands, with a scatter plot)? */
export function hasDensity(d: Dataset): boolean {
  return rowBand(d.rows ?? 0) === "density" && scatterFields(d) !== null;
}

/** The starter chart, sized to its column. */
export function starterChart(d: Dataset): Spec | null {
  const spec = starterSpec(d);
  if (!spec) return null;
  return { ...spec, width: "container", autosize: { type: "fit-x", contains: "padding" } };
}

/**
 * "Both fields have values in 398 of 406 rows." for the scatter caption, from the rows the
 * chart plots (read from the view after it runs); null until then, so the caption never
 * loads a file on its own (a large file waits for its button).
 */
export function bothValuesNote(d: Dataset, plotted: number | null): string | null {
  if (plotted === null || d.rows === null) return null;
  return `Both fields have values in ${formatCount(plotted)} of ${formatCount(d.rows)} rows.`;
}

/** The Vega-Lite features a spec uses, for the line under the chart. */
export function chartFeatures(spec: Spec): string[] {
  const out = ["Vega-Lite"];
  const text = JSON.stringify(spec);
  const has = (s: string) => text.includes(s);
  if (has('"bind":{"input"')) out.push("input binding");
  if (has('"bind":"scales"')) out.push("scale binding");
  if (has('"bind":"legend"')) out.push("legend binding");
  if (out.length > 1) return out;
  const mark = spec.mark as { type?: string } | string | undefined;
  const type = typeof mark === "string" ? mark : mark?.type;
  if (type) out.push(`${type} mark`);
  const projection = spec.projection as { type?: string } | undefined;
  if (projection?.type) out.push(`${projection.type} projection`);
  if (has('"timeUnit"')) out.push("time unit");
  for (const agg of ["mean", "sum", "count"]) if (has(`"aggregate":"${agg}"`)) out.push(`${agg} aggregate`);
  if (has('"bin"')) out.push("binning");
  if (has('"tooltip":true')) out.push("tooltip");
  return out;
}
