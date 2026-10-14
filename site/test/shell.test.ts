// The page shell (site/src/layouts/Base.astro) and stylesheet: light by default like
// the other Vega sites, no web fonts, and every color, font and size drawn from the
// theme tokens. (The built pages are checked in build.test.ts.)
import { readdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { expect, test } from 'vitest';
import { noindex } from '../src/lib/seo';

const site = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (rel: string) => readFileSync(path.join(site, rel), 'utf8');
const layout = read('src/layouts/Base.astro');
const css = read('src/styles/site.css');

/** Every file under `dir`, recursively. */
function files(dir: string): string[] {
  return readdirSync(dir).flatMap((f) => {
    const p = path.join(dir, f);
    return statSync(p).isDirectory() ? files(p) : [p];
  });
}

test('the page uses a single light palette', () => {
  expect(ruleBody(':root')).toMatch(/color-scheme:\s*light;/);
  expect(layout).not.toContain('data-theme');
});

test('no web fonts: system stacks only, and the CSP blocks font loads', () => {
  expect(layout).toContain("font-src 'none'");
  expect(css).not.toMatch(/@font-face|@import/);
});

test('the CSP allows only same-origin scripts, and no eval', () => {
  expect(layout).toContain("script-src 'self';");
  expect(layout).not.toMatch(/unsafe-eval/);
});

test('search and link previews: canonical URL, Open Graph and Twitter card, theme color', () => {
  const meta = (attr: string, key: string) => layout.match(new RegExp(`<meta ${attr}="${key}" content=[{]?([^}>]+)[}]?>`))?.[1];
  expect(layout).toContain('<link rel="canonical" href={canonical}>');
  expect(meta('property', 'og:url')).toBe('canonical');
  expect(meta('property', 'og:type')).toBe('"website"');
  expect(meta('property', 'og:site_name')).toBe('SITE_NAME');
  // Link previews say what the page says.
  expect(meta('property', 'og:title')).toBe('title');
  expect(meta('property', 'og:description')).toBe('description');
  expect(meta('name', 'twitter:card')).toBe('"summary"');
  expect(meta('name', 'theme-color')).toBe(`"${css.match(/--header: (#[0-9a-f]{6})/)![1]}"`);
});

test("a fork's build (SITE_NOINDEX=1, or another repository) keeps out of search results; the canonical build doesn't", () => {
  expect(noindex({})).toBe(false);
  expect(noindex({ SITE_NOINDEX: '0', GITHUB_REPOSITORY: 'vega/vega-datasets' })).toBe(false);
  expect(noindex({ SITE_NOINDEX: '1' })).toBe(true);
  expect(noindex({ SITE_NOINDEX: '0', GITHUB_REPOSITORY: 'dsmedia/vega-datasets' })).toBe(true);
  expect(layout).toMatch(/\{noindex && <meta name="robots" content="noindex">\}/);
  expect(layout.indexOf('name="robots"')).toBeLessThan(layout.indexOf('</head>'));
});

test('the stylesheet parses: every block closes, none closes twice', () => {
  // A stray brace makes browsers drop the rule after it (a whole @media block, say).
  let depth = 0;
  const stray: number[] = [];
  // Blank out comments but keep their line breaks, so the reported line numbers are the file's.
  css.replace(/\/\*[\s\S]*?\*\//g, (c) => c.replace(/[^\n]/g, '')).split('\n').forEach((line, i) => {
    for (const ch of line) {
      if (ch === '{') depth++;
      if (ch === '}' && --depth < 0) {
        stray.push(i + 1);
        depth = 0;
      }
    }
  });
  expect(stray).toEqual([]);
  expect(depth).toBe(0);
});

/** Custom properties declared in a stretch of CSS. */
function declared(block: string): Set<string> {
  return new Set([...block.matchAll(/(--[\w-]+)\s*:/g)].map((m) => m[1]!));
}

/** The body of the first top-level rule with exactly this selector. */
function ruleBody(selector: string): string {
  const start = css.indexOf(`\n${selector} {`);
  expect(start, `${selector} rule`).toBeGreaterThan(-1);
  return css.slice(start, css.indexOf('\n}', start));
}

test('every token the stylesheet and scripts use is defined', () => {
  const defined = declared(css);
  const used = new Set([...css.matchAll(/var\((--[\w-]+)/g)].map((m) => m[1]!));
  for (const file of files(path.join(site, 'src'))) {
    const text = readFileSync(file, 'utf8');
    for (const m of text.matchAll(/[tT]oken\("(--[\w-]+)"\)/g)) used.add(m[1]!);
  }
  // Set on the dataset page's Explore chart box, not in the stylesheet.
  for (const name of ['--chart-h', '--chart-h-phone']) used.delete(name);
  expect(used.size).toBeGreaterThan(20);
  expect([...used].filter((name) => !defined.has(name))).toEqual([]);
});

test('forced colors: data colors kept; chart text and rules, built or live, take the mode\'s colors', () => {
  const block = css.slice(css.indexOf('@media (forced-colors: active)'));
  expect(block.length).toBeGreaterThan(0);
  const body = block.slice(0, block.indexOf('\n}\n'));
  expect(body).toMatch(/\.stack > span, \.gdot \{ forced-color-adjust: none; \}/);
  // The prerendered catalog chart sits in .catalog-chart, outside any .vega-embed.
  expect(body).toMatch(/:is\(\.catalog-chart, \.explore-chart\) svg text \{ fill: CanvasText !important; \}/);
  expect(body).not.toMatch(/\.vega-embed svg/);
});

test('forced colors override every color the stylesheet gives chart SVG (text, rules, brush)', () => {
  // [element, property] pairs from rules; `important` keeps only !important declarations.
  const pairs = (block: string, important: boolean) => {
    const out = new Set<string>();
    for (const [, selectors, decls] of block.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
      if (!/catalog-chart/.test(selectors!) || !/\bsvg\b/.test(selectors!)) continue;
      for (const [, prop, value] of decls!.matchAll(/(fill|stroke)\s*:\s*([^;]+);?/g)) {
        if (important && !/!important/.test(value!)) continue;
        for (const sel of selectors!.split(/,(?![^(]*\))/)) out.add(`${sel.trim().split(/\s+/).pop()} ${prop}`);
      }
    }
    return out;
  };
  const bare = css.replace(/\/\*[\s\S]*?\*\//g, '');
  const start = bare.indexOf('@media (forced-colors: active)');
  const forcedBlock = bare.slice(start, bare.indexOf('\n}\n', start));
  const outside = bare.replace(/@media[^{]+\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}/g, '');
  const themed = pairs(outside, false);
  const forced = pairs(forcedBlock, true);
  expect(themed.size).toBeGreaterThan(2);
  // A theming rule can be more specific than the forced one (.mark-text.role-mark text), so
  // the forced declarations are !important for each element and property the theme colors.
  expect([...themed].filter((p) => !forced.has(p))).toEqual([]);
});

test('snippets wrap long URLs at hyphens and spaces, not mid-word', () => {
  // word-break: break-all split "vega-datasets" as "vega-data / sets" in the rail.
  expect(css).not.toMatch(/word-break:\s*break-all/);
  expect(css).toMatch(/\.rail-use \.snippet \{[^}]*overflow-wrap: anywhere/);
});
