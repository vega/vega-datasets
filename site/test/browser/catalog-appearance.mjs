// Build and serve first. Same PUPPETEER_CORE / CHROME_PATH overrides as the other
// browser checks. --baseline records the old behavior without parity assertions.
import assert from 'node:assert/strict';
import { writeFileSync } from 'node:fs';
import { launchBrowser } from './browser.mjs';
import { parseArgs } from 'node:util';
import { catalogGeometry } from './catalog-geometry.mjs';

const { values: args } = parseArgs({ options: {
  base: { type: 'string', default: 'http://127.0.0.1:8000/vega-datasets/' },
  output: { type: 'string' }, baseline: { type: 'boolean', default: false },
} });
const browser = await launchBrowser();
const results = { base: args.base, chrome: await browser.version(), samples: [], resizing: [] };
const frames = (page) => page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));
function delta(a, b) {
  assert.equal(a.points.length, b.points.length);
  const points = a.points.flatMap((p, i) => ['x', 'y', 'width', 'height'].map((key) => Math.abs(p[key] - b.points[i][key])));
  const text = a.text.map((t) => {
    const other = b.text.find((v) => v.text === t.text && v.role === t.role);
    return other ? Math.max(...['x', 'y', 'width', 'height', 'font'].map((key) => Math.abs(t[key] - other[key]))) : Infinity;
  });
  return { point: Math.max(...points), text: Math.max(...text), missingText: a.text.length !== b.text.length };
}
function readable(g) {
  assert.equal(g.overflow, 0);
  assert.ok(Math.min(...g.text.map((t) => t.font)) >= 10, 'Rendered type must be at least 10 CSS px');
  const labels = g.text.filter((t) => t.role.includes('role-mark'));
  for (const t of g.text) {
    assert.ok(t.x >= -1 && t.y >= -1 && t.x + t.width <= g.width + 1 && t.y + t.height <= g.height + 1, `Clipped text: ${t.text}`);
  }
  for (let i = 0; i < labels.length; i++) for (const b of labels.slice(i + 1)) {
    const a = labels[i];
    assert.ok(!(a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y), `Overlapping labels: ${a.text} / ${b.text}`);
  }
}
const parity = (a, b) => {
  const d = delta(a, b);
  assert.ok(d.point <= 0.25 && d.text <= 0.25 && !d.missingText, `Internal geometry changed: ${JSON.stringify(d)}`);
  assert.ok(Math.abs(a.height - b.height) < 0.25 && Math.abs(a.width - b.width) < 0.25);
};
async function interactions(page, keepBrush = false) {
  await page.$eval('[data-chart]', (e) => e.scrollIntoView({ block: 'center' }));
  // Deliver the scroll event that dismisses tooltips before testing a new hover.
  await frames(page);
  for (const name of ['cars', 'stocks']) {
    const p = await (await page.$(`.chart-live .mark-symbol path[aria-label^="${name}:"]`)).boundingBox();
    await page.mouse.move(p.x + p.width / 2, p.y + p.height / 2);
    await page.waitForFunction((name) => document.querySelector('#vg-tooltip-element.visible')?.textContent.includes(name), {}, name);
  }
  const g = await page.evaluate(catalogGeometry);
  const box = await (await page.$('.chart-live svg.marks')).boundingBox();
  const area = { x: g.width * .33, y: g.height * .2, width: g.width * .36, height: g.height * .43 };
  const selected = g.points.filter((p) => p.x + p.width / 2 > area.x && p.x + p.width / 2 < area.x + area.width && p.y + p.height / 2 > area.y && p.y + p.height / 2 < area.y + area.height);
  assert.ok(selected.length > 0 && selected.length < g.points.length);
  await page.mouse.move(box.x + area.x, box.y + area.y);
  await page.mouse.down();
  await page.mouse.move(box.x + area.x + area.width, box.y + area.y + area.height, { steps: 10 });
  await page.mouse.up();
  await page.waitForFunction(() => document.querySelector('.status').textContent.includes('filtered by chart'));
  const count = await page.$eval('.status', (e) => Number(e.textContent.match(/(\d+) of/)[1]));
  assert.equal(count, selected.length, 'Brush must select the points inside the rendered rectangle');
  const brush = await (await page.$('.chart-live [class*="brush_brush_bg"] path')).boundingBox();
  for (const key of ['width', 'height']) assert.ok(Math.abs(brush[key] - area[key]) < 1, `Scaled brush ${key}`);
  assert.ok(Math.abs(brush.x - box.x - area.x) < 1 && Math.abs(brush.y - box.y - area.y) < 1, 'Scaled brush origin');
  if (!keepBrush) {
    await page.mouse.click(box.x + area.x, box.y + area.y, { count: 2 });
    await page.waitForFunction(() => !document.querySelector('.status').textContent.includes('filtered by chart'));
  }
  return { tooltipTargets: ['cars', 'stocks'], selected: count, brush: area };
}
try {
  // Include both sides of the container-layout thresholds and the touch/brush breakpoint.
  for (const width of [320, 390, 430, 512, 513, 640, 641, 768, 800, 801, 1000, 1080, 1081, 1360]) {
    const context = await browser.createBrowserContext();
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    await page.setViewport({ width, height: 900, isMobile: width <= 640, hasTouch: width <= 640, deviceScaleFactor: 1 });
    await page.goto(args.base, { waitUntil: 'networkidle0' });
    const initialRuntime = await page.evaluate(() => performance.getEntriesByType('resource').some((e) => e.name.endsWith('.js') && e.decodedBodySize > 100_000));
    assert.equal(initialRuntime, false);
    await page.$eval('[data-chart]', (e) => e.scrollIntoView({ block: 'center' }));
    const before = await page.evaluate(catalogGeometry);
    if (args.output && [390, 641, 800, 1360].includes(width)) await (await page.$('[data-chart]')).screenshot({ path: args.output.replace(/\.json$/, `-${width}-static.png`) });
    if (width > 640) await page.hover('[data-chart]');
    else await page.tap('[data-format="JSON"]');
    await page.waitForSelector('.chart-live:not(.pending) svg.marks');
    await frames(page);
    const after = await page.evaluate(catalogGeometry);
    const change = delta(before, after);
    results.samples.push({ width, before, after, change });
    console.log(`${width}px: dot ${before.points[0].width.toFixed(2)} → ${after.points[0].width.toFixed(2)}, font ${Math.min(...before.text.map((t) => t.font)).toFixed(2)} → ${Math.min(...after.text.map((t) => t.font)).toFixed(2)}, max point/text shift ${change.point.toFixed(3)}/${change.text.toFixed(3)}`);
    if (!args.baseline) {
      parity(before, after); readable(before); readable(after);
      if ([641, 768, 800, 1360].includes(width)) results.samples.at(-1).interaction = await interactions(page);
      if (args.output && [390, 641, 800, 1360].includes(width)) await (await page.$('[data-chart]')).screenshot({ path: args.output.replace(/\.json$/, `-${width}-live.png`) });
      for (const gallery of ['vega', 'vega-lite', 'vega', 'altair', 'vega', 'vega-lite', 'vega']) {
        await page.click(`[data-gallery="${gallery}"]`);
        await page.waitForFunction(() => !document.querySelector('.chart-live.pending'));
        await frames(page);
        readable(await page.evaluate(catalogGeometry));
      }
    }
    assert.deepEqual(errors, []);
    await context.close();
  }
  if (!args.baseline) {
    const page = await browser.newPage();
    await page.setViewport({ width: 1360, height: 900 });
    await page.goto(args.base, { waitUntil: 'networkidle0' });
    await page.hover('[data-chart]');
    await page.waitForSelector('.chart-live:not(.pending) svg.marks');
    for (const width of [800, 768, 641, 640, 390, 513, 512, 801, 1081, 1080, 1360]) {
      await page.setViewport({ width, height: 900 });
      // Wait for the entire replacement (if any), including the resize debounce.
      await new Promise((r) => setTimeout(r, 300));
      await page.waitForFunction(() => !document.querySelector('.pending'));
      const g = await page.evaluate(catalogGeometry);
      const reference = results.samples.find((s) => s.width === width).before;
      parity(reference, g); readable(g);
      results.resizing.push({ width, change: delta(reference, g) });
      if ([800, 641].includes(width)) results.resizing.at(-1).interaction = await interactions(page);
    }
    // A container change without a window resize must select the same reference drawing.
    await page.$eval('[data-chart]', (e) => e.style.width = '601px');
    await page.waitForFunction(() => document.querySelector('.chart-live:not(.pending) svg.marks')?.viewBox.baseVal.width === 640 && !document.querySelector('.pending'));
    parity(results.samples.find((s) => s.width === 641).before, await page.evaluate(catalogGeometry));
    results.containerResize = await interactions(page);
    // Fractional widths must match CSS's breakpoint choice (clientWidth rounds).
    await page.$eval('[data-chart]', (e) => e.style.width = '480.25px');
    await page.waitForFunction(() => !document.querySelector('.pending'));
    await new Promise((r) => setTimeout(r, 200));
    assert.equal(await page.$eval('.chart-live svg.marks', (e) => e.viewBox.baseVal.width), 640);
    await page.$eval('[data-chart]', (e) => e.style.width = '');
    await page.waitForFunction(() => document.querySelector('.chart-live:not(.pending) svg.marks')?.viewBox.baseVal.width === 1242 && !document.querySelector('.pending'));
    const selected = await interactions(page, true);
    await page.setViewport({ width: 800, height: 900 });
    await page.waitForFunction(() => document.querySelector('.chart-live:not(.pending) svg.marks')?.viewBox.baseVal.width === 640 && !document.querySelector('.pending'));
    assert.equal(await page.$eval('.status', (e) => Number(e.textContent.match(/(\d+) of/)[1])), selected.selected);
    results.selectionSurvivesLayout = true;
    await page.close();

    // Keyboard filtering keeps focus, and the native actions retain standalone legends.
    const actions = await browser.newPage();
    await actions.setViewport({ width: 800, height: 900 });
    await actions.goto(args.base, { waitUntil: 'networkidle0' });
    await actions.focus('#home-q');
    await actions.keyboard.type('cars');
    await actions.waitForSelector('.chart-live:not(.pending) svg.marks');
    assert.equal(await actions.$eval('#home-q', (e) => document.activeElement === e), true);
    await actions.click('[data-gallery="vega"]');
    await actions.waitForFunction(() => document.querySelector('.chart-live svg').textContent.includes('Vega examples'));
    await actions.evaluate(() => {
      const create = URL.createObjectURL.bind(URL);
      URL.createObjectURL = (blob) => {
        if (blob.type.includes('svg')) blob.text().then((text) => window.__exportSVG = text);
        return create(blob);
      };
      window.open = () => ({ postMessage: (data) => { window.__editor = data; } });
    });
    await actions.click('.chart-live summary');
    await actions.$eval('.vega-actions a[download$=".svg"]', (a) => a.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true })));
    await actions.waitForFunction(() => window.__exportSVG);
    const svg = await actions.evaluate(() => window.__exportSVG);
    assert.match(svg, /role-legend/); assert.match(svg, />Format</); assert.match(svg, />CSV</); assert.match(svg, />JSON</);
    await actions.$eval('.vega-actions a[download$=".png"]', (a) => a.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true })));
    await actions.waitForFunction(() => /^(data:|blob:)/.test(document.querySelector('.vega-actions a[download$=".png"]').href));
    const png = await actions.$eval('.vega-actions a[download$=".png"]', (a) => new Promise((resolve, reject) => {
      const img = new Image(); img.onload = () => resolve({ width: img.naturalWidth, height: img.naturalHeight }); img.onerror = reject; img.src = a.href;
    }));
    assert.ok(png.width >= 700 && png.height > 240);
    await actions.$eval('.vega-actions', (e) => [...e.querySelectorAll('a')].find((a) => a.textContent.includes('Editor')).click());
    await actions.waitForFunction(() => window.__editor);
    const editor = await actions.evaluate(() => JSON.parse(window.__editor.spec));
    assert.equal(editor.autosize.type, 'fit-x');
    assert.equal(editor.layer[0].encoding.color.legend.title, 'Format');
    assert.deepEqual(editor.params.find((p) => p.name === 'galleries').value, ['vega']);
    assert.deepEqual(editor.params.find((p) => p.name === 'matched').value, ['cars']);
    assert.ok(editor.data.values.every((r) => r.href.startsWith('http')));
    const { compile } = await import('vega-lite');
    const vega = await import('vega');
    const exported = new vega.View(vega.parse(compile(editor).spec), { renderer: 'none' });
    await exported.runAsync();
    assert.match(await exported.toSVG(), /role-legend/);
    exported.finalize();
    results.actions = { keyboardFocus: true, svgLegend: true, editorLegend: true, filterSnapshot: true, png };
    if (args.output) writeFileSync(args.output.replace(/\.json$/, '-export.svg'), svg);
    await actions.close();

    for (const live of [false, true]) {
      const phone = await browser.newPage();
      await phone.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });
      await phone.goto(args.base, { waitUntil: 'networkidle0' });
      await phone.$eval('[data-chart]', (e) => e.scrollIntoView({ block: 'center' }));
      if (live) {
        await phone.tap('[data-format="JSON"]');
        await phone.waitForSelector('.chart-live:not(.pending) svg.marks');
        await phone.$eval('[data-chart]', (e) => e.scrollIntoView({ block: 'center' }));
      }
      await frames(phone);
      await phone.evaluate(() => {
        window.__swipeEnded = false;
        document.addEventListener('scrollend', () => { window.__swipeEnded = true; }, { once: true });
      });
      const chart = await (await phone.$('[data-chart]')).boundingBox();
      const y = await phone.evaluate(() => scrollY);
      const cdp = await phone.createCDPSession();
      await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: chart.x + chart.width / 2, y: chart.y + chart.height / 2 }] });
      for (let dy = 20; dy <= 120; dy += 20) await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: chart.x + chart.width / 2, y: chart.y + chart.height / 2 - dy }] });
      await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
      await phone.waitForFunction((y) => scrollY > y + 30, {}, y);
      assert.equal(await phone.$('#vg-tooltip-element.visible'), null);
      // A tap during inertial scrolling stops the scroll rather than following a link.
      await phone.waitForFunction(() => window.__swipeEnded);
      await phone.$eval('[data-chart]', (e) => e.scrollIntoView({ block: 'center' }));
      await frames(phone);
      const prefix = live ? '.chart-live' : '.chart-static';
      const point = (await phone.$$(`${prefix} .mark-symbol path[aria-label^="cars:"]`));
      const visible = (await Promise.all(point.map(async (p) => ({ p, box: await p.boundingBox() })))).find((p) => p.box?.width > 0).p;
      await Promise.all([phone.waitForNavigation(), visible.tap()]);
      assert.ok(phone.url().endsWith('/datasets/cars/'));
      await phone.close();
    }
    results.mobile = { staticTap: true, liveTap: true, chartSwipeScrolls: true, tooltipDismissed: true };
  }
} finally {
  if (args.output) writeFileSync(args.output, JSON.stringify(results, null, 2));
  await browser.close();
}
