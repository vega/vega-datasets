// Real Chrome checks for chart activation, mode reuse and responsive size stability.
// First build and serve the site, then run:
//   node site/test/browser/chart-interactions.mjs --base http://127.0.0.1:8000/vega-datasets/
// Add --measure --output report.json for three cold/approached mobile activation runs
// and six mode switches, at 4x CPU, ~1.68 Mbps down / 768 Kbps up and 150 ms latency.
// PUPPETEER_CORE and CHROME_PATH follow the other browser checks in this directory.
import assert from 'node:assert/strict';
import { writeFileSync } from 'node:fs';
import { launchBrowser } from './browser.mjs';
import { parseArgs } from 'node:util';

const { values: args } = parseArgs({ options: {
  base: { type: 'string', default: 'http://127.0.0.1:8000/vega-datasets/' },
  measure: { type: 'boolean', default: false }, output: { type: 'string' },
} });
const browser = await launchBrowser();
const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const frames = (page) => page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
const results = { base: args.base, chrome: await browser.version(), checks: [], home: [], cars: [] };

async function open(route = '', width = 390, measured = false) {
  const context = await browser.createBrowserContext();
  const page = await context.newPage();
  await page.setViewport({ width, height: 844, deviceScaleFactor: width <= 640 ? 3 : 1, isMobile: width <= 640, hasTouch: width <= 640 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  if (measured) {
    await page.setCacheEnabled(false);
    const cdp = await page.createCDPSession();
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
    await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 150, downloadThroughput: 1.6 * 1024 * 1024 / 8, uploadThroughput: 750 * 1024 / 8 });
    await page.evaluateOnNewDocument(() => {
      window.__events = [];
      new PerformanceObserver((list) => {
        for (const e of list.getEntries()) if (e.interactionId) window.__events.push({ id: e.interactionId, type: e.name, at: e.startTime, duration: e.duration, processing: e.processingEnd - e.processingStart });
      }).observe({ type: 'event', buffered: true, durationThreshold: 16 });
    });
  }
  await page.goto(args.base + route, { waitUntil: 'networkidle0', timeout: 120_000 });
  return { page, context, errors };
}

function geometry() {
  const host = document.querySelector('[data-chart]');
  const svg = [...host.querySelectorAll('svg.marks')].find((s) => s.getBoundingClientRect().width > 0);
  const box = svg.getBoundingClientRect();
  return { width: box.width, height: box.height, hostHeight: host.getBoundingClientRect().height, overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth };
}
async function carsReady(page) {
  await page.waitForFunction(() => document.querySelector('#explore svg.marks') && !document.querySelector('#explore [aria-busy]'), { timeout: 60_000 });
}
async function arm(page, kind) {
  await page.evaluate((kind) => {
    window.__clickResult = null;
    window.__armedAt = performance.now();
    const selector = kind === 'home' ? '[data-gallery="vega"]' : '#explore [data-mode]';
    const current = () => kind === 'home'
      ? document.querySelector('.chart-live:not(.pending) svg.marks')
      : document.querySelector('.explore-view:not([hidden]):not(.pending) svg.marks') ?? document.querySelector('.explore-chart > .chart-wrapper svg.marks');
    const old = current();
    document.addEventListener('click', function click(event) {
      if (!event.target.closest(selector)) return;
      document.removeEventListener('click', click, true);
      const at = event.timeStamp;
      const observer = new MutationObserver(() => {
        const next = current();
        if (!next || next === old || document.querySelector('#explore [aria-busy]')) return;
        observer.disconnect();
        requestAnimationFrame(() => requestAnimationFrame(() => {
          window.__clickResult = { at, readyMs: performance.now() - at, mode: event.target.closest(selector).textContent.trim() };
        }));
      });
      observer.observe(document.querySelector(kind === 'home' ? '[data-chart]' : '#explore'), { subtree: true, childList: true, attributes: true });
    }, true);
  }, kind);
}
async function result(page) {
  await page.waitForFunction(() => window.__clickResult, { timeout: 60_000 });
  await pause(150); // Event Timing is delivered after the next paint.
  return page.evaluate(() => {
    const events = window.__events.filter((e) => e.at >= window.__armedAt);
    const click = events.find((e) => e.type === 'click' && Math.abs(e.at - window.__clickResult.at) < 2);
    // A short click may fall below Event Timing's 16 ms minimum even if its pointer
    // events were slower. Include the whole interaction, not just its click entry.
    const interaction = click ?? events.findLast((e) => /^(pointerdown|pointerup)$/.test(e.type) && e.at <= window.__clickResult.at);
    const group = interaction ? events.filter((e) => e.id === interaction.id) : [];
    return { ...window.__clickResult, events: group, interactionMs: group.length ? Math.max(...group.map((e) => e.duration)) : null };
  });
}

