/**
 * The site's own copies of the data files (connect-src 'self'), fetched at most once per
 * page: Explore's Vega loader (embed.ts) and In Motion (motion.ts) share the text.
 */

/** The absolute URL of the site's `data/` folder, ending in a slash. */
export function siteDataBase(): string {
  return new URL(`${import.meta.env.BASE_URL}data/`, location.href).href;
}

const texts = new Map<string, Promise<string>>();

/** The text of a same-origin data file; a failed fetch is forgotten, so a redraw tries again. */
export function siteText(url: string): Promise<string> {
  let p = texts.get(url);
  if (!p) {
    p = fetch(url).then((res) => {
      if (!res.ok) throw new Error(`Could not load ${url.split("/").pop()} (HTTP ${res.status})`);
      return res.text();
    });
    p.catch(() => texts.delete(url));
    texts.set(url, p);
  }
  return p;
}
