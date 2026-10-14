/** Every page, for search engines (referenced from each page's head). */
import { catalog } from "../prerender/catalog";
import { datasetUrl, HOME_URL, statusUrl } from "../lib/seo";

export function GET(): Response {
  const urls = [HOME_URL, ...catalog.datasets.map((d) => datasetUrl(d.name)), statusUrl()];
  const body = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.map((u) => `  <url><loc>${u}</loc></url>`).join("\n")}\n</urlset>\n`;
  return new Response(body, { headers: { "Content-Type": "application/xml; charset=utf-8" } });
}
