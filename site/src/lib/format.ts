const nf = new Intl.NumberFormat("en-US");

/** A file size in decimal units (1 KB = 1,000 bytes), as the catalog chart's axis labels it. */
export function formatBytes(bytes: number | null): string {
  if (bytes === null) return "–";
  if (bytes < 1000) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let v = bytes / 1000;
  let i = 0;
  // 999,600 bytes is "1.0 MB", not "1000 KB".
  while (v >= 999.5 && i < units.length - 1) {
    v /= 1000;
    i++;
  }
  return `${v < 9.95 ? v.toFixed(1) : Math.round(v)} ${units[i]}`;
}

export function formatCount(n: number | null): string {
  return n === null ? "–" : nf.format(n);
}


export function formatNumber(n: number): string {
  if (Number.isInteger(n)) return nf.format(n);
  const abs = Math.abs(n);
  const digits = abs >= 100 ? 1 : abs >= 1 ? 2 : 3;
  return n.toLocaleString("en-US", { maximumFractionDigits: digits });
}

/**
 * A catalog date. A date-time with no zone is the file's own wall-clock time, read as UTC
 * (JavaScript would read it as the viewer's local time, a day early east of UTC), so every
 * viewer sees the file's values.
 */
export function parseDate(iso: string): Date {
  return new Date(/T[\d:.]+$/.test(iso) ? `${iso}Z` : iso);
}

/** A catalog date as text, with the time when it isn't midnight (or when `time` says so). */
export function formatDate(iso: string, time?: boolean): string {
  const d = parseDate(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const hasTime = time ?? d.getUTCHours() + d.getUTCMinutes() + d.getUTCSeconds() > 0;
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    ...(hasTime ? { hour: "2-digit", minute: "2-digit" } : {}),
    timeZone: "UTC",
  });
}

export function plural(n: number, one: string, many = `${one}s`): string {
  return `${nf.format(n)} ${n === 1 ? one : many}`;
}


export const FORMAT_LABEL: Record<string, string> = {
  csv: "CSV",
  tsv: "TSV",
  json: "JSON",
  topojson: "TopoJSON",
  geojson: "GeoJSON",
  parquet: "Parquet",
  arrow: "Arrow",
  png: "PNG",
};

export const TYPE_LABEL: Record<string, string> = {
  integer: "integer",
  number: "number",
  string: "string",
  date: "date",
  datetime: "datetime",
  boolean: "boolean",
  array: "list",
};
