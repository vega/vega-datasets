import { fileURLToPath } from 'node:url';
import { getViteConfig } from 'astro/config';

// `unit` runs offline against site/generated/catalog.json and the built pages in site/dist
// (build both first with `npm run site:build`); Astro's Vite setup lets it render components.
// `links` checks every outbound link the site generates, so it needs the network.
const root = fileURLToPath(new URL('.', import.meta.url));

export default getViteConfig(
  {
    root,
    test: {
      projects: [
        { extends: true, test: { name: 'unit', include: ['test/*.test.ts'] } },
        { extends: true, test: { name: 'links', include: ['test/network/*.test.ts'], testTimeout: 600_000 } },
      ],
    },
  },
  { root },
);
