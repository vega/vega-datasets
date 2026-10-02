/**
 * A heavy map's starter chart (us_10m's counties, zipcodes' 42,000 points), drawn when
 * the site is built: headless Vega draws it to SVG from the local file, and sharp turns
 * that into a small WebP, so the page shows the map without drawing thousands of marks.
 */
import * as vega from "vega";
import { compile, type TopLevelSpec } from "vega-lite";
import sharp from "sharp";
import type { Dataset } from "../lib/catalog";
import { starterSpec } from "../lib/starter";
import { themeConfig } from "../lib/vega-theme";
import { readDataUrl } from "./repo";
import { lightToken } from "./tokens";

export interface MapPreview {
  webp: Buffer;
  width: number;
  height: number;
}

const drawn = new Map<string, Promise<MapPreview>>();

/** The preview for `d`, drawn once per build (the page and the image both ask). */
export function mapPreview(d: Dataset): Promise<MapPreview> {
  let p = drawn.get(d.name);
  if (!p) drawn.set(d.name, (p = draw(d)));
  return p;
}

async function draw(d: Dataset): Promise<MapPreview> {
  const spec = starterSpec(d);
  if (!spec) throw new Error(`${d.name} has no starter chart`);
  // On white, like the gallery thumbnails (an opaque picture is also far smaller than one with alpha).
  const config = { ...themeConfig(lightToken), background: "#ffffff" };
  const { spec: vg } = compile(spec as unknown as TopLevelSpec, { config: config as never });
  const loader = vega.loader();
  loader.load = async (uri: string) => readDataUrl(uri);
  const view = new vega.View(vega.parse(vg), { renderer: "none", loader });
  try {
    await view.runAsync();
    const svg = await view.toSVG();
    const size = svg.match(/<svg [^>]*width="(\d+(?:\.\d+)?)" height="(\d+(?:\.\d+)?)"/);
    const width = Math.round(Number(size?.[1] ?? 600));
    const height = Math.round(Number(size?.[2] ?? 400));
    // About 1.8 times the size, for sharp screens; the page shows it at its own size.
    const webp = await sharp(Buffer.from(svg), { density: 128 }).webp({ quality: 72 }).toBuffer();
    return { webp, width, height };
  } finally {
    view.finalize();
  }
}
