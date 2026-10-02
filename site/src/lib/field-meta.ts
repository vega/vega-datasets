/**
 * What the fields table says about a field's schema metadata, as plain text (unit-tested):
 * its documented range, values and rules, its format, and the table's keys. Each line
 * needs its property, so an undescribed field shows exactly what it did before.
 */
import { categoryValues, type Dataset, type Field, insideDocumented, missingMarkers, primaryKey } from "./catalog";
import { formatNumber } from "./format";

/** At most this many allowed values are listed; the rest are counted. */
const ENUM_SHOWN = 12;

const bound = (v: number | string) => (typeof v === "number" ? formatNumber(v) : v);

/** A missing-value marker as a reader sees it: the empty one has no text to show. */
const marker = (v: string) => (v === "" ? "empty" : v);

function rangeNote(f: Field): string | null {
  const { minimum, maximum } = f.constraints ?? {};
  if (minimum === undefined && maximum === undefined) return null;
  const text =
    minimum !== undefined && maximum !== undefined ? `Documented range ${bound(minimum)} – ${bound(maximum)}`
    : minimum !== undefined ? `Documented minimum ${bound(minimum)}`
    : `Documented maximum ${bound(maximum!)}`;
  return insideDocumented(f) === false ? `${text} (some values fall outside)` : text;
}

function categoriesNote(f: Field): string | null {
  const values = categoryValues(f);
  if (!values) return null;
  const list = values.map((c) => (c.label !== undefined && c.label !== String(c.value) ? `${c.value} (${c.label})` : String(c.value))).join(", ");
  return f.categoriesOrdered ? `Values, in order: ${list}` : `Values: ${list}`;
}

/** The `enum` constraint, unless it only repeats the categories. */
function enumNote(f: Field): string | null {
  const allowed = f.constraints?.enum;
  if (!allowed?.length) return null;
  const same = (a: string[], b: string[]) => a.length === b.length && a.every((v) => b.includes(v));
  const categories = categoryValues(f)?.map((c) => String(c.value));
  if (categories && same(allowed.map(String), categories)) return null;
  const more = allowed.length - ENUM_SHOWN;
  return `Allowed values: ${allowed.slice(0, ENUM_SHOWN).map(String).join(", ")}${more > 0 ? ` and ${more} more` : ""}`;
}

const characters = (n: number) => `${formatNumber(n)} character${n === 1 ? "" : "s"}`;

/** `minLength` and `maxLength`. */
function lengthNote(f: Field): string | null {
  const { minLength: min, maxLength: max } = f.constraints ?? {};
  const [lo, hi] = [typeof min === "number" ? min : undefined, typeof max === "number" ? max : undefined];
  if (lo !== undefined && hi !== undefined) return `Length ${formatNumber(lo)} – ${characters(hi)}`;
  if (lo !== undefined) return `At least ${characters(lo)}`;
  return hi !== undefined ? `At most ${characters(hi)}` : null;
}

/** Quiet notes under a field's description: documented range, values, rules and missing-value markers. */
export function fieldNotes(f: Field): string[] {
  const c = f.constraints ?? {};
  const missing = missingMarkers(f.missingValues);
  return [
    rangeNote(f),
    c.exclusiveMinimum !== undefined ? `Greater than ${bound(c.exclusiveMinimum as number | string)}` : null,
    c.exclusiveMaximum !== undefined ? `Less than ${bound(c.exclusiveMaximum as number | string)}` : null,
    categoriesNote(f),
    enumNote(f),
    lengthNote(f),
    typeof c.pattern === "string" ? `Pattern ${c.pattern}` : null,
    c.required ? "Required" : null,
    c.unique ? "Unique" : null,
    missing.length ? `Counted as missing: ${missing.map(marker).join(", ")}`
    : f.missingValues ? "No missing-value markers"
    : null,
  ].filter((n): n is string => n !== null);
}

/** The field's format, shown with its type when it says something ("default" and "any" don't). */
export function formatNote(f: Field): string | null {
  return f.format && f.format !== "default" && f.format !== "any" ? f.format : null;
}

/** Whether the field is (part of) the table's primary key. */
export function isKey(d: Dataset, f: Field): boolean {
  return primaryKey(d).includes(f.name);
}

/**
 * The schema's own missing-value markers, for the note under the table ("NA counts as
 * missing."); null when the schema has none, only Table Schema's default (empty cells),
 * or every field lists its own. When some fields do, the note says so.
 */
export function missingNote(d: Dataset): string | null {
  const markers = missingMarkers(d.missingValues);
  if (!markers.length || (markers.length === 1 && markers[0] === "")) return null;
  const inheriting = d.fields.filter((f) => f.missingValues === undefined).length;
  if (inheriting === 0) return null;
  const except = inheriting < d.fields.length ? ", except in fields that list their own markers" : "";
  const named = markers.map((m) => (m === "" ? "empty cells" : `“${m}”`));
  const text = named.length === 1 ? named[0]! : `${named.slice(0, -1).join(", ")} and ${named.at(-1)}`;
  return `${text.charAt(0).toUpperCase()}${text.slice(1)} ${named.length === 1 ? "counts" : "count"} as missing${except}.`;
}
