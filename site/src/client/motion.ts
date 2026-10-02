/**
 * "In Motion" on the gapminder page (components/MotionSection.astro, the only page that
 * loads this script): plays the eased animation from lib/motion.ts. It starts when the
 * section comes near the screen, plays only while the chart is in view, and never
 * plays by itself for readers who prefer reduced motion.
 */
import type { Result } from "vega-embed";
import { type Colors, type Country, FIRST_YEAR, type GapminderRow, gapminderSpec, SEGMENT_MS, STEP_YEARS, toCountries, vegaEditorUrl } from "../lib/motion";
import { siteDataBase, siteText } from "./data";
import { $, h } from "./dom";
import { embedOptions, loadVega } from "./embed";
import { chartInk, onThemeChange, reducedMotion, token } from "./theme";

/** The points keep their data colors; the rest follows the theme, or the forced colors. */
function colors(): Colors {
  const ink = chartInk();
  return {
    neutral: token("--motion-neutral"),
    accent: token("--chart-1"),
    focus: ink.strong,
    surface: ink.surface,
    watermark: ink.forced ? ink.grid : token("--motion-watermark"),
    ...(ink.forced ? { watermarkOpacity: 0.4 } : {}),
    trail: ink.ink,
    label: ink.ink,
  };
}

/** The same fetch as Explore's scatter plot of gapminder.json, so the page loads the file once. */
async function loadCountries(): Promise<Country[]> {
  return toCountries(JSON.parse(await siteText(`${siteDataBase()}gapminder.json`)) as GapminderRow[]);
}

async function start(section: HTMLElement): Promise<void> {
  const chartHost = $(".motion-chart", section);
  const play = $<HTMLButtonElement>(".motion-play", section);
  const slider = $<HTMLInputElement>("#motion-year", section);
  const yearOut = $("output.motion-year", section);
  const regions = [...section.querySelectorAll<HTMLButtonElement>(".motion-regions [data-region]")];
  const followNote = $(".motion-note", section);
  const editor = $<HTMLAnchorElement>("[data-editor]", section);
  const status = $(".motion-status", section);
  status.textContent = "Loading…";

  let values: Country[];
  let v: Awaited<ReturnType<typeof loadVega>>;
  try {
    [values, v] = await Promise.all([loadCountries(), loadVega()]);
  } catch (err) {
    status.textContent = `The chart didn't load: ${err instanceof Error ? err.message : String(err)}`;
    return;
  }
  status.textContent = "";
  const state = { clock: 0, playing: false, follow: "China", hl: null as string | null, userPaused: reducedMotion() };
  let result: Result | undefined;

  const setPlaying = (p: boolean) => {
    state.playing = p;
    play.textContent = p ? "Pause" : "Play";
    play.setAttribute("aria-pressed", String(p));
    void result?.view.signal("playing", p).runAsync();
  };
  const describeFollow = () => {
    followNote.replaceChildren(h("b", null, state.follow), " is highlighted with its full path. Select any bubble to follow that country instead.");
  };
  const updateEditor = () => {
    editor.href = vegaEditorUrl(gapminderSpec(values, 640, 400, colors(), { clock: 0, playing: true, follow: state.follow, hl: state.hl }));
  };

  // Size to the content box: clientWidth includes padding, and sizing to it would grow the chart on every resize.
  const contentWidth = () => {
    const cs = getComputedStyle(chartHost);
    return Math.floor(chartHost.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight));
  };

  // Renders run one at a time, so a resize and a theme change can't both embed a view.
  let queue: Promise<void> = Promise.resolve();
  const draw = async () => {
    if (result) {
      state.clock = result.view.signal("clock") as number;
      result.finalize();
    }
    const width = Math.max(280, contentWidth());
    const height = Math.round(Math.min(520, Math.max(300, width * 0.6)));
    result = await v.vegaEmbed(chartHost, gapminderSpec(values, width, height, colors(), state) as never, embedOptions(v, "svg", false));
    result.view.addSignalListener("t", (_n, t: number) => {
      slider.value = String(t);
      yearOut.textContent = String(FIRST_YEAR + STEP_YEARS * Math.round(t));
    });
    result.view.addSignalListener("follow", (_n, f: string) => {
      state.follow = f;
      describeFollow();
      updateEditor();
    });
  };
  const render = () => (queue = queue.then(draw).catch((err: unknown) => {
    status.textContent = `The chart didn't render: ${err instanceof Error ? err.message : String(err)}`;
  }));

  // Region chips: emphasis instead of six colors (a scatter plot can't keep six hues apart for every reader).
  for (const b of regions) {
    b.addEventListener("click", () => {
      state.hl = b.dataset.region || null;
      regions.forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      void result?.view.signal("hl", state.hl).runAsync();
      updateEditor();
    });
  }
  play.addEventListener("click", () => {
    state.userPaused = state.playing;
    setPlaying(!state.playing);
  });
  slider.addEventListener("input", () => {
    state.userPaused = true;
    setPlaying(false);
    const t = Number(slider.value);
    void result?.view.signal("clock", t * SEGMENT_MS).runAsync();
    yearOut.textContent = String(FIRST_YEAR + STEP_YEARS * Math.round(t));
  });

  // Play only while the chart is on screen, never automatically for reduced-motion viewers.
  const io = new IntersectionObserver(([entry]) => {
    if (!entry) return;
    if (entry.isIntersecting && entry.intersectionRatio >= 0.4 && !state.userPaused) setPlaying(true);
    else if (!entry.isIntersecting && state.playing) setPlaying(false);
  }, { threshold: [0, 0.4] });

  let resizeTimer = 0;
  let lastWidth = contentWidth();
  const ro = new ResizeObserver(() => {
    const w = contentWidth();
    if (Math.abs(w - lastWidth) < 8) return;
    lastWidth = w;
    clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(() => void render(), 150);
  });

  describeFollow();
  updateEditor();
  await render();
  io.observe(chartHost);
  ro.observe(chartHost);
  // Redraw when forced colors change so the chart follows the system palette.
  onThemeChange(() => void render());
}

const section = document.querySelector<HTMLElement>("[data-motion]");
if (section) {
  const near = new IntersectionObserver((entries) => {
    if (!entries.some((e) => e.isIntersecting)) return;
    near.disconnect();
    void start(section);
  }, { rootMargin: "400px 0px" });
  near.observe(section);
}
