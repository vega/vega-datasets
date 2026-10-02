/**
 * What search engines and link previews read: page titles, meta descriptions, and
 * schema.org JSON-LD (a DataCatalog on the home page, a Dataset per dataset page,
 * which is what Google Dataset Search indexes). Plain data, unit-tested.
 */
import type { Catalog, Dataset } from "./catalog";
import { isReleased } from "./dataset-model";
import { FORMAT_LABEL, formatBytes, plural } from "./format";
import { isYear } from "./starter";

export const SITE_NAME = "Vega Datasets";
/** The canonical home of the site; fork deployments point here too. */
export const HOME_URL = "https://vega.github.io/vega-datasets/";
export const REPO = "https://github.com/vega/vega-datasets";
export const HOME_TITLE = "Vega Datasets: Example Data for Vega, Vega-Lite and Altair";
export const HOME_DESCRIPTION =
  "Every dataset in vega-datasets: what each field holds, where the data comes from, its license, and the Vega, Vega-Lite and Altair gallery examples that use it.";

/**
 * Whether a build stays out of search results (`<meta name="robots" content="noindex">`):
 * `SITE_NOINDEX=1` (site.yml sets it outside vega/vega-datasets), or a GitHub build of any
 * other repository. Only vega.github.io/vega-datasets, which every page names as canonical,
 * is indexed.
 */
export function noindex(env: Record<string, string | undefined>): boolean {
  const repo = env.GITHUB_REPOSITORY;
  return env.SITE_NOINDEX === "1" || (repo !== undefined && repo !== "vega/vega-datasets");
}

/** The repository a build links its edit links to when `SITE_REPO` doesn't name one. */
export const DEFAULT_SITE_REPO = "vega/vega-datasets";

/**
 * The repository that built the site, for its edit links ("Add", "Edit this dataset's
 * metadata"): `SITE_REPO` (`owner/name`; site.yml sets it from `github.repository`), else
 * vega/vega-datasets. Project links ("View on GitHub", Contributing) stay on {@link REPO}.
 */
export function siteRepo(env: Record<string, string | undefined>): string {
  const repo = env.SITE_REPO?.trim();
  return `https://github.com/${repo && /^[\w.-]+\/[\w.-]+$/.test(repo) ? repo : DEFAULT_SITE_REPO}`;
}

/** The metadata coverage page: its path relative to the home page, and its title. */
export const STATUS_PATH = "metadata/";
export const STATUS_TITLE = "Metadata Coverage";

/** A dataset's row on the status page: namespaced, so no dataset name can collide with the layout's ids (main#page). */
export function statusRowId(name: string): string {
  return `ds-${name}`;
}

export function statusUrl(): string {
  return HOME_URL + STATUS_PATH;
}

/** A dataset page's path, relative to the home page. */
export function datasetPath(name: string): string {
  return `datasets/${encodeURIComponent(name)}/`;
}

export function datasetUrl(name: string): string {
  return HOME_URL + datasetPath(name);
}

/** Markdown as plain text: links keep their text, emphasis and code marks go, whitespace collapses. */
export function plainText(markdown: string): string {
  return markdown
    .replace(/!?\[([^\]]*)\]\([^)]*\)+/g, "$1")
    .replace(/[*_`]/g, "")
    .replace(/^\s*>\s?/gm, "")
    .replace(/^\s*#+\s+/gm, "")
    .replace(/\s+/g, " ")
    .trim();
}

/** Cut at a word boundary to at most `max` characters, marking the cut with "…". */
export function clip(text: string, max: number): string {
  if (text.length <= max) return text;
  const cut = text.slice(0, max - 1);
  const space = cut.lastIndexOf(" ");
  return `${(space > max * 0.6 ? cut.slice(0, space) : cut).replace(/[\s,;:.–-]+$/, "")}…`;
}

/** "cars — JSON, 406 rows, 9 fields · Vega Datasets"; maps and images say what they are. */
export function datasetTitle(d: Dataset): string {
  const format = FORMAT_LABEL[d.format] ?? d.format.toUpperCase();
  let what: string;
  if (d.format === "topojson" || d.format === "geojson") what = `${format} map`;
  else if (d.kind === "file") what = `${format} image`;
  else if (d.rows !== null) what = [format, plural(d.rows, "row"), d.fields.length ? plural(d.fields.length, "field") : null].filter(Boolean).join(", ");
  else what = format;
  return `${d.name} — ${what} · ${SITE_NAME}`;
}

/** The meta description: the description's first paragraph as plain text, at most 160 characters. */
export function metaDescription(markdown: string, max = 160): string {
  const first = markdown.trim().split(/\n\s*\n/)[0] ?? "";
  return clip(plainText(first), max);
}

/**
 * A dataset page's meta description: its title (when the metadata has one) followed by
 * the description's first paragraph, else that paragraph alone, at most 160 characters.
 */
export function datasetMetaDescription(d: Dataset): string {
  const description = d.description || `${d.name} from vega-datasets.`;
  if (!d.title) return metaDescription(description);
  // A title is plain text: only the description is Markdown.
  const title = d.title.trim();
  return clip(`${title}${/[.!?]$/.test(title) ? "" : "."} ${metaDescription(description, Infinity)}`, 160);
}

const MIME: Record<string, string> = {
  csv: "text/csv",
  tsv: "text/tab-separated-values",
  json: "application/json",
  topojson: "application/json",
  geojson: "application/geo+json",
  parquet: "application/vnd.apache.parquet",
  arrow: "application/vnd.apache.arrow.file",
  png: "image/png",
};

/** Data Package license names that are SPDX identifiers, so they have a canonical URL. */
const SPDX = new Set([
  "BSD-3-Clause", "CC-BY-4.0", "CC-BY-SA-4.0", "CC0-1.0", "ISC", "LGPL-2.1", "MIT", "ODbL-1.0", "ODC-By-1.0", "OGL-UK-3.0", "PDDL-1.0",
]);

/** License URLs for a dataset: the recorded path, else the SPDX page for a known identifier. */
export function licenseUrls(d: Dataset): string[] {
  const urls = d.licenses.flatMap((l) => {
    if (l.path && /^https?:/.test(l.path)) return [l.path];
    if (SPDX.has(l.name)) return [`https://spdx.org/licenses/${l.name}.html`];
    return [];
  });
  return [...new Set(urls)];
}

