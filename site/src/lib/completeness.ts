/**
 * How fully a dataset is described,
 * shared by the dataset page (a quiet "Add" beside each undescribed field, one footer line)
 * and the status page for contributors (every dataset against the checklist).
 *
 * Counted as gaps: the dataset's `title`, `description`, a source, a known license, and a
 * `description` for every field of a table with a schema. Properties that apply only to
 * some datasets (`categories`, `constraints`, `missingValues`, `primaryKey`, `foreignKeys`,
 * a field `title` for a cryptic name) can't be judged automatically: they are reported as
 * documented when present, never as gaps.
 */
import type { Dataset, Field } from "./catalog";
import { parse } from "smol-toml";
import { licenseFamily } from "./catalog";

/** The dataset-level checklist, in the order the status page shows it. */
export type Check = "title" | "description" | "source" | "license";
export const CHECKS: readonly Check[] = ["title", "description", "source", "license"];
export const CHECK_LABEL: Record<Check, string> = {
  title: "Title",
  description: "Description",
  source: "Source",
  license: "License",
};

export interface Completeness {
  /** Whether each dataset-level item is filled in. */
  has: Record<Check, boolean>;
  /** The table's fields and which lack a description; null without a declared schema (maps, images, JSON trees, inferred columns). */
  fields: { total: number; undescribed: string[] } | null;
  /** Missing dataset-level items plus undescribed fields. */
  gaps: number;
  /** Properties that apply only where they fit, as present: shown for information, never counted. */
  documented: string[];
}

const filled = (text: string | null | undefined): boolean => typeof text === "string" && text.trim() !== "";

/** Whether a field has a description (whitespace alone doesn't count). */
export function hasDescription(f: Field): boolean {
  return filled(f.description);
}

const count = (n: number, one: string) => (n === 1 ? `${one} (1 field)` : `${one} (${n} fields)`);

/** The "where they apply" properties the dataset documents, in words. */
export function documented(d: Dataset): string[] {
  const n = (p: (f: Field) => boolean) => d.fields.filter(p).length;
  const out: string[] = [];
  const titles = n((f) => filled(f.title));
  const categories = n((f) => (f.categories?.length ?? 0) > 0);
  const constraints = n((f) => Object.keys(f.constraints ?? {}).length > 0);
  const missing = n((f) => f.missingValues !== undefined);
  if (titles) out.push(count(titles, "Field titles"));
  if (categories) out.push(count(categories, "Categories"));
  if (constraints) out.push(count(constraints, "Constraints"));
  if (d.missingValues !== undefined || missing) out.push(d.missingValues !== undefined ? "Missing values" : count(missing, "Missing values"));
  if (d.primaryKey !== undefined && d.primaryKey.length > 0) out.push("Primary key");
  if (d.foreignKeys?.length) out.push(d.foreignKeys.length === 1 ? "Foreign key" : `Foreign keys (${d.foreignKeys.length})`);
  return out;
}

export function completeness(d: Dataset): Completeness {
  const has: Record<Check, boolean> = {
    title: filled(d.title),
    description: filled(d.description),
    // A source counts when one is recorded; the status page
    // notes sources recorded without a link.
    source: d.sources.some((s) => filled(s.title) || filled(s.path)),
    license: licenseFamily(d) !== "Not specified",
  };
  // Field items apply to declared fields only: a table without a schema shows its columns, but
  // the metadata never named them.
  const fields = d.fields.length && !d.fieldsInferred ? { total: d.fields.length, undescribed: d.fields.filter((f) => !hasDescription(f)).map((f) => f.name) } : null;
  const gaps = CHECKS.filter((c) => !has[c]).length + (fields?.undescribed.length ?? 0);
  return { has, fields, gaps, documented: documented(d) };
}

/** Whether the dataset records sources but none with a link (information on the status page, not a gap). */
export function sourcesUnlinked(d: Dataset): boolean {
  return d.sources.length > 0 && !d.sources.some((s) => filled(s.path));
}

/** Datasets by number of gaps, most first, ties by name. */
export function byGaps<T extends { dataset: Dataset; status: Completeness }>(rows: T[]): T[] {
  return [...rows].sort((a, b) => b.status.gaps - a.status.gaps || a.dataset.name.localeCompare(b.dataset.name));
}

export interface Summary {
  datasets: number;
  /** Datasets with no gaps. */
  complete: number;
  /** Datasets missing each dataset-level item. */
  missing: Record<Check, number>;
  /** Fields of tables with a schema, and how many have a description. */
  fields: { total: number; described: number };
  /** Tables with a schema but no field description at all. */
  tablesWithoutDescriptions: number;
}

export function summarize(datasets: Dataset[]): Summary {
  const all = datasets.map(completeness);
  const missing = Object.fromEntries(CHECKS.map((c) => [c, all.filter((s) => !s.has[c]).length])) as Record<Check, number>;
  const tables = all.flatMap((s) => (s.fields ? [s.fields] : []));
  const total = tables.reduce((sum, f) => sum + f.total, 0);
  const undescribed = tables.reduce((sum, f) => sum + f.undescribed.length, 0);
  return {
    datasets: datasets.length,
    complete: all.filter((s) => s.gaps === 0).length,
    missing,
    fields: { total, described: total - undescribed },
    tablesWithoutDescriptions: tables.filter((f) => f.undescribed.length === f.total).length,
  };
}

