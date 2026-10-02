// The metadata checklist (lib/completeness.ts): each item on fixtures, the license families,
// datasets without a schema, the order and totals of the status page, where each dataset's
// entry is in the metadata TOML, and the repository edit links go to. The live catalog is
// checked only loosely: the metadata will be filled in, and that must not break a test.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, test } from 'vitest';
import type { Dataset } from '../src/lib/catalog';
import { ADDITIONS_FILE, byGaps, completeness, documented, entryUrl, hasDescription, isResourcesHeader, pairHeaders, resourceLines, sourcesUnlinked, summarize } from '../src/lib/completeness';
import { DEFAULT_SITE_REPO, siteRepo } from '../src/lib/seo';
import { anchorProblems } from './anchors';
import { loadCatalog, REPO } from './catalog';
import { described, strip } from './fixtures';

/** The fixture, complete: a title, description, source, known license and every field described. */
function full(): Dataset {
  const d = described();
  return { ...d, sources: [{ title: 'Made up', path: 'https://example.org/' }], fields: d.fields.map((f) => ({ ...f, description: f.description ?? `About ${f.name}.` })) };
}

describe('the checklist', () => {
  test('a fully described dataset has no gaps', () => {
    const s = completeness(full());
    expect(s.has).toEqual({ title: true, description: true, source: true, license: true });
    expect(s.fields).toEqual({ total: 8, undescribed: [] });
    expect(s.gaps).toBe(0);
  });

  test('each dataset-level item is one gap', () => {
    expect(completeness({ ...full(), title: undefined }).has.title).toBe(false);
    expect(completeness({ ...full(), title: '  ' }).gaps).toBe(1);
    expect(completeness({ ...full(), description: '' }).has.description).toBe(false);
    expect(completeness({ ...full(), description: '\n ' }).gaps).toBe(1);
    expect(completeness({ ...full(), sources: [] }).has.source).toBe(false);
    expect(completeness({ ...full(), sources: [] }).gaps).toBe(1);
    const none = { ...full(), title: undefined, description: '', sources: [], licenses: [] };
    expect(completeness(none).gaps).toBe(4);
  });

  test('a source without a link still counts, and is noted', () => {
    const d = { ...full(), sources: [{ title: 'Generated Data' }] };
    expect(completeness(d).has.source).toBe(true);
    expect(sourcesUnlinked(d)).toBe(true);
    expect(sourcesUnlinked(full())).toBe(false);
    expect(sourcesUnlinked({ ...full(), sources: [] })).toBe(false);
  });

  test.each([
    [[], false],
    [[{ name: 'notspecified' }], false],
    [[{ name: 'notspecified' }, { name: 'notspecified', title: 'Unknown' }], false],
    [[{ name: 'notspecified' }, { name: 'CC-BY-4.0' }], true],
    [[{ name: 'CC0-1.0' }], true],
    [[{ name: 'other-pd' }], true],
    [[{ name: 'BSD-3-Clause' }], true],
    [[{ name: 'ODbL-1.0' }], true],
    [[{ name: 'some-other-license' }], true],
  ])('license %j known: %s', (licenses, known) => {
    const s = completeness({ ...full(), licenses });
    expect(s.has.license).toBe(known);
    expect(s.gaps).toBe(known ? 0 : 1);
  });

  test('each field without a description is a gap; whitespace is no description', () => {
    const d = described();
    const s = completeness(d);
    expect(s.fields).toEqual({ total: 8, undescribed: ['id', 'mpg', 'grade', 'side', 'origin', 'when'] });
    // The fixture's source has no link but counts; only the fields are gaps.
    expect(s.gaps).toBe(6);
    const blank = { ...full(), fields: full().fields.map((f, i) => (i === 0 ? { ...f, description: '   ' } : f)) };
    expect(hasDescription(blank.fields[0]!)).toBe(false);
    expect(completeness(blank).fields!.undescribed).toEqual(['id']);
  });

  test('datasets without a schema (maps, images, JSON trees) have no field items', () => {
    const map: Dataset = { ...full(), kind: 'json', format: 'topojson', fields: [], rows: null };
    const image: Dataset = { ...full(), kind: 'file', format: 'png', fields: [], rows: null };
    for (const d of [map, image]) {
      const s = completeness(d);
      expect(s.fields).toBeNull();
      expect(s.gaps).toBe(0);
    }
    expect(completeness({ ...image, title: undefined, licenses: [{ name: 'notspecified' }] }).gaps).toBe(2);
  });

  test('a table without a declared schema (fields read from the data) has no field items', () => {
    const inferred: Dataset = { ...full(), fieldsInferred: true, fields: full().fields.map((f) => ({ ...f, description: null })) };
    expect(completeness(inferred).fields).toBeNull();
    expect(completeness(inferred).gaps).toBe(0);
    expect(summarize([inferred]).fields).toEqual({ total: 0, described: 0 });
    expect(summarize([inferred]).tablesWithoutDescriptions).toBe(0);
  });

  test('properties that apply only where they fit are documented, never gaps', () => {
    expect(documented(described())).toEqual([
      'Field titles (5 fields)', 'Categories (2 fields)', 'Constraints (4 fields)', 'Missing values', 'Primary key', 'Foreign keys (2)',
    ]);
    const bare = strip(full());
    expect(documented(bare)).toEqual([]);
    expect(completeness(bare).gaps).toBe(1); // the title only: strip() removes it.
    // A field's own markers, without the schema's.
    const own = { ...bare, fields: bare.fields.map((f, i) => (i === 0 ? { ...f, missingValues: ['-'] } : f)) };
    expect(documented(own)).toEqual(['Missing values (1 field)']);
  });
});

