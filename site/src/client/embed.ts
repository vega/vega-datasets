/**
 * Vega, loaded on demand (the first chart a reader touches), and the options every
 * chart embeds with. The page's CSP forbids compiling code and fetching from other
 * origins, so the specs run as published with two documented Vega hooks (lib/vega-data.ts):
 * expressions run through vega-interpreter, CSV and TSV go through readers registered
 * with `vega.formats()`, and a loader fetches the public data URLs from the site's own
 * `data/`. Tooltips take the page's look.
 */
import type { Loader, View } from "vega";
import type { EmbedOptions } from "vega-embed";
import { onceUnlessFailed } from "../lib/once";
import { chartConfig } from "../lib/vega-theme";
import { readers, siteDataUri } from "../lib/vega-data";
import { siteDataBase, siteText } from "./data";
import { chartInk, token } from "./theme";
import { dismissTipsOnTouch } from "./tooltip";

export interface VegaModules {
  View: typeof import("vega").View;
  vegaEmbed: typeof import("vega-embed").default;
  expressionInterpreter: typeof import("vega-interpreter").expressionInterpreter;
  /** A loader for one chart; `onError` hears of each file that failed to load. */
  loader(onError?: (uri: string, err: unknown) => void): Loader;
}

/** The chart code (Vega's modules) didn't load: a dropped connection, say. */
export class ChartCodeError extends Error {
  constructor(cause: unknown) {
    super("Couldn't load the chart code.", { cause });
    this.name = "ChartCodeError";
  }
}

/**
 * Apply changes and remeasure axes in one evaluation: a newly selected field can have
 * wider tick labels. Vega 6 documents prerun, but its View types omit the arguments.
 */
export function runView(view: View, before: () => void): Promise<View> {
  const run = view.runAsync as (encode?: string, prerun?: () => void) => Promise<View>;
  return run.call(view, undefined, () => { before(); view.resize(); });
}

type Modules = [typeof import("vega-embed"), typeof import("vega-interpreter"), typeof import("vega")];

/**
 * Vega, imported once for the page and set up for its CSP; a failed import isn't kept, so
 * the next chart (or a Retry) imports again. Takes the importer so tests can fail it.
 */
export function vegaLoader(importModules: () => Promise<Modules>): () => Promise<VegaModules> {
  return onceUnlessFailed(() => importModules().then(setUp, (err: unknown) => {
    throw new ChartCodeError(err);
  }));
}

export const loadVega = vegaLoader(() => Promise.all([import("vega-embed"), import("vega-interpreter"), import("vega")]));

function setUp([embed, interp, vega]: Modules): VegaModules {
  // vega-loader's `formats` registry is exported by vega but missing from its type declarations.
  const { formats } = vega as unknown as { formats(name: string, reader: unknown): void };
  for (const [name, reader] of Object.entries(readers())) formats(name, reader);
  const local = siteDataBase();
  // The site's own copy of a public data file, fetched once per page (the gapminder page
  // draws two charts from one file); anything else goes through Vega's loader. Vega
  // swallows a failed load (the chart draws with no rows), so the caller hears of it.
  const loader = (onError?: (uri: string, err: unknown) => void): Loader => {
    const l = vega.loader();
    const load = l.load.bind(l);
    l.load = async (uri: string, options?: unknown) => {
      const url = siteDataUri(uri, local);
      try {
        return await (url === uri ? load(uri, options as never) : siteText(url));
      } catch (err) {
        onError?.(uri, err);
        throw err;
      }
    };
    return l;
  };
  return { View: vega.View, vegaEmbed: embed.default, expressionInterpreter: interp.expressionInterpreter, loader };
}

/**
 * Options for a chart drawn with `renderer`. SVG charts follow forced-color changes through
 * site.css; canvas charts bake the colors in, so they are drawn again (see onThemeChange).
 */
export function embedOptions(v: VegaModules, renderer: "svg" | "canvas", actions: EmbedOptions["actions"], onLoadError?: (uri: string, err: unknown) => void): EmbedOptions {
  dismissTipsOnTouch();
  return {
    config: chartConfig(chartInk(), token("--font-sans")) as EmbedOptions["config"],
    renderer,
    ast: true,
    expr: v.expressionInterpreter,
    loader: v.loader(onLoadError),
    tooltip: { theme: "custom" },
    actions,
  };
}

/** vega-embed's actions menu opens from a `<summary>` that holds only an icon: give it a name. */
export function labelActions(host: Element): void {
  host.querySelector(".vega-embed details > summary")?.setAttribute("aria-label", "Chart actions");
}
