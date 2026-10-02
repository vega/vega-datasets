/**
 * "Try this dataset": build a small, sensible Vega-Lite starter chart from a dataset's
 * schema and field profiles, and open it in the Vega Editor.
 *
 * The rules, in order: maps for geographic files and for latitude/longitude columns;
 * start/end ranges as a timeline; time series as lines; two measures as a scatter
 * plot; a measure by category as bars; then a histogram or category counts.
 * Identifier and code columns are never plotted as measurements.
 */
import LZString from "lz-string";
import { categoryLabels, categoryValues, type Dataset, documentedRange, effectiveMissing, type Field, orderedCategories } from "./catalog";

type Spec = Record<string, unknown>;
type Enc = Record<string, unknown>;

const EDITOR = "https://vega.github.io/editor/#/url/vega-lite/";
const SCHEMA = "https://vega.github.io/schema/vega-lite/v6.json";

/** Vega-Lite treats `.` and `[ ]` in field names as nested access; escape them. */
export function fieldRef(name: string): string {
  return name.replace(/([.[\]])/g, "\\$1");
}

// What a field's metadata adds to an encoding of it. Each addition needs its property,
// so an undescribed field encodes exactly as before.

/** The field's title for an axis, legend or tooltip; Vega-Lite's own "Mean of …" for a mean. */
export function titled(f: Field, enc: Enc = {}): Enc {
  return f.title ? { title: enc.aggregate === "mean" ? `Mean of ${f.title}` : f.title } : {};
}

// Text from the metadata inside a Vega expression. Vega refuses a string literal that names a
// JavaScript object property ("toString", "__proto__", "constructor"), so each one goes in
// behind a prefix that no such name has, and is compared with the prefixed text of a value.
const TAG = "v:";

/** Texts as an array literal of prefixed strings, for `indexof(…, tag(expr))`. */
export function tagged(texts: string[]): string {
  return JSON.stringify(texts.map((t) => TAG + t));
}

/** An expression's value as prefixed text (numbers too: -99 becomes "v:-99"). */
export function tag(expr: string): string {
  return `"${TAG}" + ${expr}`;
}

/** A prefixed text back as the text. */
export function untag(expr: string): string {
  return `slice(${expr}, ${TAG.length})`;
}

/**
 * An expression that shows each category's label in place of its value, looked up in
 * arrays (no object literal), so any value is safe and the CSP-safe interpreter reads it.
 */
export function labelExpr(labels: [string, string][]): string {
  const at = `indexof(${tagged(labels.map(([v]) => v))}, ${tag("datum.label")})`;
  return `${at} < 0 ? datum.label : ${untag(`${tagged(labels.map(([, l]) => l))}[${at}]`)}`;
}

type Range = ReturnType<typeof documentedRange>;

/** The bounds of `r` on zero's side (a minimum at or below it, a maximum at or above it); null when none is. */
function zeroSide(r: Range): Range {
  if (!r) return null;
  const min = r.min !== undefined && r.min <= 0 ? r.min : undefined;
  const max = r.max !== undefined && r.max >= 0 ? r.max : undefined;
  if (min === undefined && max === undefined) return null;
  return { ...(min !== undefined ? { min } : {}), ...(max !== undefined ? { max } : {}), fits: r.fits };
}

/**
 * A number field on a channel. A documented range that every value lies inside becomes
 * the scale's bounds (a histogram's bin extent, when both ends are documented). A bar's
 * length starts at zero, so for `bars` a bound on the far side of zero is left out: the
 * bars would start off the plot.
 */
export function measure(f: Field, enc: Enc = {}, bars = false): Enc {
  const out: Enc = { field: fieldRef(f.name), type: "quantitative", ...enc };
  const range = bars ? zeroSide(documentedRange(f)) : documentedRange(f);
  if (range?.fits && out.bin) {
    if (range.min !== undefined && range.max !== undefined) out.bin = { ...(out.bin as Enc), extent: [range.min, range.max] };
  } else if (range?.fits) {
    out.scale = {
      ...(out.scale as Enc | undefined),
      ...(range.min !== undefined ? { domainMin: range.min } : {}),
      ...(range.max !== undefined ? { domainMax: range.max } : {}),
    };
  }
  return { ...out, ...titled(f, out) };
}

/**
 * The documented order as a Vega-Lite `sort` array of text, or null. Text that names an
 * object property can't go in (Vega refuses the literal in the sort expression Vega-Lite
 * writes), so such categories keep the default order. Numbered categories are sorted as
 * text, and `categoryAsText` makes the field's values text to match: a file may hold them
 * as numbers, as text (CSV), or both, and the sort compares strictly.
 */