/** The time span the data covers, as an ISO 8601 interval, from the first date or year field. */
export function temporalCoverage(d: Dataset): string | null {
  for (const f of d.fields) {
    const p = f.profile;
    if (p.kind === "temporal") return `${p.min.slice(0, 10)}/${p.max.slice(0, 10)}`;
  }
  for (const f of d.fields) {
    const p = f.profile;
    if (p.kind === "quantitative" && isYear(f)) return `${p.min}/${p.max}`;
  }
  return null;
}

const one = <T>(xs: T[]): T | T[] | undefined => (xs.length === 0 ? undefined : xs.length === 1 ? xs[0] : xs);

/** schema.org Dataset for a dataset page. Google Dataset Search requires name and description. */
export function datasetJsonLd(c: Catalog, d: Dataset): Record<string, unknown> {
  const url = datasetUrl(d.name);
  const keywords = [...new Set(c.examplesFor(d).flatMap((e) => e.categories))].sort();
  const sources = d.sources.map((s) => ({ "@type": "Organization", name: s.title, ...(s.path ? { url: s.path } : {}) }));
  const coverage = temporalCoverage(d);
  const ld: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "@id": `${url}#dataset`,
    name: d.name,
    description: clip(plainText(d.description || `${d.name} from vega-datasets.`), 5000),
    url,
    identifier: d.name,
    license: one(licenseUrls(d)),
    isAccessibleForFree: true,
    creator: one(sources),
    isBasedOn: one(d.sources.flatMap((s) => (s.path ? [s.path] : []))),
    publisher: { "@type": "Organization", name: "Vega", url: "https://vega.github.io/" },
    includedInDataCatalog: { "@type": "DataCatalog", name: SITE_NAME, url: HOME_URL },
    distribution: [{
      "@type": "DataDownload",
      encodingFormat: MIME[d.format] ?? "application/octet-stream",
      contentUrl: d.url,
      ...(d.bytes !== null ? { contentSize: formatBytes(d.bytes) } : {}),
    }],
    variableMeasured: one(d.fields.map((f) => ({
      "@type": "PropertyValue",
      name: f.name,
      ...(f.description ? { description: f.description } : {}),
      ...(f.profile.kind === "quantitative" ? { minValue: f.profile.min, maxValue: f.profile.max } : {}),
    }))),
    temporalCoverage: coverage ?? undefined,
    keywords: keywords.length ? keywords : undefined,
    version: isReleased(d) ? c.package.version : undefined,
  };
  return Object.fromEntries(Object.entries(ld).filter(([, v]) => v !== undefined));
}

export function breadcrumbJsonLd(d: Dataset): Record<string, unknown> {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Datasets", item: HOME_URL },
      { "@type": "ListItem", position: 2, name: d.name, item: datasetUrl(d.name) },
    ],
  };
}

/** The home page: the site, and the catalog of every dataset. */
export function catalogJsonLd(c: Catalog): Record<string, unknown>[] {
  return [
    { "@context": "https://schema.org", "@type": "WebSite", name: SITE_NAME, url: HOME_URL },
    {
      "@context": "https://schema.org",
      "@type": "DataCatalog",
      name: SITE_NAME,
      url: HOME_URL,
      description: HOME_DESCRIPTION,
      publisher: { "@type": "Organization", name: "Vega", url: "https://vega.github.io/" },
      license: "https://spdx.org/licenses/BSD-3-Clause.html",
      // Each dataset's page carries its full Dataset description; the catalog names and links them.
      dataset: c.datasets.map((d) => ({ "@type": "Dataset", "@id": `${datasetUrl(d.name)}#dataset`, name: d.name, url: datasetUrl(d.name) })),
    },
  ];
}

/** JSON for a `<script type="application/ld+json">` (or other data block): `<` is escaped so the text can't close the element. */
export function jsonForScript(value: unknown): string {
  return JSON.stringify(value).replace(/</g, "\\u003c");
}
