/** Pictures of the heavy maps' starter charts (prerender/map-preview.ts), one per map. */
import type { GetStaticPaths } from "astro";
import { catalog } from "../../prerender/catalog";
import { mapPreview } from "../../prerender/map-preview";
import { hasMapPreview } from "../../lib/large-data";

export const getStaticPaths = (() => catalog.datasets.filter(hasMapPreview).map((d) => ({ params: { name: d.name }, props: { d } }))) satisfies GetStaticPaths;

export async function GET({ props }: { props: { d: import("../../lib/catalog").Dataset } }): Promise<Response> {
  const { webp } = await mapPreview(props.d);
  return new Response(new Uint8Array(webp), { headers: { "Content-Type": "image/webp" } });
}