function sortOrder(f: Field): string[] | null {
  const order = orderedCategories(f)?.map(String);
  return order && !order.some((v) => v in Object.prototype) ? order : null;
}

/** The transform that makes an ordered, numbered category's values text (null stays null), or null when none is needed. */
export function categoryAsText(f: Field): Enc | null {
  const numbered = orderedCategories(f)?.some((v) => typeof v === "number");
  return numbered && sortOrder(f) ? { calculate: `toString(datum[${JSON.stringify(f.name)}])`, as: f.name } : null;
}

/**
 * A category on a channel, with labels on its axis or legend. When the metadata says the
 * order matters, the documented order replaces `enc.sort` (and so sets the color domain's
 * order), and an axis reads it as ordinal. Colors stay nominal: an ordinal ramp would fade
 * the first category into the background.
 */
export function category(f: Field, enc: Enc = {}, guide: "axis" | "legend" = "legend"): Enc {
  const order = sortOrder(f);
  const labels = categoryLabels(f);
  return {
    field: fieldRef(f.name),
    type: order && guide === "axis" ? "ordinal" : "nominal",
    ...enc,
    ...(order ? { sort: order } : {}),
    ...titled(f),
    ...(labels ? { [guide]: { labelExpr: labelExpr(labels) } } : {}),
  };
}

/** A marker as a value may hold it: its text, and for a number the number's own text ("-99.0" is -99 once parsed). */
export function markerForms(f: Field, markers: string[]): string[] {
  const numeric = f.type === "integer" || f.type === "number";
  return [...new Set(markers.flatMap((m) => (numeric && m.trim() !== "" && Number.isFinite(Number(m)) ? [m, String(Number(m))] : [m])))];
}


/**
 * A filter that leaves out the rows where any of `fields` holds one of its documented
 * missing-value markers, as the fields table's profile does; null when no field has
 * markers declared, so an undescribed chart stays as it was.
 */
export function missingFilter(d: Dataset, fields: Field[]): Enc | null {
  const tests = fields.flatMap((f) => {
    const markers = effectiveMissing(d, f);
    if (!markers?.length) return [];
    return [`indexof(${tagged(markerForms(f, markers))}, ${tag(`datum[${JSON.stringify(f.name)}]`)}) < 0`];
  });
  return tests.length ? { filter: tests.join(" && ") } : null;
}

/**
 * The starter chart with what its encoded fields' metadata asks of the data: the rows they
 * mark as missing left out, and ordered numbered categories made text. Markers are matched
 * on a value's text, as Table Schema says, so a date field with markers is read as text
 * (`parse: null`) and parsed after the filter (`toDate`, as Vega-Lite's own parse does).
 * Without such metadata the spec is unchanged.
 */
function withMetadata(d: Dataset, spec: Spec | null): Spec | null {
  const encoding = spec?.encoding as Record<string, Enc> | undefined;
  if (!spec || !encoding) return spec;
  const used = new Set(Object.values(encoding).map((e) => e.field));
  const fields = d.fields.filter((f) => used.has(fieldRef(f.name)));
  const dates = fields.filter((f) => f.profile.kind === "temporal" && effectiveMissing(d, f)?.length);
  const transform = [
    missingFilter(d, fields),
    ...dates.map((f) => ({ calculate: `toDate(datum[${JSON.stringify(f.name)}])`, as: f.name })),
    ...fields.map(categoryAsText),
  ].filter((t) => t !== null);
  if (!transform.length) return spec;
  const data = spec.data as Spec;
  const parse = dates.length ? { format: { ...(data.format as Spec | undefined), parse: Object.fromEntries(dates.map((f) => [f.name, null])) } } : {};
  return { ...spec, data: { ...data, ...parse }, transform };
}

const ID_NAME = /(^id$|_id$|^id_|code$|^code|^zip|zip_code|^key$|^index$|^cluster$|^source$|^target$|^group$|^fips)/i;
const ID_DESC = /\b(identifier|unique id|fips|code for|index of)\b/i;
const YEAR_NAME = /^(year|yr)$|year$/i;
const TIME_PART = /^(month|day|hour|minute|weekday)$/i;
/** Integer columns that group rows (age bands, sex codes) rather than measure them. */
const GROUPING = /^(age|sex|rank|level|grade)$/i;
const LAT = /^(lat|latitude)$/i;
const LON = /^(lon|lng|long|longitude)$/i;
const SERIES = /^(symbol|source|location|country|region|series|sex|gender|division|entity|variety|site|origin|species|type|category)$/i;

