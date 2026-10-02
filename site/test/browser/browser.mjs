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
