/**
 * Explore, live: the dataset's chart (a scatter plot of two measures, the starter time
 * series, or the starter map), drawn into the section the page already has, with the
 * line naming its Vega-Lite features and the Editor button following the pickers.
 * dataset.ts loads this module when the section comes near the screen.
 *
 * The chart runs the spec the Editor opens, public data URL included (embed.ts adapts
 * Vega to the page's CSP). How and when it draws follows the large-data policy
 * (lib/large-data.ts): long tables open on their density overview (bins from the page,
 * no download) until the reader asks for all points; mid-size tables draw by themselves
 * only on a desktop-class device (lib/device.ts); heavy maps open on a picture.
 */
import type { Dataset } from "../lib/catalog";
import { deviceSignals, isDesktopClass } from "../lib/device";
import { bothValuesNote, chartFeatures, defaultAxes, exploreModes, type Mode, scatterFields, scatterSpec, starterChart } from "../lib/explore-model";
import { allowed, BAND_POLICY, type DensityGrid, densityPageSpec, tableBand } from "../lib/large-data";
import { editorUrl, starterSpec } from "../lib/starter";
import { pointSource } from "../lib/vega-data";
import { $, afterPaint, h, readJson } from "./dom";
import { ChartCodeError, embedOptions, labelActions, loadVega, runView } from "./embed";
import { onThemeChange } from "./theme";

type Spec = Record<string, unknown>;

const PHONE = "(max-width: 640px)";

/** A data file that didn't load (Vega itself only logs it, and draws no rows). */
class LoadError extends Error {
  constructor(readonly file: string) {
    super(`Couldn't load ${file}.`);
  }
}

/** "an origin", "a species". */
function withArticle(word: string): string {
  return `${/^[aeiou]/i.test(word) ? "an" : "a"} ${word}`;
}