/** Numeric identifiers and codes: plotting them as measurements is meaningless. */
function isId(f: Field): boolean {
  if (ID_NAME.test(f.name)) return true;
  return f.profile.kind === "quantitative" && (/categor/i.test(f.name) || ID_DESC.test(f.description ?? ""));
}

export function isYear(f: Field): boolean {
  const p = f.profile;
  return p.kind === "quantitative" && !integerCategory(f) && Number.isInteger(p.min) && p.min >= 1000 && p.max <= 2200 && (YEAR_NAME.test(f.name) || f.type === "integer");
}

/** Small-range integers (cylinders, ratings, ages in bands) behave like categories, not measures. */
function isOrdinalInt(f: Field): boolean {
  const p = f.profile;
  return p.kind === "quantitative" && f.type === "integer" && p.max - p.min <= 12;
}

/** Integers the metadata documents as categories (grades 1–3, with labels): groups, not measures. */
function integerCategory(f: Field): boolean {
  return f.type === "integer" && f.profile.kind === "quantitative" && categoryValues(f) !== null;
}

/** Quantities worth plotting on an axis (not identifiers, years, codes, coordinates or documented categories). */
export function isMeasure(f: Field): boolean {
  return (
    f.profile.kind === "quantitative" &&
    !integerCategory(f) &&
    !isId(f) &&
    !isYear(f) &&
    !isOrdinalInt(f) &&
    !TIME_PART.test(f.name) &&
    !(f.type === "integer" && GROUPING.test(f.name)) &&
    !LAT.test(f.name) &&
    !LON.test(f.name)
  );
}

/** A category with between 2 and `max` values (identifiers excluded); an integer category counts its documented values. */
export function nominal(f: Field, max: number): boolean {
  const n = f.profile.kind === "nominal" ? f.profile.distinct : integerCategory(f) ? categoryValues(f)!.length : 0;
  return n >= 2 && n <= max && !ID_NAME.test(f.name);
}

function spanYears(f: Field): number {
  const p = f.profile;
  if (p.kind !== "temporal") return 0;
  return (new Date(p.max).getTime() - new Date(p.min).getTime()) / (365.25 * 864e5);
}

const PROJECTION: Record<string, string> = {
  us_10m: "albersUsa",
  world_110m: "equalEarth",
  london_boroughs: "mercator",
  london_tube_lines: "mercator",
  earthquakes: "equalEarth",
};

function geoFile(d: Dataset, base: Spec): Spec | null {
  if (d.format === "topojson") {
    const feature = d.objects?.[0];
    if (!feature) return null;
    return {
      ...base,
      width: 600,
      height: 400,
      data: { url: d.url, format: { type: "topojson", feature } },
      projection: { type: PROJECTION[d.name] ?? "equalEarth" },
      // Thousands of shapes: screen readers get the chart's description, not each one.
      mark: { type: "geoshape", stroke: "white", strokeWidth: 0.5, aria: false },
    };
  }
  return {
    ...base,
    width: 600,
    height: 360,
    data: { url: d.url, format: { type: "json", property: "features" } },
    projection: { type: PROJECTION[d.name] ?? "equalEarth" },
    mark: { type: "geoshape", aria: false },
  };
}

function pointMap(d: Dataset, base: Spec, lat: Field, lon: Field, color: Field | undefined): Spec {
  const la = lat.profile;
  const lo = lon.profile;
  // Mostly-US coordinates read best on the Albers USA projection.
  const us =
    la.kind === "quantitative" && lo.kind === "quantitative" &&
    lo.min >= -180 && lo.max <= -60 && la.min >= 15 && la.max <= 72;
  return {
    ...base,
    width: 600,
    height: 380,
    projection: { type: us ? "albersUsa" : "equalEarth" },
    mark: { type: "circle", size: (d.rows ?? 0) > 5000 ? 4 : 16, opacity: 0.7, tooltip: true },
    encoding: {
      longitude: { field: fieldRef(lon.name), type: "quantitative", ...titled(lon) },
      latitude: { field: fieldRef(lat.name), type: "quantitative", ...titled(lat) },
      ...(color ? { color: category(color) } : {}),
    },
  };
}

export function starterSpec(d: Dataset): Spec | null {
  return withMetadata(d, starterRule(d));
}