describe('the status page', () => {
  const ds = (name: string, gaps: number): Dataset => ({ ...full(), name, fields: full().fields.map((f, i) => (i < gaps ? { ...f, description: null } : f)) });

  test('most gaps first, ties by name', () => {
    const rows = [ds('b', 1), ds('c', 3), ds('a', 1), ds('d', 0)].map((dataset) => ({ dataset, status: completeness(dataset) }));
    expect(byGaps(rows).map((r) => r.dataset.name)).toEqual(['c', 'a', 'b', 'd']);
  });

  test('totals', () => {
    const image: Dataset = { ...full(), name: 'img', kind: 'file', fields: [], licenses: [] };
    expect(summarize([ds('a', 0), ds('b', 8), image])).toEqual({
      datasets: 3,
      complete: 1,
      missing: { title: 0, description: 0, source: 0, license: 1 },
      fields: { total: 16, described: 8 },
      tablesWithoutDescriptions: 1,
    });
  });
});

describe("a dataset's entry in the metadata TOML", () => {
  const TOML = [
    '[package]', // 1
    'name = "x"',
    '',
    '[[resources]] # Path: a.csv', // 4
    'path = "a.csv"',
    '',
    '[[resources.sources]]',
    'path = "https://example.org/a"',
    '',
    '[[resources]]', // 10: no comment, named by its path
    "path = 'b.json'",
    '',
    '[[resources]]', // 13: no path of its own (its sub-table's doesn't name it)
    '[[resources.licenses]]',
    'path = "https://example.org/license"',
    '',
    '  [[ resources ]]   #   Path: c.png', // 17: spaces are allowed
    'path = "c.png"',
    '[[ contributors ]]', // another array of tables, a plain bare key: harmless
    'title = "x"',
    '[[resources]] # Path: a.csv', // 21: a duplicate keeps the first
    'path = "a.csv"',
  ].join('\r\n');

  test("lines by file: each real header paired, in order, with the parser's resources", () => {
    expect([...resourceLines(TOML)]).toEqual([['a.csv', 4], ['b.json', 10], ['c.png', 17]]);
  });

  test('only the plain header form counts; any other spelling that could name resources means no anchors', () => {
    expect(isResourcesHeader('[[resources]]')).toBe(true);
    expect(isResourcesHeader('  [[ resources ]]   # Path: a.csv')).toBe(true);
    expect(isResourcesHeader('[[resources.sources]]')).toBe(false);
    expect(isResourcesHeader('[["resources"]]')).toBe(false);
    // A quoted nested-array value and an escaped header, counts still equal (2 and 2).
    const nestedHeaders = ['[[resources]]', 'path = "a.csv"', 'tags = [', '[["resources"]]', ']', '[["\\u0072esources"]]', 'path = "b.csv"'].join('\n');
    expect(resourceLines(nestedHeaders)).toEqual(new Map());
    const plain = (header: string) => ['[[resources]]', 'path = "a.csv"', header, 'path = "b.csv"'].join('\n');
    expect(resourceLines(plain('[[resources]]'))).toEqual(new Map([['a.csv', 1], ['b.csv', 3]]));
    for (const header of ['[["resources"]]', "[[ 'resources' ]]", '[["\\u0072esources"]]', '[["resources".x]]', '[[resources . "x"]]']) {
      expect(resourceLines(plain(header)), header).toEqual(new Map());
    }
    // A plain bare-key array of tables (a sub-table, another list) doesn't disturb the anchors.
    expect(resourceLines(plain('[[resources.sources]]\ntitle = "s"\n[[resources]]'))).toEqual(new Map([['a.csv', 1], ['b.csv', 5]]));
  });

  test('paths in any TOML string form', () => {
    const toml = ['[[resources]] # Path: x.csv', 'path = """a.csv"""', "[[resources]]", "path = '''b.csv'''", '[[resources]] # Path: b.csv', 'path = "c\\u002ecsv"'].join('\n');
    expect(Object.fromEntries(resourceLines(toml))).toEqual({ 'a.csv': 1, 'b.csv': 3, 'c.csv': 5 });
  });

  test('array continuation lines that start with "[" are values', () => {
    const toml = [
      '[[resources]]',
      'schema = { fields = [{ name = "v", type = "array", constraints = { enum = [ [1, 2], [3] ] } }] }',
      'tags = [',
      '  [1, 2],',
      '  ["resources"],',
      ']',
      'path = "a.csv"',
      '[[resources]]',
      'path = "b.csv"',
    ].join('\n');
    expect(Object.fromEntries(resourceLines(toml))).toEqual({ 'a.csv': 1, 'b.csv': 8 });
  });

  test('when the headers and the parsed resources disagree, or the file does not parse, no anchors', () => {
    expect(pairHeaders([1, 5], ['a.csv', 'b.csv'])).toEqual(new Map([['a.csv', 1], ['b.csv', 5]]));
    expect(pairHeaders([1], ['a.csv', 'b.csv'])).toEqual(new Map());
    expect(pairHeaders([1, 5, 9], ['a.csv', 'b.csv'])).toEqual(new Map());
    // A resource without a path gets no anchor, and the others keep theirs.
    expect(pairHeaders([1, 5], [undefined, 'b.csv'])).toEqual(new Map([['b.csv', 5]]));
    expect(resourceLines('[[resources]]\npath = "a.csv"\n[[resources]\n')).toEqual(new Map());
  });

  test('header-like text inside strings is not a header', () => {
    const toml = [
      '[[resources]] # Path: a.csv', // 1
      'path = "a.csv"',
      'description = """',
      '[[resources]] # Path: b.csv', // inside a basic multiline string
      'path = "b.csv"',
      '"""',
      '[[resources]] # Path: b.csv', // 7: the real one
      'path = "b.csv"',
      "description = '''",
      '[[resources]] # Path: c.csv', // inside a literal multiline string
      "'''",
      'note = """an escaped quote \\""" leaves it open',
      '[[resources]] # Path: d.csv', // still inside
      'and it closes with an extra quote """"',
      'y = "one line \\"\\"\\" with quotes" # a comment with """',
      "z = 'literal with \"\"\"'",
      '[[resources]] # Path: c.csv', // 17
      'path = "c.csv"',
      '[[resources]] # Path: d.csv', // 19
      'path = "d.csv"',
    ].join('\n');
    expect(Object.fromEntries(resourceLines(toml))).toEqual({ 'a.csv': 1, 'b.csv': 7, 'c.csv': 17, 'd.csv': 19 });
  });

  test('comments name nothing: only the parsed path does', () => {
    const toml = ['[[resources]] # Path: old.csv', 'path = "new.csv"', '[[resources]] # Path: old.csv', 'path = "old.csv"'].join('\n');
    expect(Object.fromEntries(resourceLines(toml))).toEqual({ 'new.csv': 1, 'old.csv': 3 });
  });

  test('a link to the line, else to the file', () => {
    const lines = resourceLines(TOML);
    const file = 'https://github.com/o/r/blob/main/_data/datapackage_additions.toml';
    expect(entryUrl(file, lines, 'b.json')).toBe(`${file}#L10`);
    expect(entryUrl(file, lines, 'missing.csv')).toBe(file);
  });

  test("the build test's anchor check never parses a suffix", () => {
    const real = readFileSync(path.join(REPO, ADDITIONS_FILE), 'utf8');
    // Valid as a whole, though its suffix from the first resource isn't: the later
    // [[contributors]] would then redefine [contributors.details].
    const text = [real, '[contributors.details]', 'note = "Maintainer"', '[[contributors]]', 'title = "Another contributor"', ''].join('\n');
    const anchors = resourceLines(text);
    expect(anchors).toEqual(resourceLines(real));
    expect(anchorProblems(text, anchors)).toEqual([]);
    // And it catches wrong anchors: off the header, out of order, missing.
    const [first, second] = [...anchors.keys()];
    expect(anchorProblems(text, new Map([...anchors, [first!, anchors.get(first!)! + 1]]))).not.toEqual([]);
    expect(anchorProblems(text, new Map([...anchors, [first!, anchors.get(second!)!], [second!, anchors.get(first!)!]]))).not.toEqual([]);
    const missing = new Map(anchors);
    missing.delete(second!);
    expect(anchorProblems(text, missing)).toEqual([`resource 2 (${second}) has no anchor`]);
  });

  test('every dataset in the catalog has a line in the real file', () => {
    const lines = resourceLines(readFileSync(path.join(REPO, ADDITIONS_FILE), 'utf8'));
    const text = readFileSync(path.join(REPO, ADDITIONS_FILE), 'utf8').split(/\r?\n/);
    for (const d of loadCatalog().datasets) {
      const n = lines.get(d.file);
      expect(n, d.file).toBeDefined();
      // As the module recognizes headers (`[[ resources ]]` is fine too).
      expect(isResourcesHeader(text[n! - 1]!), d.file).toBe(true);
    }
  });
});

