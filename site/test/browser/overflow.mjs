// No page scrolls sideways: home, the metadata coverage page and every dataset page on a phone
// (390px) and a desktop, and on the desktop the fields table stays inside its column (long
// unbroken summary values, URLs and list literals, used to push it out).
// Not part of `npm run site:test` (it needs Chrome and a built site).
//
// Usage, after `npm run site:build`:
//   node site/test/browser/overflow.mjs [--port 8124]
// Environment: PUPPETEER_CORE (a folder whose node_modules has puppeteer-core, if it isn't
// installed here) and CHROME_PATH (the Chrome executable). The script starts the preview
// server (site/scripts/serve.mjs) and stops it when it is done.
import { spawn } from 'node:child_process';
import { readdirSync } from 'node:fs';
import { launchBrowser } from './browser.mjs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

const { values: args } = parseArgs({ options: { port: { type: 'string', default: '8124' } } });
const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '..', '..', '..');
const base = `http://localhost:${args.port}/vega-datasets/`;

/** Start the preview server and resolve once it listens. */
function serve() {
  const child = spawn(process.execPath, [path.join(repo, 'site', 'scripts', 'serve.mjs'), '--port', args.port], { stdio: ['ignore', 'pipe', 'inherit'] });
  return new Promise((resolve, reject) => {
    child.stdout.on('data', (b) => { if (String(b).includes('Field Guide at')) resolve(child); });
    child.on('exit', (code) => reject(new Error(`The preview server exited (${code})`)));
  });
}

const PHONE = { width: 390, height: 844, deviceScaleFactor: 1, isMobile: true, hasTouch: true };
const DESKTOP = { width: 1360, height: 900, deviceScaleFactor: 1, isMobile: false, hasTouch: false };

const dist = path.join(repo, 'site', 'dist', 'datasets');
// Home, the metadata coverage page (its table scrolls inside its own region) and every dataset page.
const pages = ['', 'metadata/', ...readdirSync(dist).sort().map((n) => `datasets/${n}/`)];

/** How far the page scrolls sideways, and how far the fields table reaches past its column. */
function measure() {
  const table = document.querySelector('.dict');
  const parent = table?.parentElement;
  return {
    scroll: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    table: table && parent ? Math.round(table.getBoundingClientRect().right - parent.getBoundingClientRect().right) : 0,
  };
}

const server = await serve();
const browser = await launchBrowser();
const failures = [];
let checks = 0;
try {
  for (const [label, viewport] of [['phone', PHONE], ['desktop', DESKTOP]]) {
    const page = await browser.newPage();
    await page.setViewport(viewport);
    for (const p of pages) {
      await page.goto(base + p, { waitUntil: 'load' });
      const m = await page.evaluate(measure);
      checks++;
      if (m.scroll > 0 || m.table > 1) failures.push({ label, page: p || 'home', ...m });
    }
    await page.close();
  }
} finally {
  await browser.close();
  server.kill();
}
for (const f of failures) console.log(`FAIL  ${f.label} ${f.page}: page scrolls ${f.scroll}px, fields table ${f.table}px past its column`);
console.log(`\n${checks - failures.length} of ${checks} checks passed.`);
process.exitCode = failures.length ? 1 : 0;
