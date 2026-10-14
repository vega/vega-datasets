// What search engines read: titles, meta descriptions, and schema.org JSON-LD. Every
// dataset page carries a Dataset with Google's required fields (name, and a description
// of 50 to 5,000 characters); datasets whose descriptions are too short are listed in
// SHORT, so a new one fails here until its description is written.
import { describe, expect, test } from 'vitest';
import { breadcrumbJsonLd, catalogJsonLd, clip, datasetJsonLd, datasetTitle, licenseUrls, metaDescription, plainText, temporalCoverage } from '../src/lib/seo';
import { loadCatalog } from './catalog';

const catalog = loadCatalog();
const ds = (name: string) => catalog.dataset(name)!;

/** Datasets whose descriptions are under Google's 50-character minimum (as of this change). */
const SHORT = ['platformer_terrain', 'sp500_2000', 'windvectors'];

describe('titles and descriptions', () => {
  test('titles say what the file is', () => {
    expect(datasetTitle(ds('cars'))).toBe('cars — JSON, 406 rows, 9 fields · Vega Datasets');
    expect(datasetTitle(ds('us_10m'))).toBe('us_10m — TopoJSON map · Vega Datasets');
    expect(datasetTitle(ds('gimp'))).toBe('gimp — PNG image · Vega Datasets');
  });

  test('meta descriptions are plain text, at most 160 characters, cut at a word', () => {
    for (const d of catalog.datasets) {
      const m = metaDescription(d.description);
      expect(m.length, d.name).toBeLessThanOrEqual(160);
      expect(m, d.name).not.toMatch(/`|\*\*|\]\(/);
    }
    expect(clip('one two three four five six', 16)).toBe('one two three…');
    expect(plainText('A [TopoJSON](https://x) map with `code` and **bold**.')).toBe('A TopoJSON map with code and bold.');
  });
});

describe('Dataset JSON-LD', () => {
  test.each(catalog.datasets.map((d) => [d.name, d] as const))('%s', (name, d) => {
    const ld = datasetJsonLd(catalog, d);
    expect(ld['@type']).toBe('Dataset');
    expect(ld.name).toBe(name);
    expect(ld.url).toBe(`https://vega.github.io/vega-datasets/datasets/${name}/`);
    const description = ld.description as string;
    if (SHORT.includes(name)) expect(description.length).toBeLessThan(50);
    else expect(description.length).toBeGreaterThanOrEqual(50);
    expect(description.length).toBeLessThanOrEqual(5000);
    const dist = (ld.distribution as { contentUrl: string; encodingFormat: string }[])[0]!;
    expect(dist.contentUrl).toBe(d.url);
    expect(dist.encodingFormat).toMatch(/^[a-z]+\/[\w.+-]+$/);
    // Round-trips as JSON, with nothing undefined left behind.
    expect(JSON.parse(JSON.stringify(ld))).toEqual(ld);
  });

  test('licenses become URLs; temporal and variable detail where the data has it', () => {
    expect(licenseUrls(ds('penguins'))).toEqual([ds('penguins').licenses[0]!.path]);
    expect(licenseUrls(ds('barley'))).toEqual([]);
    expect(temporalCoverage(ds('seattle_weather'))).toBe('2012-01-01/2015-12-31');
    expect(temporalCoverage(ds('gapminder'))).toBe('1955/2005');
    const vars = datasetJsonLd(catalog, ds('cars')).variableMeasured as { name: string; minValue?: number }[];
    expect(vars.find((v) => v.name === 'Horsepower')).toMatchObject({ minValue: 46, maxValue: 230 });
  });

  test('breadcrumbs and the catalog', () => {
    expect((breadcrumbJsonLd(ds('cars')).itemListElement as unknown[]).length).toBe(2);
    const [site, cat] = catalogJsonLd(catalog);
    expect(site!['@type']).toBe('WebSite');
    expect((cat!.dataset as unknown[]).length).toBe(catalog.datasets.length);
  });
});