function starterRule(d: Dataset): Spec | null {
  const base: Spec = {
    $schema: SCHEMA,
    description: `Starter chart for ${d.name} from vega-datasets. Edit freely.`,
    data: { url: d.url },
  };
  if (d.format === "topojson" || d.format === "geojson") return geoFile(d, base);
  if (d.kind !== "table" || d.fields.length === 0) return null;
  if (d.format === "parquet" || d.format === "arrow") return null; // Vega-Lite needs extra loaders for these.

  const fields = d.fields.filter((f) => f.type !== "array");
  const rows = d.rows ?? 0;
  const measures = fields.filter(isMeasure);
  const temporal = fields.filter((f) => f.profile.kind === "temporal");
  const years = fields.filter(isYear);
  const smallCat = fields.find((f) => nominal(f, 10));
  const seriesCat = fields.find((f) => nominal(f, 12) && SERIES.test(f.name));
  const cat = fields.find((f) => nominal(f, 60));
  const colorBy = (f: Field | undefined): Enc => (f ? { color: category(f) } : {});

  // 1. Latitude/longitude columns → a point map.
  const lat = fields.find((f) => LAT.test(f.name) && f.profile.kind === "quantitative");
  const lon = fields.find((f) => LON.test(f.name) && f.profile.kind === "quantitative");
  if (lat && lon) return pointMap(d, base, lat, lon, smallCat);

  // 2. start/end columns → a timeline of ranges.
  const start = fields.find((f) => /^start$/i.test(f.name) && f.profile.kind === "quantitative");
  const end = fields.find((f) => /^end$/i.test(f.name) && f.profile.kind === "quantitative");
  const label = fields.find((f) => nominal(f, 80));
  if (start && end && label) {
    return {
      ...base,
      width: 520,
      mark: { type: "bar", tooltip: true },
      encoding: {
        // Ranges read in time order, whatever order the labels are documented in.
        y: { field: fieldRef(label.name), type: "nominal", sort: { field: fieldRef(start.name) }, ...titled(label) },
        x: { field: fieldRef(start.name), type: "quantitative", scale: { zero: false }, axis: { format: "d" }, ...titled(start) },
        x2: { field: fieldRef(end.name) },
      },
    };
  }

  const [m1, m2] = measures;

  // 3. Dates or years with a measure → a time series.
  const t = temporal[0];
  if (t && m1) {
    const unit = rows > 1000 ? (spanYears(t) > 20 ? "year" : "yearmonth") : undefined;
    return {
      ...base,
      width: 640,
      height: 300,
      mark: { type: "line", interpolate: "monotone", tooltip: true },
      encoding: {
        x: { field: fieldRef(t.name), type: "temporal", ...(unit ? { timeUnit: unit } : {}), ...titled(t) },
        y: measure(m1, unit || seriesCat ? { aggregate: "mean" } : {}),
        ...colorBy(seriesCat),
      },
    };
  }
  const y = years[0];
  if (y && m1) {
    return {
      ...base,
      width: 640,
      height: 300,
      mark: { type: "line", point: rows <= 60, tooltip: true },
      encoding: {
        x: measure(y, { scale: { zero: false }, axis: { format: "d" } }),
        y: measure(m1, { aggregate: "mean" }),
        ...colorBy(seriesCat),
      },
    };
  }

  // 4. Two measures → a scatter plot.
  if (m1 && m2) {
    return {
      ...base,
      width: 480,
      height: 360,
      mark: { type: "point", tooltip: true, opacity: rows > 5000 ? 0.3 : 0.8 },
      encoding: {
        x: measure(m1, { scale: { zero: false } }),
        y: measure(m2, { scale: { zero: false } }),
        ...colorBy(smallCat),
      },
    };
  }

  // 5. A measure by category → sorted bars.
  if (m1 && cat) {
    return {
      ...base,
      width: 480,
      mark: { type: "bar", tooltip: true },
      encoding: {
        y: category(cat, { sort: "-x" }, "axis"),
        x: measure(m1, { aggregate: "mean" }, true),
      },
    };
  }

  // 6. One measure → a histogram.
  if (m1) {
    return {
      ...base,
      width: 480,
      height: 260,
      mark: { type: "bar", tooltip: true },
      encoding: {
        x: measure(m1, { bin: { maxbins: 30 } }),
        y: { aggregate: "count", type: "quantitative" },
      },
    };
  }

  // 7. Only categories → counts.
  if (cat) {
    return {
      ...base,
      width: 480,
      mark: { type: "bar", tooltip: true },
      encoding: {
        y: category(cat, { sort: "-x" }, "axis"),
        x: { aggregate: "count", type: "quantitative" },
      },
    };
  }
  return null;
}

/** A Vega Editor link that opens `spec` (Vega-Lite). */
export function editorUrl(spec: Spec): string {
  return EDITOR + LZString.compressToEncodedURIComponent(JSON.stringify(spec, null, 2));
}
