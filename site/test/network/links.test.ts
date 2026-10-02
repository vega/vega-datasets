// Every outbound link the site generates must resolve: gallery pages, example
// sources, Vega Editor example routes, each dataset's file URL (which the starter
// charts load), and the links written into the layout, pages and scripts.
// Needs the network; run with `npm run site:check-links`.
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { expect, test } from 'vitest';
import { siteRepo } from '../../src/lib/seo';
import { starterSpec } from '../../src/lib/starter';
import { REPO, loadCatalog } from '../catalog';

/**
 * Files not yet on npm link to GitHub Pages, which this same build deploys; checking
 * the live site would fail until the deploy it is blocking. Check the checkout instead.
 */
const PAGES_DATA = 'https://vega.github.io/vega-datasets/data/';

/** Six tries back off 1 + 2 + 4 + 8 + 16 s: a host that is down for half a minute (it happens to
 *  idl.cs.washington.edu) doesn't fail a pull request. A try that hangs is cut off at 30 s. */
const ATTEMPTS = 6;
const TRY_TIMEOUT_MS = 30_000;
const CONCURRENCY = 12;

/**
 * Fixed links in site/src (layout, pages, components, scripts): literal https URLs, and `${REPO}…` templates
 * with the repository URL filled in (`${EDIT_REPO}…` with the one SITE_REPO names, as the
 * build does). Links built from other values (a dataset's file, an encoded spec) are covered by the catalog loop instead. Fragments are dropped:
 * a HEAD request can't see them (home.test.ts checks the README anchors).
 */
function writtenLinks(): string[] {
  const repo = 'https://github.com/vega/vega-datasets';
  const files = (dir: string): string[] => readdirSync(dir).flatMap((f) => {
    const p = path.join(dir, f);
    return statSync(p).isDirectory() ? files(p) : [p];
  });
  const texts = files(path.join(REPO, 'site', 'src')).map((f) => readFileSync(f, 'utf8'));
  const urls = texts.flatMap((t) => [
    ...[...t.matchAll(/https:\/\/[^\s"'`)<>]+/g)].map((m) => m[0]),
    ...[...t.matchAll(/`\$\{REPO\}([^`]*)`/g)].map((m) => repo + m[1]),
    // Edit links go to the repository this build names (SITE_REPO; a fork's CI sets its own).
    ...[...t.matchAll(/`\$\{EDIT_REPO\}([^`]*)`/g)].map((m) => siteRepo(process.env) + m[1]),
  ]);
  return [...new Set(urls
    .map((u) => u.split('#')[0]!)
    .filter((u) => !u.includes('${') && !u.startsWith('https://vega.github.io/schema/')))];
}

/** Final HTTP status after redirects, retrying transient failures (jsDelivr can 403 under bursts). */
async function status(url: string): Promise<number> {
  if (url.startsWith(PAGES_DATA)) {
    return existsSync(path.join(REPO, 'data', url.slice(PAGES_DATA.length))) ? 200 : 404;
  }
  let last = 0;
  for (let attempt = 0; attempt < ATTEMPTS; attempt++) {
    try {
      last = (await fetch(url, { method: 'HEAD', redirect: 'follow', signal: AbortSignal.timeout(TRY_TIMEOUT_MS) })).status;
      if (last === 200 || last === 404) return last;
    } catch {
      last = -1;
    }
    if (attempt < ATTEMPTS - 1) await new Promise((r) => setTimeout(r, 1000 * 2 ** attempt));
  }
  return last;
}

test('every link target resolves', async () => {
  const catalog = loadCatalog();
  const links = new Map<string, string>();
  for (const e of catalog.examples) {
    links.set(e.url, `gallery page of ${e.id}`);
    links.set(e.source, `source of ${e.id}`);
    if (e.editor) {
      // The Editor is a single-page app; its example routes load these spec files.
      const [gallery, slug] = e.editor.split('#/examples/')[1]!.split('/');
      const ext = gallery === 'vega' ? 'vg' : 'vl';
      links.set(`https://vega.github.io/editor/spec/${gallery}/${slug}.${ext}.json`, `Editor route of ${e.id}`);
    }
  }
  for (const d of catalog.datasets) {
    links.set(d.url, `file of ${d.name}`);
    const data = (starterSpec(d) as { data?: { url?: string } } | null)?.data?.url;
    if (data) links.set(data, `starter data of ${d.name}`);
  }

  const written = writtenLinks();
  // The edit links' repository as this build configures it (a fork's own, in its CI).
  expect(written).toContain(`${siteRepo(process.env)}/blob/main/_data/datapackage_additions.toml`);
  for (const url of written) links.set(url, 'link in the page code');

  const queue = [...links];
  const broken: string[] = [];
  await Promise.all(Array.from({ length: CONCURRENCY }, async () => {
    for (let next = queue.shift(); next; next = queue.shift()) {
      const [url, what] = next;
      const code = await status(url);
      if (code !== 200) broken.push(`${code} ${what}: ${url}`);
    }
  }));
  expect(broken.sort()).toEqual([]);
  expect(links.size).toBeGreaterThan(1000);
});
