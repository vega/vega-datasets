// The home page's catalog chart brush is see-through. Vega-Lite draws an interval brush as
// two rects: a faint fill behind (brush_brush_bg) and a transparent frame on top
// (brush_brush). A theming rule once filled both with the ink color, so the frame hid the
// points it selected under a solid box. Checked in the light palette, with an old saved
// dark choice and dark OS preference, and in both forced-color palettes (where the brush
// takes Highlight).
// Not part of `npm run site:test` (it needs Chrome and a built site).
//
// Usage, after `npm run site:build`:
//   node site/test/browser/brush.mjs [--port 8126]
// Environment: PUPPETEER_CORE (a folder whose node_modules has puppeteer-core, if it isn't
// installed here) and CHROME_PATH (the Chrome executable). The script starts the preview
// server (site/scripts/serve.mjs) and stops it when it is done.
import { spawn } from 'node:child_process';
import { launchBrowser } from './browser.mjs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

const { values: args } = parseArgs({ options: { port: { type: 'string', default: '8126' } } });
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

/** The display modes checked: the brush must be see-through in each. */
const MODES = {
  light: { features: [] },
  'dark preference and saved choice': { features: [{ name: 'prefers-color-scheme', value: 'dark' }], savedDark: true },
  'forced colors, light': { features: [{ name: 'forced-colors', value: 'active' }, { name: 'prefers-color-scheme', value: 'light' }] },
  'forced colors, dark': { features: [{ name: 'forced-colors', value: 'active' }, { name: 'prefers-color-scheme', value: 'dark' }] },
};

/** In the page: each brush layer's painted fill, as its alpha times fill-opacity. */
function brushPaint() {
  const alpha = (color) => {
    const m = /rgba?\(([^)]+)\)/.exec(color);
    if (!m) return color === 'none' || color === 'transparent' ? 0 : 1;
    const parts = m[1].split(/[\s,/]+/).filter(Boolean);
    return parts.length > 3 ? Number(parts[3]) : 1;
  };
  const layer = (bg) => {
    const g = [...document.querySelectorAll('.catalog-chart svg g[class*="brush_brush"]')].find((el) => el.getAttribute('class').includes('brush_brush_bg') === bg);
    const p = g?.querySelector('path');
    if (!p) return null;
    const s = getComputedStyle(p);
    return { opacity: +(alpha(s.fill) * Number(s.fillOpacity)).toFixed(3), width: Math.round(p.getBoundingClientRect().width) };
  };
  return { back: layer(true), frame: layer(false) };
}

const server = await serve();
const browser = await launchBrowser();
const results = [];
function check(name, ok, detail) {
  results.push(ok);
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}  ${JSON.stringify(detail)}`);
}

try {
  for (const [mode, { features, savedDark }] of Object.entries(MODES)) {
    const page = await browser.newPage();
    await page.setViewport({ width: 1360, height: 900 });
    // Through the protocol: puppeteer's own helper refuses forced-colors.
    const cdp = await page.createCDPSession();
    await cdp.send('Emulation.setEmulatedMedia', { features });
    if (savedDark) await page.evaluateOnNewDocument(() => localStorage.setItem('vega-datasets-theme', 'dark'));
    await page.goto(base, { waitUntil: 'networkidle0' });
    if (savedDark) {
      const state = await page.evaluate(() => ({
        background: getComputedStyle(document.body).backgroundColor,
        expandable: document.documentElement.classList.contains('js'),
        saved: localStorage.getItem('vega-datasets-theme'),
      }));
      check('saved dark choice: page stays light and expandable lists initialize', state.background === 'rgb(255, 255, 255)' && state.expandable && state.saved === 'dark', state);
    }
    await page.evaluate(() => document.querySelector('.catalog-chart')?.scrollIntoView({ block: 'center' }));
    const box = await (await page.$('.catalog-chart')).boundingBox();
    // The chart goes live when the pointer first reaches it.
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.waitForSelector('.catalog-chart .vega-embed svg', { timeout: 15000 });
    await new Promise((res) => setTimeout(res, 500));
    const x = box.x + box.width * 0.35;
    const y = box.y + box.height * 0.25;
    await page.mouse.move(x, y);
    await page.mouse.down();
    await page.mouse.move(x + 220, y + 110, { steps: 10 });
    await page.mouse.up();
    await new Promise((res) => setTimeout(res, 300));
    const r = await page.evaluate(brushPaint);
    const drawn = r.back?.width > 100 && r.frame?.width > 100;
    check(`${mode}: the brush's frame is unfilled`, drawn && r.frame.opacity === 0, r);
    check(`${mode}: the brush's fill is faint`, drawn && r.back.opacity > 0 && r.back.opacity <= 0.3, r);
    await page.close();
  }
} finally {
  await browser.close();
  server.kill();
}
const passed = results.filter(Boolean).length;
console.log(`\n${passed} of ${results.length} checks passed.`);
process.exitCode = passed === results.length ? 0 : 1;
