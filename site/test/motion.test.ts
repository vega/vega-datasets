// The "In Motion" gapminder chart: eased interpolation between five-year keyframes,
// checked in a headless Vega view with the CSP-safe expression interpreter the page uses.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import LZString from 'lz-string';
import * as vega from 'vega';
import { expressionInterpreter } from 'vega-interpreter';
import { afterAll, beforeAll, describe, expect, test } from 'vitest';
import {
  FIRST_YEAR,
  type GapminderRow,
  LABELED,
  SEGMENT_MS,
  STEP_YEARS,
  gapminderSpec,
  toCountries,
  vegaEditorUrl,
} from '../src/lib/motion';
import { REPO } from './catalog';

const rows = JSON.parse(readFileSync(path.join(REPO, 'data', 'gapminder.json'), 'utf8')) as GapminderRow[];
const countries = toCountries(rows);
const colors = { neutral: '#aaaaaa', accent: '#2e5c49', focus: '#111111', surface: '#ffffff', watermark: '#eeeeee', trail: '#444444', label: '#444444' };
const spec = gapminderSpec(countries, 640, 400, colors, { clock: 0, playing: false, follow: 'China', hl: null });
const china = countries.find((c) => c.country === 'China')!;

/** Vega's easeCubicInOut, written out so the test doesn't trust the thing it checks. */
const easeCubicInOut = (t: number) => (t < 0.5 ? 4 * t ** 3 : 1 - (-2 * t + 2) ** 3 / 2);

describe('gapminder keyframes', () => {
  test('every country has one keyframe per five years, 1955 to 2005', () => {
    const years = [...new Set(rows.map((r) => r.year))].sort();
    expect(years).toEqual(Array.from({ length: 11 }, (_, i) => FIRST_YEAR + STEP_YEARS * i));
    for (const c of countries) {
      expect([c.fert.length, c.life.length, c.pop.length], c.country).toEqual([11, 11, 11]);
    }
  });

  test('every country is in a named region', () => {
    expect(countries.filter((c) => c.region === 'Other').map((c) => c.country)).toEqual([]);
  });
});

describe('gapminder motion spec', () => {
  let view: vega.View;
  beforeAll(async () => {
    view = new vega.View(vega.parse(spec as vega.Spec, undefined, { ast: true }), {
      renderer: 'none',
      expr: expressionInterpreter,
    } as vega.ViewOptions);
    await view.runAsync();
  });
  afterAll(() => view.finalize());

  async function at(t: number) {
    view.signal('clock', t * SEGMENT_MS);
    await view.runAsync();
    const c = view.data('countries').find((d: { country: string }) => d.country === 'China');
    return { year: view.signal('year') as number, x: c.x as number, y: c.y as number, p: c.p as number };
  }

  test.each([0, 1, 2, 10])('lands exactly on keyframe %i', async (k) => {
    const s = await at(k);
    expect(s.year).toBe(FIRST_YEAR + STEP_YEARS * k);
    expect(s.x).toBeCloseTo(china.fert[k]!, 9);
    expect(s.y).toBeCloseTo(china.life[k]!, 9);
    expect(s.p).toBeCloseTo(china.pop[k]!, 0);
  });

  test.each([0.25, 0.5, 0.75, 3.4])('eases between keyframes at t=%f', async (t) => {
    const k = Math.floor(t);
    const f = easeCubicInOut(t - k);
    const s = await at(t);
    expect(s.y).toBeCloseTo(china.life[k]! + f * (china.life[k + 1]! - china.life[k]!), 9);
    expect(s.x).toBeCloseTo(china.fert[k]! + f * (china.fert[k + 1]! - china.fert[k]!), 9);
    expect(s.year).toBe(FIRST_YEAR + STEP_YEARS * Math.round(t));
  });

  test('clamps past the last keyframe', async () => {
    const s = await at(12);
    expect(s.year).toBe(2005);
    expect(s.y).toBeCloseTo(china.life[10]!, 9);
  });

  test('draws the followed country\'s full path and the labeled countries', async () => {
    await at(0);
    expect(view.data('trail')).toHaveLength(11);
    expect(view.data('labeled').map((d: { country: string }) => d.country).sort()).toEqual([...LABELED].sort());
  });

  test('renders one bubble per country', async () => {
    const svg = await view.toSVG();
    const bubbles = svg.match(/<path[^>]*class="[^"]*"[^>]*|<path /g) ?? [];
    expect(bubbles.length).toBeGreaterThanOrEqual(countries.length);
  });
});

test('the Vega Editor link decodes to the same spec and renders with the default parser', async () => {
  const url = vegaEditorUrl(spec);
  const decoded = JSON.parse(LZString.decompressFromEncodedURIComponent(url.split('#/url/vega/')[1]!)!);
  expect(decoded).toEqual(JSON.parse(JSON.stringify(spec)));
  const view = new vega.View(vega.parse(decoded), { renderer: 'none' });
  try {
    await view.runAsync();
    expect(view.data('countries')).toHaveLength(countries.length);
  } finally {
    view.finalize();
  }
});
