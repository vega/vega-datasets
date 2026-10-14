import { mkdtempSync, mkdirSync, writeFileSync, symlinkSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { once } from 'node:events';
import { afterAll, beforeAll, expect, test } from 'vitest';
import { createPreviewServer } from '../scripts/serve.mjs';
import { publicFile } from '../scripts/public-files.mjs';

const fixture = mkdtempSync(path.join(tmpdir(), 'vega-preview-'));
const repo = path.join(fixture, 'repo');
const dist = path.join(repo, 'site/dist');
const server = createPreviewServer(repo);
let base: string;
function file(name: string, content = name) {
  const target = path.join(fixture, name);
  mkdirSync(path.dirname(target), { recursive: true });
  writeFileSync(target, content);
}
beforeAll(async () => {
  file('repo/site/dist/index.html', 'Public home');
  file('repo/site/dist/404.html', 'Public missing page');
  file('repo/site/dist/datasets/cars/index.html', 'Cars page');
  file('repo/site/dist/assets/main.js', '/* public script */');
  file('repo/data/cars.json', '[1,2,3]');
  file('repo/datapackage.json', '{"resources":[]}');
  file('repo/private.txt', 'fixture private marker');
  file('repo/.git', 'fixture internal marker');
  file('repo/site/dist/.hidden', 'fixture hidden marker');
  file('outside/index.html', 'fixture outside marker');
  file('outside/cars.json', 'fixture outside marker');
  // Directory junctions work on Windows without administrator symlink privileges.
  symlinkSync(path.join(fixture, 'outside'), path.join(dist, 'escape'), 'junction');
  symlinkSync(path.join(fixture, 'outside'), path.join(repo, 'data/escape'), 'junction');
  symlinkSync(path.join(repo, 'site'), path.join(repo, 'alias'), 'junction');
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const address = server.address();
  if (!address || typeof address === 'string') throw new Error('Expected TCP listener');
  base = `http://127.0.0.1:${address.port}/vega-datasets/`;
});
afterAll(async () => {
  await new Promise<void>((resolve, reject) => server.close((err) => err ? reject(err) : resolve()));
  // Delete only this test's verified, absolute temporary fixture.
  const checked = path.resolve(fixture);
  if (path.dirname(checked) !== path.resolve(tmpdir()) || !path.basename(checked).startsWith('vega-preview-')) throw new Error('Unsafe fixture cleanup');
  rmSync(checked, { recursive: true, force: true });
});

test.each(['', 'datasets/cars/', 'assets/main.js', 'data/cars.json', 'datapackage.json'])('serves intended public resource %s', async (url) => {
  expect((await fetch(base + url)).status).toBe(200);
});
test.each(['private.txt', '.git', 'site/scripts/serve.mjs', '.hidden', '%2ehidden', 'data/%2e%2e%2fprivate.txt', 'data/%2e%2e%5cprivate.txt', 'escape/', 'escape/index.html', 'data/escape/cars.json'])('does not expose %s', async (url) => {
  const response = await fetch(base + url);
  expect(response.status).toBe(404);
  expect(await response.text()).toBe('Public missing page');
});
test('redirects directories and supports HEAD without a body', async () => {
  const redirect = await fetch(base + 'datasets/cars', { redirect: 'manual' });
  expect(redirect.status).toBe(301);
  expect(redirect.headers.get('location')).toBe('/vega-datasets/datasets/cars/');
  const head = await fetch(base + 'data/cars.json', { method: 'HEAD' });
  expect(head.status).toBe(200);
  expect(head.headers.get('content-type')).toContain('application/json');
  expect(await head.text()).toBe('');
});
test('handles malformed paths, unsupported methods and absent error pages', async () => {
  expect((await fetch(base + '%E0%A4%A')).status).toBe(400);
  expect((await fetch(base, { method: 'POST' })).status).toBe(405);
  rmSync(path.join(dist, '404.html'));
  expect((await fetch(base + 'missing')).status).toBe(404);
});
test('canonical containment checks final indexes and rejects alternate root-document targets', () => {
  expect(publicFile(dist, 'escape/index.html')).toBeNull();
  expect(publicFile(repo, 'site/dist/escape/index.html', false)).toBeNull();
  expect(publicFile(repo, 'alias/dist/index.html')).not.toBeNull();
  expect(publicFile(repo, 'alias/dist/index.html', false)).toBeNull();
  expect(publicFile(dist, '../private.txt')).toBeNull();
  expect(publicFile(dist, path.join(fixture, 'outside/index.html'))).toBeNull();
});
