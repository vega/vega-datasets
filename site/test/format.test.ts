// Numbers as the pages print them.
import { expect, test } from 'vitest';
import { formatBytes } from '../src/lib/format';

test('file sizes are in decimal units, as on the catalog chart axis', () => {
  expect(formatBytes(null)).toBe('–');
  expect(formatBytes(77)).toBe('77 B');
  expect(formatBytes(999)).toBe('999 B');
  expect(formatBytes(1000)).toBe('1.0 KB');
  expect(formatBytes(8487)).toBe('8.5 KB');
  // cars: the chart puts it at the axis' 100 KB, and its card says so.
  expect(formatBytes(100_492)).toBe('100 KB');
  expect(formatBytes(999_600)).toBe('1.0 MB');
  expect(formatBytes(1_399_981)).toBe('1.4 MB');
  expect(formatBytes(9_863_892)).toBe('9.9 MB');
  expect(formatBytes(13_493_022)).toBe('13 MB');
  expect(formatBytes(9_960)).toBe('10 KB');
});
