// The large-data policy (lib/large-data.ts, lib/device.ts): which band a table falls in,
// which devices draw mid-size tables by themselves, which maps open on a picture, and the
// density overview binned when the site is built.
import * as vega from 'vega';
import { compile, type TopLevelSpec } from 'vega-lite';
import { describe, expect, test } from 'vitest';
import { DESKTOP_MIN_CORES, DESKTOP_MIN_MEMORY_GB, deviceSignals, type DeviceSignals, FINE_POINTER, isDesktopClass } from '../src/lib/device';
import { defaultAxes, scatterFields, scatterSpec } from '../src/lib/explore-model';
import {
  allowed,
  AUTO_DRAW_MAX_ROWS,
  BAND_POLICY,
  DENSITY_BINS,
  DENSITY_MAX_LABELS,
  densityCaption,
  densityGrid,
  densityPageSpec,
  densitySpec,
  drawPointsLabel,
  groupDigits,
  hasMapPreview,
  labelEdges,
  mapMarks,
  MAP_PREVIEW_MARKS,
  niceStep,
  POINTS_MAX_ROWS,
  rowBand,
  SVG_MAX_ROWS,
  tableBand,
} from '../src/lib/large-data';
import { densityOf } from '../src/prerender/density';
import { loadCatalog, readDataUrl } from './catalog';

const catalog = loadCatalog();
const ds = (name: string) => catalog.dataset(name)!;

describe('the device check', () => {
  const desktop: DeviceSignals = { finePointer: true, cores: 8, memoryGb: 8, saveData: false };

  test('a fine pointer, 4 cores, 4 GB and no Save-Data is desktop-class', () => {
    expect(isDesktopClass(desktop)).toBe(true);
    expect(isDesktopClass({ ...desktop, cores: DESKTOP_MIN_CORES, memoryGb: DESKTOP_MIN_MEMORY_GB })).toBe(true);
  });

  test('each signal alone rules it out', () => {
    expect(isDesktopClass({ ...desktop, finePointer: false })).toBe(false);
    expect(isDesktopClass({ ...desktop, cores: DESKTOP_MIN_CORES - 1 })).toBe(false);
    expect(isDesktopClass({ ...desktop, cores: undefined })).toBe(false);
    expect(isDesktopClass({ ...desktop, memoryGb: DESKTOP_MIN_MEMORY_GB / 2 })).toBe(false);
    expect(isDesktopClass({ ...desktop, saveData: true })).toBe(false);
  });

  test('memory counts only where the browser reports it (Firefox and Safari do not)', () => {
    expect(isDesktopClass({ ...desktop, memoryGb: undefined })).toBe(true);
  });

  test('the signals are read from the window', () => {
    const queries: string[] = [];
    const win = (fine: boolean, nav: object) => ({ matchMedia: (q: string) => (queries.push(q), { matches: fine }), navigator: nav });
    expect(deviceSignals(win(true, { hardwareConcurrency: 8, deviceMemory: 8, connection: { saveData: true } }))).toEqual({ finePointer: true, cores: 8, memoryGb: 8, saveData: true });
    expect(deviceSignals(win(false, {}))).toEqual({ finePointer: false, cores: undefined, memoryGb: undefined, saveData: false });
    expect(queries).toEqual([FINE_POINTER, FINE_POINTER]);
  });
});

describe('the bands', () => {
  test.each([
    [1, 'svg'],
    [4_999, 'svg'],
    [5_000, 'svg'],
    [5_001, 'canvas'],
    [20_000, 'canvas'],
    [20_001, 'on-request'],
    [50_000, 'on-request'],
    [50_001, 'density'],
    [3_000_000, 'density'],
  ] as const)('%i rows: %s', (rows, band) => {
    expect(rowBand(rows)).toBe(band);
  });

  test('the thresholds are the policy', () => {
    expect([SVG_MAX_ROWS, AUTO_DRAW_MAX_ROWS, POINTS_MAX_ROWS, MAP_PREVIEW_MARKS]).toEqual([5_000, 20_000, 50_000, 1_000]);
  });

  test('what each band allows, on a desktop-class device and elsewhere', () => {
    const on = (desktop: boolean) =>
      Object.fromEntries(Object.entries(BAND_POLICY).map(([band, p]) => [band, [p.renderer, allowed(p.autoDraw, desktop), allowed(p.zoom, desktop)]]));
    expect(on(true)).toEqual({ svg: ['svg', true, true], canvas: ['canvas', true, true], 'on-request': ['canvas', false, false], density: ['canvas', false, false] });
    expect(on(false)).toEqual({ svg: ['svg', true, true], canvas: ['canvas', false, false], 'on-request': ['canvas', false, false], density: ['canvas', false, false] });
  });

  test('the catalog: flights_20k (exactly 20,000 rows) draws by itself on a desktop only; flights_200k_json opens on density', () => {
    expect(tableBand(ds('flights_20k'))).toBe('canvas');
    expect(tableBand(ds('flights_5k'))).toBe('svg');
    expect(tableBand(ds('flights_200k_json'))).toBe('density');
    expect(tableBand(ds('us_10m'))).toBeNull();
    expect(drawPointsLabel(ds('flights_20k'))).toBe('Draw 20,000 Points (1.8 MB)');
    expect(drawPointsLabel(ds('flights_200k_json'))).toBe('Draw All 200,000 Points (9.9 MB)');
  });

  test('points on canvas are fainter, and zoom only where the band allows it', () => {
    const opacity = (name: string) => {
      const d = ds(name);
      const f = scatterFields(d)!;
      const layer = (scatterSpec(d, f, { ...defaultAxes(f), zoom: false, height: 300 }).layer as { mark: { opacity: number } }[])[0]!;
      return layer.mark.opacity;
    };
    expect(opacity('cars')).toBe(0.8);
    expect(opacity('flights_20k')).toBe(0.35);
  });
});