describe('the repository edit links go to', () => {
  test(`defaults to ${DEFAULT_SITE_REPO}`, () => {
    expect(siteRepo({})).toBe('https://github.com/vega/vega-datasets');
    expect(siteRepo({ SITE_REPO: '' })).toBe('https://github.com/vega/vega-datasets');
    expect(siteRepo({ SITE_REPO: 'not a repo' })).toBe('https://github.com/vega/vega-datasets');
    expect(siteRepo({ SITE_REPO: 'https://evil.example/x' })).toBe('https://github.com/vega/vega-datasets');
  });

  test('site.yml sets SITE_REPO for the whole job, so the tests and link check see what the build used', () => {
    const yml = readFileSync(path.join(REPO, '.github', 'workflows', 'site.yml'), 'utf8').split(/\r?\n/);
    // The build job's own env (four spaces in), not a step's (ten).
    const job = yml.indexOf('  build:');
    const env = yml.indexOf('    env:', job);
    const steps = yml.indexOf('    steps:', job);
    expect(job).toBeGreaterThan(-1);
    expect(env).toBeGreaterThan(job);
    expect(env).toBeLessThan(steps);
    expect(yml.slice(env, steps)).toContain('      SITE_REPO: ${{ github.repository }}');
    expect(yml.filter((l) => l.includes('SITE_REPO:'))).toHaveLength(1);
  });

  test('SITE_REPO names the repository that built the site', () => {
    expect(siteRepo({ SITE_REPO: 'dsmedia/vega-datasets' })).toBe('https://github.com/dsmedia/vega-datasets');
    expect(siteRepo({ SITE_REPO: ' vega/vega-datasets\n' })).toBe('https://github.com/vega/vega-datasets');
  });
});

/** Invariants that hold however much metadata is filled in (and whichever tables have a schema). */
function totalsAddUp(datasets: Dataset[]) {
  const s = summarize(datasets);
  expect(s.datasets).toBe(datasets.length);
  const gaps = datasets.map((d) => completeness(d).gaps);
  expect(gaps.every((g) => Number.isInteger(g) && g >= 0)).toBe(true);
  expect(s.complete).toBe(gaps.filter((g) => g === 0).length);
  // Declared fields only: a table whose columns were read from the data has no field items.
  const declared = datasets.filter((d) => !d.fieldsInferred);
  expect(s.fields.total).toBe(declared.reduce((n, d) => n + d.fields.length, 0));
  expect(s.fields.described).toBe(declared.reduce((n, d) => n + d.fields.filter(hasDescription).length, 0));
}

test('the live catalog: every dataset is judged, and the totals add up', () => {
  const c = loadCatalog();
  totalsAddUp(c.datasets);
  // As they would if a table lost its schema.
  totalsAddUp(c.datasets.map((d) => (d.name === 'cars' ? { ...d, fieldsInferred: true as const } : d)));
});
