// Preview the built Field Guide and its public datasets on loopback. This serves
// explicit public roots, not the checkout or Jekyll's separately rendered pages.
// Text is gzipped, directories redirect, and missing pages use the site's 404 page.
// Usage: npm run site:serve [-- --port 8000]
import { createReadStream } from 'node:fs';
import { createServer } from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { createGzip } from 'node:zlib';
import { pipeline } from 'node:stream';
import { publicFile } from './public-files.mjs';

const BASE = '/vega-datasets/';
const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const DOCUMENTS = new Set(['datapackage.json', 'datapackage.md', 'README.md', 'CONTRIBUTING.md', 'CHANGELOG.md', 'sources.md', 'LICENSE']);

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.map': 'application/json; charset=utf-8',
  '.xml': 'application/xml; charset=utf-8',
  '.csv': 'text/csv; charset=utf-8',
  '.tsv': 'text/tab-separated-values; charset=utf-8',
  '.md': 'text/markdown; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.webp': 'image/webp',
  '.woff2': 'font/woff2',
};

/** The file for a request path, or a redirect for a directory without its slash. */
function resolve(repoRoot, pathname) {
  const dist = path.join(repoRoot, 'site', 'dist');
  const rel = pathname.slice(BASE.length);
  const file = publicFile(dist, rel)
    ?? (rel.startsWith('data/') ? publicFile(path.join(repoRoot, 'data'), rel.slice(5)) : null)
    ?? (DOCUMENTS.has(rel) ? publicFile(repoRoot, rel, false) : null);
  if (file) return { file };
  const index = publicFile(dist, `${rel.replace(/\/$/, '')}${rel ? '/' : ''}index.html`);
  if (index) {
    return pathname.endsWith('/') ? { file: index } : { redirect: `${pathname.split('/').map(encodeURIComponent).join('/')}/` };
  }
  return null;
}

function send(req, res, status, file) {
  const type = TYPES[path.extname(file)] ?? 'application/octet-stream';
  const gzip = /\bgzip\b/.test(req.headers['accept-encoding'] ?? '') && /text|json|javascript|xml|svg/.test(type);
  res.writeHead(status, { 'Content-Type': type, 'Cache-Control': 'no-cache', 'X-Content-Type-Options': 'nosniff', Vary: 'Accept-Encoding', ...(gzip ? { 'Content-Encoding': 'gzip' } : {}) });
  if (req.method === 'HEAD') { res.end(); return; }
  const stream = createReadStream(file);
  // A disappeared file or disconnected reader must not crash the preview process.
  if (gzip) pipeline(stream, createGzip(), res, () => {});
  else pipeline(stream, res, () => {});
}

export function createPreviewServer(repoRoot = repo) {
  return createServer((req, res) => {
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      res.writeHead(405, { Allow: 'GET, HEAD' }).end();
      return;
    }
    let pathname;
    try {
      pathname = decodeURIComponent(new URL(req.url ?? '/', 'http://localhost').pathname);
    } catch {
      res.writeHead(400).end('Bad request');
      return;
    }
    if (!pathname.startsWith(BASE)) {
      // The site lives under /vega-datasets/; the host's root (robots.txt and the rest) isn't ours.
      if (pathname === '/' || pathname === BASE.slice(0, -1)) res.writeHead(302, { Location: BASE }).end();
      else res.writeHead(404).end('Not found');
      return;
    }
    const found = resolve(repoRoot, pathname);
    if (found?.redirect) res.writeHead(301, { Location: found.redirect }).end();
    else if (found?.file) send(req, res, 200, found.file);
    else {
      const fallback = publicFile(path.join(repoRoot, 'site', 'dist'), '404.html');
      if (fallback) send(req, res, 404, fallback);
      else res.writeHead(404).end('Not found');
    }
  });
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const { values } = parseArgs({ options: { port: { type: 'string', default: '8000' } } });
  createPreviewServer().listen(Number(values.port), '127.0.0.1', () => {
    console.log(`Field Guide at http://127.0.0.1:${values.port}${BASE}`);
  });
}