// --- Where a dataset's metadata lives ----------------------------------------------------------

/** The metadata file contributors edit, relative to the repository root. */
export const ADDITIONS_FILE = "_data/datapackage_additions.toml";

type Quote = '"""' | "'''";

/** Where a multiline string closing with `quote` ends on `line` (just after its closing quotes), or -1. */
function closeMultiline(line: string, from: number, quote: Quote): number {
  for (let j = from; j < line.length; j++) {
    // Basic strings have escapes (\" is a quote, not a delimiter); literal strings don't.
    if (quote === '"""' && line[j] === "\\") {
      j++;
      continue;
    }
    if (line.startsWith(quote, j)) {
      // Up to two more quotes belong to the string: `""""` is a quote, then the close.
      let k = j + 3;
      while (k < j + 5 && line[k] === quote[0]) k++;
      return k;
    }
  }
  return -1;
}

/** The multiline string still open at the end of `line` (read from `from`, outside any string), if any. */
function openAtEnd(line: string, from: number): Quote | null {
  for (let i = from; i < line.length; i++) {
    const ch = line[i];
    if (ch === "#") return null;
    const quote: Quote | null = line.startsWith('"""', i) ? '"""' : line.startsWith("'''", i) ? "'''" : null;
    if (quote) {
      const end = closeMultiline(line, i + 3, quote);
      if (end < 0) return quote;
      i = end - 1;
    } else if (ch === '"' || ch === "'") {
      // A one-line string, to its closing quote (a basic string skips escaped characters).
      let j = i + 1;
      while (j < line.length && line[j] !== ch) j += ch === '"' && line[j] === "\\" ? 2 : 1;
      i = j;
    }
  }
  return null;
}

/**
 * A `[[resources]]` header in its plain form: the bare key, optional spaces inside and around
 * the brackets, an optional comment. The metadata file writes every header this way.
 */
const HEADER = /^\s*\[\[\s*resources\s*\]\]\s*(?:#.*)?$/;
/** Another array-of-tables header with a plain bare (dotted) key, such as `[[resources.sources]]`: harmless. */
const BARE_TABLES = /^\s*\[\[\s*[A-Za-z0-9_-]+(?:\s*\.\s*[A-Za-z0-9_-]+)*\s*\]\]\s*(?:#.*)?$/;

/** Whether a line is a `[[resources]]` header as this module recognizes one (the plain form). */
export function isResourcesHeader(line: string): boolean {
  return HEADER.test(line);
}

/**
 * The (1-based) lines of the `[[resources]]` headers, skipping text inside multiline strings;
 * null when any other line outside a string starts with `[[` and isn't a plain bare-key header.
 * Such a line could be `resources` spelled another way (`[["resources"]]`, an escape) or an
 * array value (`[["resources"]]` inside a multiline array), so no line can be trusted.
 */
function headerLines(toml: string): number[] | null {
  const out: number[] = [];
  let string: Quote | null = null;
  let suspicious = false;
  toml.split(/\r?\n/).forEach((line, i) => {
    let from = 0;
    if (string) {
      const end = closeMultiline(line, 0, string);
      if (end < 0) return;
      string = null;
      from = end;
    } else if (HEADER.test(line)) {
      out.push(i + 1);
      return;
    } else if (/^\s*\[\[/.test(line) && !BARE_TABLES.test(line)) {
      suspicious = true;
    }
    string = openAtEnd(line, from);
  });
  return suspicious ? null : out;
}

/**
 * Header lines paired, in order, with the parsed resources' paths (the first block for a file
 * wins); nothing at all when the counts disagree, since then no pairing can be trusted.
 */
export function pairHeaders(lines: number[], paths: (string | undefined)[]): Map<string, number> {
  const out = new Map<string, number>();
  if (lines.length !== paths.length) return out;
  paths.forEach((p, i) => {
    if (p !== undefined && !out.has(p)) out.set(p, lines[i]!);
  });
  return out;
}

/**
 * The line of each `[[resources]]` block in the metadata TOML, by the file it describes: a TOML
 * parser reads the resources and their `path`s, and the n-th header line is the n-th resource.
 * Comments name nothing. A file that doesn't parse, or whose headers can't be matched to its
 * resources, gives no lines (edit links then go to the file itself).
 */
export function resourceLines(toml: string): Map<string, number> {
  let resources: unknown;
  try {
    resources = parse(toml).resources;
  } catch {
    return new Map();
  }
  if (!Array.isArray(resources)) return new Map();
  const paths = resources.map((r: unknown) => {
    const p = r && typeof r === "object" ? (r as { path?: unknown }).path : undefined;
    return typeof p === "string" ? p : undefined;
  });
  const headers = headerLines(toml);
  return headers ? pairHeaders(headers, paths) : new Map();
}

/** A link to a dataset's entry in the metadata file (its line when known, else the file). */
export function entryUrl(fileUrl: string, lines: ReadonlyMap<string, number>, file: string): string {
  const n = lines.get(file);
  return n ? `${fileUrl}#L${n}` : fileUrl;
}