export function enhanceExplore(section: HTMLElement, d: Dataset): void {
  const modes = exploreModes(d);
  if (!modes.length) return;
  const phone = matchMedia(PHONE);
  const desktop = isDesktopClass(deviceSignals(window));
  const band = tableBand(d);
  const policy = band ? BAND_POLICY[band] : null;
  const canvas = policy?.renderer === "canvas";
  // Scroll to zoom traps page scrolling on a narrow screen, and redraws every point per wheel step.
  const zoom = () => !phone.matches && (!policy || allowed(policy.zoom, desktop));
  const fields = scatterFields(d);
  const state: { mode: Mode; x: string; y: string } = { mode: modes[0]!, ...(fields ? defaultAxes(fields) : { x: "", y: "" }) };

  const binds = $(".binds", section);
  const host = $(".explore-chart", section);
  const note = $(".chart-caption .hint", section);
  const features = $(".chart-caption .features", section);
  const edit = $<HTMLAnchorElement>("[data-editor]", section);
  const drawButton = host.querySelector<HTMLButtonElement>("button.draw");
  const drawAll = section.querySelector<HTMLButtonElement>("[data-draw-all]");
  // The density overview, while it shows: bins written into the page when it was built.
  let density = section.hasAttribute("data-density") ? readJson<DensityGrid>("density-data") : null;
  // How many rows the scatter plot draws: counted for the default fields when the site was
  // built (so the caption keeps its length), then read from the view after each run.
  let plotted: number | null = note.dataset.plotted ? Number(note.dataset.plotted) : null;

  section.querySelectorAll<HTMLButtonElement>(".seg [data-mode]").forEach((b) => {
    b.addEventListener("click", () => {
      const m = b.dataset.mode as Mode;
      if (state.mode === m) return;
      state.mode = m;
      section.querySelectorAll(".seg [data-mode]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      void render();
    });
  });

  const height = () => (phone.matches ? 300 : 380);
  // The overview's spec per height, built once: a thousand bins, each with its tooltip text.
  const overviews = new Map<number, Spec>();
  const overview = (g: DensityGrid, h: number): Spec => {
    let spec = overviews.get(h);
    if (!spec) overviews.set(h, (spec = densityPageSpec(d, g, h)));
    return spec;
  };
  /** The spec the page draws, exactly as the Editor opens it (the overview's Editor spec bins the public file). */
  const currentSpec = (): Spec => {
    if (density) return overview(density, height());
    if (state.mode === "scatter" && fields) return scatterSpec(d, fields, { x: state.x, y: state.y, zoom: zoom(), height: height() });
    return starterChart(d) ?? starterSpec(d)!;
  };

  const describe = () => {
    // The overview's caption, features and Editor link are in the page as built (they
    // don't change while it shows); working them out again would cost a thousand-bin spec.
    if (density) return;
    const spec = currentSpec();
    edit.href = editorUrl(spec);
    features.textContent = chartFeatures(spec).join(" · ");
    note.hidden = state.mode !== "scatter" || !fields;
    if (state.mode !== "scatter" || !fields) return;
    const color = fields.color ? ` ${phone.matches ? "Tap" : "Click"} the legend to isolate ${withArticle(fields.color.name.toLowerCase())}.` : "";
    const lead = zoom() ? `Pick two fields. Scroll to zoom, drag to pan.${color}` : `Pick two fields.${color}`;
    const count = bothValuesNote(d, plotted);
    note.textContent = count ? `${lead} ${count}` : lead;
  };

  type Drawing = {
    result: import("vega-embed").Result;
    plot: HTMLElement;
    inputs: ChildNode[];
    source: string | null;
    layout: number;
  };
  // Only small, multi-mode tables retain views. Large data keeps its one-view policy.
  const retain = modes.length > 1 && band === "svg";
  const drawings = new Map<Mode, Drawing>();
  let active: Drawing | undefined;
  let layout = 0;
  window.addEventListener("resize", () => { layout++; });
  const forget = () => {
    for (const { result, plot } of drawings.values()) { result.finalize(); plot.remove(); }
    drawings.clear();
    active = undefined;
    binds.replaceChildren();
  };
  const recount = (drawing: Drawing) => {
    if (drawing !== active) return;
    plotted = drawing.source ? (drawing.result.view.data(drawing.source) as unknown[]).length : null;
    describe();
  };
  const show = (drawing: Drawing) => {
    for (const other of drawings.values()) {
      other.plot.hidden = other !== drawing;
      other.plot.querySelectorAll("details[open]").forEach((el) => el.removeAttribute("open"));
    }
    active = drawing;
    drawing.plot.classList.remove("pending");
    binds.replaceChildren(...drawing.inputs);
    binds.hidden = state.mode !== "scatter" || density !== null;
    host.querySelectorAll(".chart-preview, button.draw, .load-error").forEach((el) => el.remove());
    recount(drawing);
  };
  let queue: Promise<void> = Promise.resolve();
  let revision = 0;
  let invalidated = false;
  const draw = async (version: number) => {
    if (version !== revision) return;
    const v = await loadVega();
    if (version !== revision) return;
    if (invalidated) { forget(); invalidated = false; }
    const mode = state.mode;
    const cached = drawings.get(mode);
    if (cached) {
      show(cached);
      // A hidden responsive Vega view may have seen a zero-width container on resize.
      // Refit only when the window changed; ordinary mode switches need no Vega run.
      if (cached.layout !== layout) {
        await runView(cached.result.view, () => { cached.result.view.width(cached.result.view.container()!.clientWidth); });
        cached.layout = layout;
      }
      return;
    }
    // Yield only for a new chart, not for the inexpensive switch to an existing one.
    await afterPaint();
    if (version !== revision) return;
    const spec = currentSpec();
    // Don't keep two large dataflows alive even temporarily while changing modes.
    if (!retain) forget();
    const plot = h("div", { class: "explore-view pending" });
    const inputs = h("div");
    host.append(plot);
    const failed: string[] = [];
    let result: import("vega-embed").Result;
    try {
      result = await v.vegaEmbed(plot, spec as never, {
        ...embedOptions(v, canvas && !density ? "canvas" : "svg", { export: true, source: true, compiled: true, editor: false }, (uri) => failed.push(uri)),
        bind: inputs,
      });
    } catch (err) { plot.remove(); throw err; }
    // How many times the chart has been drawn: once on open, unless asked (the browser check reads it).
    section.dataset.draws = String(Number(section.dataset.draws ?? 0) + 1);
    // Vega draws an empty chart when its file doesn't load: say so instead, and count nothing.
    if (failed.length || version !== revision) {
      result.finalize();
      plot.remove();
      if (failed.length) throw new LoadError(failed[0]!.split("/").pop()!);
      return;
    }
    labelActions(plot);
    // A select narrowed to fit its row clips a long field name: its tooltip gives it in full.
    inputs.querySelectorAll("select").forEach((select) => {
      const name = () => (select.title = select.value);
      name();
      select.addEventListener("change", name);
    });
    const view = result.view;
    const source = mode === "scatter" && !density ? pointSource(result.vgSpec as never) : null;
    const drawing: Drawing = { result, plot, inputs: [...inputs.childNodes], source, layout };
    drawings.set(mode, drawing);
    show(drawing);
    if (source) {
      const follow = (axis: "x" | "y") => (_name: string, value: unknown) => {
        state[axis] = String(value);
        // A zoom on the old fields would hide the new ones: clear it (the scale domains read this store).
        void runView(view, () => {
          if (zoom()) view.change("zoom_store", view.changeset().remove(() => true));
        }).then(() => recount(drawing)).catch(() => void render(true));
      };
      view.addSignalListener("xField", follow("x"));
      view.addSignalListener("yField", follow("y"));
    }
  };
  let requested = false;
  // A Retry after the chart code failed to load is under way.
  let retryingCode = false;
  const render = (invalidate = false) => {
    requested = true;
    invalidated ||= invalidate;
    const version = ++revision;
    host.setAttribute("aria-busy", "true");
    return (queue = queue.then(() => draw(version)).catch((err: unknown) => {
      if (version !== revision) return;
      // Chrome keeps a failed dynamic import in its module map, so importing again fails at
      // once even when the connection is back (other browsers fetch again). When a Retry of
      // the chart code fails while online, reload the page, as Vite advises: a new document
      // fetches every module afresh.
      if (err instanceof ChartCodeError && retryingCode && navigator.onLine) {
        location.reload();
        return;
      }
      retryingCode = false;
      forget();
      plotted = null;
      describe();
      const retry = h("button", { class: "btn", type: "button", "data-retry": "" }, "Retry");
      retry.addEventListener("click", () => {
        retryingCode = err instanceof ChartCodeError;
        void render();
      }, { once: true });
      const message =
        err instanceof LoadError ? `Couldn't load ${err.file}.`
        : err instanceof ChartCodeError ? err.message
        : `The chart didn't load: ${err instanceof Error ? err.message : String(err)}`;
      host.replaceChildren(h("p", { class: "muted load-error", role: "status" }, message, " ", retry));
    }).finally(() => { if (version === revision) host.removeAttribute("aria-busy"); }));
  };

  // Redraw for a new screen size once a chart is asked for (a large file waits for its
  // button): a change during the first draw, while the file is still loading, queues a
  // second draw at the new size. Canvas charts also redraw for a new theme (SVG charts
  // restyle through the stylesheet, except for the overview's data colors).
  const redraw = () => {
    if (requested) void render(true);
  };
  // The density overview's ramp follows the theme (config.range.heatmap), so it redraws too.
  onThemeChange(() => {
    if (canvas || density) redraw();
  });
  phone.addEventListener("change", redraw);
  describe();
  drawAll?.addEventListener("click", () => {
    density = null;
    drawAll.remove();
    void render(true);
  }, { once: true });
  // A mid-size table's button (data-auto-draw="desktop") stands aside on a desktop-class device.
  if (!drawButton || (drawButton.dataset.autoDraw === "desktop" && desktop)) void render();
  else drawButton.addEventListener("click", () => void render(), { once: true });
}
