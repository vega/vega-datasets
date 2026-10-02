// Browser checks need a built site (`npm run site:build`) and an installed Chrome.
// Install the driver: npm install --no-save --package-lock=false puppeteer-core@25.12.0
// Each check lists its commands; some start and stop their own preview server.
// Optional: CHROME_PATH selects a browser executable. PUPPETEER_CORE points to a
// folder containing node_modules/puppeteer-core if the driver is installed elsewhere.
import { createRequire } from 'node:module';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

/** Use an installed Chrome; browser checks are optional and never download it. */
export async function launchBrowser() {
  const where = process.env.PUPPETEER_CORE;
  const module = where
    ? pathToFileURL(createRequire(path.resolve(where, 'index.js')).resolve('puppeteer-core')).href
    : 'puppeteer-core';
  const puppeteer = (await import(module)).default;
  return puppeteer.launch({
    headless: true,
    ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : { channel: 'chrome' }),
  });
}
