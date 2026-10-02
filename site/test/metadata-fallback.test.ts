// A dataset without the new metadata renders exactly as before the site read it: the
// snapshot of the fixture's charts without its metadata was written by the code at 56ba567
// (before any of it), so a change here means an undescribed dataset's chart moved.
// The fixture is steered through each starter rule by the fields it keeps.
import { describe, expect, test } from 'vitest';
import { defaultAxes, exploreModes, scatterFields, scatterSpec, starterChart } from '../src/lib/explore-model';
import { starterSpec } from '../src/lib/starter';
import { described, only, strip } from './fixtures';

const VARIANTS: [string, string[] | null][] = [
  ['time series colored by a series', null],
  ['scatter plot colored by a category', ['hp', 'mpg', 'grade', 'side']],
  ['bars of a measure by category', ['grade', 'hp']],
  ['histogram', ['hp']],
  ['category counts', ['grade']],
];

describe.each(VARIANTS)('%s', (_name, fields) => {
  const d = fields ? only(strip(described()), fields) : strip(described());

  test('starter and Explore specs match the code before the metadata', () => {
    const sf = scatterFields(d);
    // As JSON text, so the snapshot holds key order too: the Editor links carry the spec's text.
    const specs = {
      modes: exploreModes(d),
      starter: starterSpec(d),
      chart: starterChart(d),
      scatter: sf ? scatterSpec(d, sf, { ...defaultAxes(sf), zoom: true, height: 380 }) : null,
    };
    expect(JSON.stringify(specs, null, 1)).toMatchSnapshot();
  });
});