try {
  if (!args.measure) {
    for (const width of [320, 390, 430, 641, 768, 1000, 1360]) {
      const { page, context, errors } = await open('', width);
      const initialRuntime = await page.evaluate(() => performance.getEntriesByType('resource').some((e) => /\/assets\/vega[.-]/.test(e.name) || (e.name.endsWith('.js') && e.decodedBodySize > 100_000)));
      assert.equal(initialRuntime, false, 'Opening the home page must not load the chart runtime');
      await page.$eval('[data-chart]', (e) => e.scrollIntoView({ block: 'center' }));
      const before = await page.evaluate(geometry);
      // A mouse activates on hover; a phone activates through a filter, not a point tap.
      if (width > 640) await page.hover('[data-chart]');
      else await page.tap('[data-format="JSON"]');
      await page.waitForSelector('.chart-live:not(.pending) svg.marks', { timeout: 60_000 });
      await frames(page);
      const after = await page.evaluate(geometry);
      assert.ok(Math.abs(before.height - after.height) <= 2, `${width}px chart height changed: ${JSON.stringify({ before, after })}`);
      assert.ok(Math.abs(before.width - after.width) <= 2, `${width}px chart width changed: ${JSON.stringify({ before, after })}`);
      assert.equal(after.overflow, 0);
      assert.deepEqual(errors, []);
      results.checks.push({ name: `Stable activation at ${width}px`, before, after });
      console.log(`Stable chart size at ${width}px: ${before.height.toFixed(1)} → ${after.height.toFixed(1)}px`);
      if (args.output && [390, 1000].includes(width)) await (await page.$('[data-chart]')).screenshot({ path: args.output.replace(/\.json$/, `-${width}.png`) });
      if (width === 1000) {
        await page.setViewport({ width: 800, height: 844 });
        await page.waitForFunction(() => document.querySelector('.chart-live:not(.pending) svg.marks')?.viewBox.baseVal.width === 640 && !document.querySelector('.chart-live.pending'), { timeout: 15_000 });
        const resized = await page.evaluate(geometry);
        assert.equal(resized.overflow, 0);
        assert.ok(resized.height > 150 && resized.height < 400, 'Compact layout stays usable after resizing');
        results.checks.push({ name: 'Active chart refits from 1000px to 800px', before: after, after: resized });
      }
      if ([390, 641].includes(width)) {
        await page.click('[data-gallery="vega"]');
        await page.waitForFunction(() => document.querySelector('.chart-live svg.marks').textContent.includes('Vega examples'));
        await frames(page);
        const labels = await page.$$eval('.chart-live svg.marks .role-mark text', (nodes) => nodes.filter((e) => e.textContent).map((e) => ({ text: e.textContent, ...e.getBoundingClientRect().toJSON() })));
        assert.ok(labels.length > 0);
        for (let i = 0; i < labels.length; i++) for (const b of labels.slice(i + 1)) {
          const a = labels[i];
          assert.equal(a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top, false, `Labels overlap at ${width}px: ${a.text} / ${b.text}`);
        }
        results.checks.push({ name: `Vega labels stay apart at ${width}px`, labels: labels.map((e) => e.text) });
      }
      await context.close();
    }
    const { page, context, errors } = await open('datasets/cars/');
    await page.$eval('#explore', (e) => e.scrollIntoView());
    await carsReady(page);
    await page.select('#explore .binds select[name="xField"]', 'Horsepower');
    await page.select('#explore .binds select[name="yField"]', 'Weight_in_lbs');
    await page.waitForFunction(() => document.querySelector('#explore .chart-caption .hint').textContent.includes('400 of 406'));
    await page.evaluate(() => { window.__scatter = document.querySelector('.explore-view svg.marks'); window.__select = document.querySelector('.binds select'); });
    for (let i = 0; i < 3; i++) {
      await page.tap('#explore [data-mode="time"]'); await carsReady(page);
      await page.tap('#explore [data-mode="scatter"]'); await carsReady(page);
    }
    const kept = await page.evaluate(() => ({
      svg: window.__scatter === document.querySelector('.explore-view:not([hidden]) svg.marks'),
      input: window.__select === document.querySelector('.binds select'),
      draws: document.querySelector('#explore').dataset.draws,
      views: document.querySelectorAll('.explore-view').length,
      picks: [...document.querySelectorAll('.binds select')].map((s) => s.value),
      caption: document.querySelector('.chart-caption .hint').textContent,
    }));
    assert.equal(kept.svg, true); assert.equal(kept.input, true); assert.equal(kept.draws, '2'); assert.equal(kept.views, 2);
    assert.deepEqual(kept.picks, ['Horsepower', 'Weight_in_lbs']); assert.ok(kept.caption.includes('400 of 406'));
    await page.tap('#explore [data-mode="time"]'); await carsReady(page);
    await page.setViewport({ width: 430, height: 844, isMobile: true, hasTouch: true, deviceScaleFactor: 3 });
    await page.tap('#explore [data-mode="scatter"]'); await carsReady(page);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth), 0);
    assert.deepEqual(errors, []);
    results.checks.push({ name: 'Cars retains two views, input nodes and chosen fields; hidden views refit on resize', ...kept });
    await context.close();
  } else {
    results.conditions = { cpu: 4, downloadMbps: 1.6 * 1024 * 1024 / 1e6, uploadKbps: 750 * 1024 / 1000, latencyMs: 150, width: 390, height: 844, deviceScaleFactor: 3, cache: false, kind: 'lab; not field INP or a physical phone' };
    for (const approachMs of [0, 2000]) for (let run = 1; run <= 3; run++) {
      const { page, context, errors } = await open('', 390, true);
      await page.$eval('.filters', (e) => e.scrollIntoView({ block: 'center' }));
      if (approachMs) await pause(approachMs);
      await arm(page, 'home');
      await page.tap('[data-gallery="vega"]');
      const sample = { approachMs, run, ...await result(page) };
      results.home.push(sample);
      console.log(`Home approach=${approachMs} run=${run}: ${sample.readyMs.toFixed(0)}ms`);
      assert.deepEqual(errors, []);
      await context.close();
    }
    const { page, context, errors } = await open('datasets/cars/', 390, true);
    await page.$eval('#explore', (e) => e.scrollIntoView());
    await carsReady(page);
    await page.select('#explore .binds select[name="xField"]', 'Horsepower');
    await page.select('#explore .binds select[name="yField"]', 'Weight_in_lbs');
    await page.waitForFunction(() => document.querySelector('#explore .chart-caption .hint').textContent.includes('400 of 406'));
    if (args.output) await page.tracing.start({ path: args.output.replace(/\.json$/, '-cars-trace.json') });
    for (let i = 0; i < 3; i++) for (const mode of ['time', 'scatter']) {
      await arm(page, 'cars');
      await page.tap(`#explore [data-mode="${mode}"]`);
      const sample = await result(page);
      results.cars.push(sample);
      console.log(`Cars ${mode}: ${sample.readyMs.toFixed(0)}ms to chart, ${sample.interactionMs ?? '<16'}ms interaction`);
    }
    if (args.output) await page.tracing.stop();
    assert.deepEqual(errors, []);
    await context.close();
  }
  console.log(`${results.checks.length} functional checks; ${results.home.length} activation and ${results.cars.length} mode measurements passed.`);
} finally {
  if (args.output) writeFileSync(args.output, JSON.stringify(results, null, 2));
  await browser.close();
}