describe('the map rule counts the shapes or points the starter map draws', () => {
  test.each([
    ['us_10m', 3_641, true],
    ['zipcodes', 42_049, true],
    ['earthquakes', 1_707, true],
    ['airports', 3_376, true],
    ['windvectors', 4_800, true],
    ['london_tube_lines', 394, false],
    ['world_110m', 1, false],
    ['us_state_capitals', 50, false],
  ] as const)('%s: %i', (name, marks, preview) => {
    expect(mapMarks(ds(name))).toBe(marks);
    expect(hasMapPreview(ds(name))).toBe(preview);
  });

  test('tables that are not maps have no mark count', () => {
    expect(mapMarks(ds('flights_200k_json'))).toBeNull();
    expect(mapMarks(ds('cars'))).toBeNull();
  });
});

describe('the density builder', () => {
  test('nice steps are 1, 2 or 5 × 10^k with at most maxbins bins', () => {
    expect(niceStep(0, 100, 10)).toBe(10);
    expect(niceStep(0, 101, 10)).toBe(20);
    expect(niceStep(-3, 3, 50)).toBe(0.2);
    expect(niceStep(5, 5, 10)).toBe(1);
  });

  test('bins between the 0.5th and 99.5th percentiles, and counts the rest as outside', () => {
    // 1,000 rows on a diagonal from 0 to 999, one far outlier on each axis, and three rows missing a value.
    const rows: Record<string, unknown>[] = Array.from({ length: 1000 }, (_, i) => ({ a: i, b: String(i) }));
    rows.push({ a: 1e6, b: 5 }, { a: 5, b: -1e6 }, { a: null, b: 1 }, { a: 2, b: '' }, { b: 3 });
    const g = densityGrid(rows, 'a', 'b', { x: 10, y: 10 });
    expect(g.rows).toBe(1005);
    expect(g.complete).toBe(1002);
    // The box ends at the quantiles (interpolated between ranks), so the lowest and highest few rows fall outside it.
    expect(g.box.x[0]).toBe(5);
    expect(g.box.x[1]).toBeCloseTo(994.995, 6);
    const inBox = rows.filter((r) => {
      const [a, b] = [Number(r.a), r.b === '' || r.b === undefined ? NaN : Number(r.b)];
      return r.a !== null && r.a !== undefined && Number.isFinite(b) && a >= g.box.x[0] && a <= g.box.x[1] && b >= g.box.y[0] && b <= g.box.y[1];
    }).length;
    expect(g.outside).toBe(g.complete - inBox);
    expect(g.cells.reduce((s, [, , n]) => s + n, 0)).toBe(inBox);
    expect(g.xstep).toBe(100);
    expect(g.xstart).toBe(0);
    expect(g.nx).toBe(10);
    // The diagonal fills only the cells where column equals row.
    expect(g.cells.every(([i, j]) => i === j)).toBe(true);
    expect(densityCaption(g)).toBe(`Rows per bin, from all 1,005 rows, binned when the site was built. The chart leaves out ${g.outside} rows beyond the 0.5th or 99.5th percentile of either field. Another 3 lack a value in one of them. Draw all points to pick the fields.`);
  });

  test('axis labels sit on bin edges, a round number of bins apart, at most 14 of them', () => {
    expect(labelEdges(50, 50, 51)).toEqual([200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600]);
    expect(labelEdges(-40, 10, 22)).toEqual([-40, -20, 0, 20, 40, 60, 80, 100, 120, 140, 160, 180]);
    // 2-wide bins are never labelled every 5 (mid-bin): every 10 instead.
    expect(labelEdges(0, 2, 30)).toEqual([0, 10, 20, 30, 40, 50, 60]);
    expect(labelEdges(0, 0.1, 5)).toEqual([0, 0.1, 0.2, 0.3, 0.4, 0.5]);
    for (const [start, step, n] of [[50, 50, 51], [-40, 10, 22], [0, 2, 30], [-3, 0.2, 31], [100, 5, 60]] as const) {
      const values = labelEdges(start, step, n);
      expect(values.length, `${start} ${step} ${n}`).toBeLessThanOrEqual(DENSITY_MAX_LABELS);
      for (const v of values) {
        expect(Math.abs((v - start) / step - Math.round((v - start) / step)), `${v}`).toBeLessThan(1e-9);
        expect(v).toBeGreaterThanOrEqual(start);
        expect(v).toBeLessThanOrEqual(start + n * step + 1e-9);
      }
    }
  });

  test('the page spec carries its tooltip text, so no expression runs per bin', () => {
    expect([1050, -40, 0.2, 2600, 1234567.5, 0].map(groupDigits)).toEqual(['1,050', '-40', '0.2', '2,600', '1,234,567.5', '0']);
    const d = ds('flights_200k_json');
    const g = densityOf(d, defaultAxes(scatterFields(d)!));
    const spec = densityPageSpec(d, g, 380);
    expect(spec.transform).toBeUndefined();
    expect(spec.mark).toEqual({ type: 'rect', aria: false });
    const values = (spec.data as { values: Record<string, unknown>[] }).values;
    expect(values).toHaveLength(g.cells.length);
    expect(values.find((v) => v.x0 === 1000 && v.y0 === 0)).toMatchObject({ x1: 1050, y1: 10, 'x range': '1,000 – 1,050', 'y range': '0 – 10' });
  });

  test('a value on the top edge of the box lands in the last bin, as in Vega', () => {
    const rows = Array.from({ length: 201 }, (_, i) => ({ a: i / 2, b: 0 }));
    const g = densityGrid(rows, 'a', 'b', { x: 10, y: 10 });
    expect(Math.max(...g.cells.map(([i]) => i))).toBe(g.nx - 1);
  });

  describe('flights_200k_json', () => {
    const d = ds('flights_200k_json');
    const axes = defaultAxes(scatterFields(d)!);
    const g = densityOf(d, axes);

    test('bins every row, and fits the page in under 30 KB', () => {
      expect(g.rows).toBe(200_000);
      expect(g.complete - g.outside).toBe(g.cells.reduce((s, [, , n]) => s + n, 0));
      expect(g.outside).toBeGreaterThan(0);
      expect(g.outside).toBeLessThan(0.03 * g.rows);
      expect(g.nx).toBeLessThanOrEqual(DENSITY_BINS.x);
      expect(g.ny).toBeLessThanOrEqual(DENSITY_BINS.y);
      expect(JSON.stringify(g).length).toBeLessThan(30_000);
    });

    test('the Editor spec bins the public file into the same cells as the page', async () => {
      const loader = vega.loader();
      loader.load = async (uri: string) => readDataUrl(uri);
      const view = new vega.View(vega.parse(compile({ ...densitySpec(d, g, 380), width: 600 } as TopLevelSpec).spec), { renderer: 'none', loader });
      const page = new vega.View(vega.parse(compile({ ...densityPageSpec(d, g, 380), width: 600 } as TopLevelSpec).spec), { renderer: 'none' });
      try {
        await Promise.all([view.runAsync(), page.runAsync()]);
        const cells = (v: vega.View) => {
          type Node = { marktype?: string; role?: string; items?: (Node & { x?: number; y?: number; width?: number; height?: number })[] };
          const out: string[] = [];
          const walk = (n: Node) => {
            for (const it of n.items ?? []) {
              if (n.marktype === 'rect' && n.role === 'mark') out.push([it.x, it.y, it.width, it.height].map((z) => (typeof z === 'number' ? z.toFixed(1) : z)).join(' '));
              walk(it);
            }
          };
          walk((v.scenegraph() as unknown as { root: Node }).root);
          return out.sort();
        };
        const [a, b] = [cells(view), cells(page)];
        expect(a.length).toBe(g.cells.length);
        expect(a).toEqual(b);
      } finally {
        view.finalize();
        page.finalize();
      }
    }, 60_000);
  });
});
