// A chart's tooltip doesn't stay on screen once a touch gesture has moved on. On a phone, a
// scroll that starts on a chart sends pointerdown, pointermove and pointercancel (a long
// press and drag ends with pointerup instead); vega-tooltip shows on the pointermove and,
// with no pointerout on the item, stayed shown, fixed to the viewport, floating over the
// page as it scrolled. The mouse keeps its hover tooltip.
// Not part of `npm run site:test` (it needs Chrome and a built site).
//
// Usage, after `npm run site:build`:
//   node site/test/browser/touch-tooltip.mjs [--port 8125]
// Environment: PUPPETEER_CORE (a folder whose node_modules has puppeteer-core, if it isn't
// installed here) and CHROME_PATH (the Chrome executable). The script starts the preview
// server (site/scripts/serve.mjs) and stops it when it is done.
import { spawn } from 'node:child_process';
import { launchBrowser } from './browser.mjs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

const { values: args } = parseArgs({ options: { port: { type: 'string', default: '8125' } } });
const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '..', '..', '..');
const base = `http://localhost:${args.port}/vega-datasets/`;

/** Start the preview server and resolve once it listens. */
function serve() {
  const child = spawn(process.execPath, [path.join(repo, 'site', 'scripts', 'serve.mjs'), '--port', args.port], { stdio: ['ignore', 'pipe', 'inherit'] });
  return new Promise((resolve, reject) => {
    child.stdout.on('data', (b) => { if (String(b).includes('Vega Datasets at')) resolve(child); });
    child.on('exit', (code) => reject(new Error(`The preview server exited (${code})`)));
  });
}

const PHONE = { width: 412, height: 915, deviceScaleFactor: 2, isMobile: true, hasTouch: true };
/** Touch gestures that start on a chart mark, as their pointer events arrive. */
const GESTURES = {
  'a scroll that starts on the chart': ['pointerover', 'pointerenter', 'pointerdown', 'pointermove', 'pointercancel', 'pointerout', 'pointerleave'],
  'a long press and drag': ['pointerover', 'pointerenter', 'pointerdown', 'pointermove', 'pointermove', 'pointerup', 'pointerout', 'pointerleave'],
};
/**
 * A bar chart (Explore on lookup_people) and a scatter plot (cars). The home page's catalog
 * chart goes live only when a reader first touches it, and embeds with the same options.
 */
const PAGES = [['lookup_people', 'datasets/lookup_people/', '#explore'], ['cars', 'datasets/cars/', '#explore']];

/** In the page: play `events` on the chart's first mark under `root`, then scroll; what the tooltip did. */
async function play({ root, events, pointerType }) {
  const host = document.querySelector(root);
  const mark = host && [...host.querySelectorAll('svg g.mark-rect path, svg g.mark-symbol path')].find((m) => m.getBoundingClientRect().width > 0);
  if (!mark) return { mark: false };
  const r = mark.getBoundingClientRect();
  const init = { bubbles: true, cancelable: true, composed: true, clientX: r.x + r.width / 2, clientY: r.y + r.height / 2, view: window, pointerType, pointerId: 2, isPrimary: true };
  for (const type of events) {
    mark.dispatchEvent(new PointerEvent(type, init));
    await new Promise((res) => setTimeout(res, 30));
  }
  const shown = () => document.getElementById('vg-tooltip-element')?.classList.contains('visible') ?? false;
  const afterGesture = shown();
  window.scrollBy(0, 400);
  await new Promise((res) => setTimeout(res, 400));
  return { mark: true, afterGesture, afterScroll: shown() };
}

const server = await serve();
const browser = await launchBrowser();
const results = [];
function check(name, ok, detail) {
  results.push(ok);
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}  ${JSON.stringify(detail)}`);
}

/** A fresh phone page at `url`, scrolled to `root` with its chart drawn. */
async function open(url, root) {
  const page = await browser.newPage();
  await page.setViewport(PHONE);
  await page.goto(base + url, { waitUntil: 'networkidle0' });
  await page.evaluate((sel) => document.querySelector(sel)?.scrollIntoView(), root);
  await page.waitForFunction((sel) => document.querySelector(sel)?.querySelector('svg g.mark-rect path, svg g.mark-symbol path'), { timeout: 15000 }, root);
  return page;
}

try {
  for (const [label, url, root] of PAGES) {
    for (const [gesture, events] of Object.entries(GESTURES)) {
      const page = await open(url, root);
      const r = await page.evaluate(play, { root, events, pointerType: 'touch' });
      check(`${label}: after ${gesture} and a scroll, no tooltip`, r.mark && !r.afterScroll, r);
      await page.close();
    }
    // The mouse still gets its tooltip: hovering shows it and a scroll doesn't break that.
    const page = await open(url, root);
    const r = await page.evaluate(play, { root, events: ['pointerover', 'pointerenter', 'pointermove'], pointerType: 'mouse' });
    check(`${label}: a mouse hover shows the tooltip`, r.mark && r.afterGesture, r);
    await page.close();
  }
} finally {
  await browser.close();
  server.kill();
}
const passed = results.filter(Boolean).length;
console.log(`\n${passed} of ${results.length} checks passed.`);
process.exitCode = passed === results.length ? 0 : 1;
