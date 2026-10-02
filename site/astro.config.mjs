// The Field Guide: a static site, one page per dataset, built from catalog.json
// (scripts/build_site_catalog.py). `npm run site:build` runs both steps.
import { createReadStream } from 'node:fs';
import { pipeline } from 'node:stream';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'astro/config';
import { publicFile } from './scripts/public-files.mjs';

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

/** In `astro dev`, serve the repository's data/ at /vega-datasets/data/, as GitHub Pages does. */
function repositoryData() {
  const data = path.join(repo, 'data');
  return {
    name: 'repository-data',
    configureServer(server) {
      // Vite strips the base (/vega-datasets) before middleware runs, so both forms are matched.
      server.middlewares.use((req, res, next) => {
        const match = /^(?:\/vega-datasets)?\/data\/([^?]+)/.exec(req.url ?? '');
        if (!match) return next();
        let file;
        try {
          file = publicFile(data, decodeURIComponent(match[1]));
        } catch {
          res.writeHead(400).end('Bad request');
          return;
        }
        if (!file) return next();
        pipeline(createReadStream(file), res, () => {});
      });
    },
  };
}

export default defineConfig({
  site: 'https://vega.github.io',
  base: '/vega-datasets',
  trailingSlash: 'always',
  outDir: './dist',
  build: {
    format: 'directory',
    assets: 'assets',
    // The page's CSP allows only same-origin scripts, so nothing is inlined.
    inlineStylesheets: 'never',
  },
  compressHTML: true,
  devToolbar: { enabled: false },
  vite: {
    plugins: [repositoryData()],
    build: {
      // 0 keeps every script an external file (Astro inlines small ones otherwise).
      assetsInlineLimit: 0,
      chunkSizeWarningLimit: 1200,
    },
  },
});
