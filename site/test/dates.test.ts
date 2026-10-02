// Dates in the fields table read the same for every viewer: the catalog's timezone-less
// date-times are the files' own values, so they must not shift with the viewer's timezone
// (JavaScript reads them as local time: a day early in Tokyo).
import { afterAll, expect, test } from 'vitest';
import { parseDate } from '../src/lib/format';
import { binLabels, profileSummary } from '../src/lib/profile';
import { loadCatalog } from './catalog';

const catalog = loadCatalog();
const temporal = catalog.datasets.flatMap((d) => d.fields.filter((f) => f.profile.kind === 'temporal').map((f) => [d.name, f] as const));
const field = (dataset: string, name: string) => catalog.dataset(dataset)!.fields.find((f) => f.name === name)!;
const original = process.env.TZ;
afterAll(() => {
  if (original === undefined) delete process.env.TZ;
  else process.env.TZ = original;
});

const texts = () => temporal.map(([name, f]) => `${name}.${f.name}: ${profileSummary(f)} | ${binLabels(f)?.join(' ; ')}`);

test('date summaries and histogram bins read the same in every timezone', () => {
  expect(temporal.length).toBeGreaterThan(5);
  process.env.TZ = 'UTC';
  expect(new Date(2000, 0, 1).getTimezoneOffset()).toBe(0);
  const utc = texts();
  for (const tz of ['Asia/Tokyo', 'America/Los_Angeles', 'Pacific/Kiritimati', 'Pacific/Pago_Pago']) {
    process.env.TZ = tz;
    // The harness really is in another zone (Node applies TZ when it changes).
    expect(new Date(2000, 0, 1).getTimezoneOffset(), tz).not.toBe(0);
    expect(texts(), tz).toEqual(utc);
  }
});

test('seattle_weather covers 2012 to 2015, even east of UTC', () => {
  process.env.TZ = 'Asia/Tokyo';
  expect(profileSummary(field('seattle_weather', 'date'))).toBe('Jan 1, 2012 – Dec 31, 2015');
});

test('timezone-less date-times are read as UTC; explicit zones are kept', () => {
  process.env.TZ = 'Asia/Tokyo';
  expect(parseDate('2012-01-01T00:00:00').toISOString()).toBe('2012-01-01T00:00:00.000Z');
  expect(parseDate('2012-01-01T00:00:00Z').toISOString()).toBe('2012-01-01T00:00:00.000Z');
  expect(parseDate('2000-01-01T08:00:00+00:00').toISOString()).toBe('2000-01-01T08:00:00.000Z');
  expect(parseDate('2012-01-01').toISOString()).toBe('2012-01-01T00:00:00.000Z');
});

test("a date field's bins read as dates, without clock times", () => {
  const labels = binLabels(field('seattle_weather', 'date'))!;
  expect(labels).toHaveLength(24);
  expect(labels[0]).toMatch(/^Jan 1, 2012 – [A-Z][a-z]{2} \d{1,2}, 2012$/);
  expect(labels.some((l) => /AM|PM/.test(l))).toBe(false);
});
