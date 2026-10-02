/**
 * The home page's list, live: search, chips, sort and "Show All" over the cards that are
 * already in the page, and the catalog chart (its brush filters the cards too). The
 * filters live in the URL (`?q=…&format=CSV&used=vega&sort=az&all=1`), so a filtered
 * list can be shared and Back from a dataset returns to it.
 */
import { type Catalog, GALLERIES, GALLERY_LABEL, type Gallery } from "../lib/catalog";
import { formatBytes, formatCount } from "../lib/format";
import {
  baseMatches,
  type Brush,
  chartRows,
  type Filters,
  FORMAT_GROUPS,
  type FormatGroup,
  type HomeIndex,
  indexCatalog,
  isFiltered,
  legacyDataset,
  listDatasets,
  NO_FILTERS,
  SORT_LABEL,
  SORT_NOTE,
  type Sort,
  usageCount,
  usageTitle,
} from "../lib/home-model";
import { onceUnlessFailed } from "../lib/once";
import { catalogLayout } from "../lib/catalog-layout";
import type { MountedChart } from "./catalog-chart";
import { $, afterPaint, h, placeInOrder, whenIdle } from "./dom";
import { loadVega } from "./embed";
import { prepareOnIntent } from "./intent";
import { token } from "./theme";

const PHONE = "(max-width: 640px)";
const CARDS = { wide: 9, phone: 4 };

const cards = $(".cards");
const cardFor = new Map([...cards.querySelectorAll<HTMLAnchorElement>("a.card[data-name]")].map((a) => [a.dataset.name!, a]));

// Links from before the site had a page per dataset (#cars) open that dataset's page: on
// arrival, and when the fragment changes later (a link followed, or one typed in). The home
// page's entry is replaced, so Back returns to where the reader was before it.
const names = new Set(cardFor.keys());
function openLegacy(): boolean {
  const name = legacyDataset(location.hash, names);
  if (name) location.replace(cardFor.get(name)!.href);
  return name !== null;
}
openLegacy();

const phone = matchMedia(PHONE);
const search = $<HTMLInputElement>("#home-q");
const sort = $<HTMLSelectElement>("#home-sort");
const status = $(".browse .status");
const empty = $(".cards-empty");
const more = $<HTMLButtonElement>(".browse-foot .more");
const chartHost = $("[data-chart]");
const usageScope = $("[data-usage-scope]");
const formatChips = [...document.querySelectorAll<HTMLButtonElement>(".chip[data-format]")];
const galleryChips = [...document.querySelectorAll<HTMLButtonElement>(".chip[data-gallery]")];

const filters: Filters & { formats: Set<FormatGroup>; galleries: Set<Gallery> } = {
  ...NO_FILTERS,
  formats: new Set(),
  galleries: new Set(),
};
let expanded = false;

// --- The URL holds the filters -----------------------------------------------------------
function readUrl(): void {
  const p = new URLSearchParams(location.search);
  filters.query = p.get("q") ?? "";
  filters.formats = new Set(p.getAll("format").filter((g): g is FormatGroup => (FORMAT_GROUPS as readonly string[]).includes(g)));
  filters.galleries = new Set(p.getAll("used").filter((g): g is Gallery => (GALLERIES as readonly string[]).includes(g)));
  const s = p.get("sort");
  filters.sort = s && Object.hasOwn(SORT_LABEL, s) ? (s as Sort) : "used";
  expanded = p.get("all") === "1";
}

function writeUrl(): void {
  const p = new URLSearchParams();
  if (filters.query.trim()) p.set("q", filters.query.trim());
  for (const g of filters.formats) p.append("format", g);
  for (const g of filters.galleries) p.append("used", g);
  if (filters.sort !== "used") p.set("sort", filters.sort);
  if (expanded) p.set("all", "1");
  const query = p.toString();
  const url = `${location.pathname}${query ? `?${query}` : ""}${location.hash}`;
  if (url !== `${location.pathname}${location.search}${location.hash}`) history.replaceState(history.state, "", url);
}

function syncControls(): void {
  search.value = filters.query;
  sort.value = filters.sort;
  formatChips.forEach((b) => b.setAttribute("aria-pressed", String(filters.formats.has(b.dataset.format as FormatGroup))));
  galleryChips.forEach((b) => b.setAttribute("aria-pressed", String(filters.galleries.has(b.dataset.gallery as Gallery))));
}

// --- The catalog: fetched once, the first time the list or the chart is used ------------
let catalog: Catalog | null = null;
const load = onceUnlessFailed(() => fetch("home-index.json")
    .then((res) => {
      if (!res.ok) throw new Error(`Could not load the dataset index (HTTP ${res.status})`);
      return res.json() as Promise<HomeIndex>;
    })
    .then((index) => (catalog = indexCatalog(index))));

/** A failed background fetch stays quiet; an explicit action always has a way back. */
async function refresh(): Promise<void> {
  try {
    await load();
    update();
    if (isFiltered(filters) || filters.galleries.size) void hydrate();
  } catch {
    status.replaceChildren("Couldn't load filters. ", h("button", {
      class: "link", type: "button", onclick: () => void refresh(),
    }, "Retry"));
  }
}

// --- The list ------------------------------------------------------------------------------
let chart: MountedChart | null = null;
let cardScope: string | null = null;

function updateUsage(c: Catalog): void {
  const selected = GALLERIES.filter((g) => filters.galleries.has(g));
  chart?.setGalleries(selected);
  const key = selected.join("|");
  if (cardScope === key) return;
  cardScope = key;
  usageScope.textContent = `${usageTitle(filters.galleries)}${selected.length && selected.length < GALLERIES.length ? "" : " across all three libraries"}`;
  const max = Math.max(...c.datasets.map((d) => usageCount(c, d, filters.galleries)), 1);
  for (const d of c.datasets) {
    const card = cardFor.get(d.name)!;
    const n = usageCount(c, d, filters.galleries);
    const usage = c.usage(d);
    card.querySelector("[data-usage-count]")!.textContent = formatCount(n);
    card.querySelector(".card-ex")!.textContent = n === 1 ? " example" : " examples";
    card.querySelectorAll<HTMLElement>("[data-usage-gallery]").forEach((bar) => {
      const g = bar.dataset.usageGallery as Gallery;
      bar.hidden = selected.length > 0 && !filters.galleries.has(g);
      bar.style.width = `${100 * usage[g] / max}%`;
    });
    const detail = GALLERIES.filter((g) => usage[g] && (!selected.length || filters.galleries.has(g)))
      .map((g) => `${GALLERY_LABEL[g]} ${usage[g]}`).join(", ");
    card.querySelector("[data-usage-detail]")!.textContent = detail ? ` (${detail})` : "";
  }
}

function update(): void {
  if (!catalog) return;
  const c = catalog;
  updateUsage(c);
  const list = listDatasets(c, filters);
  chart?.setMatches(isFiltered({ ...filters, brush: null }) ? baseMatches(c, filters).map((d) => d.name) : null);
  const limit = phone.matches ? CARDS.phone : CARDS.wide;
  const shown = expanded ? list : list.slice(0, limit);
  status.replaceChildren();
  if (isFiltered(filters)) {
    status.append(
      `${formatCount(list.length)} of ${formatCount(c.datasets.length)}`,
      filters.brush ? "  ·  filtered by chart" : "",
    );
  } else {
    status.append(SORT_NOTE[filters.sort]);
  }
  if (isFiltered(filters) || filters.galleries.size) {
    status.append("  ·  ", h("button", { class: "link", type: "button", onclick: clearAll }, "Clear"));
  }
  // The cards are the page's own: reorder them and hide the rest (the stylesheet's
  // "first nine" rule steps aside once the script manages the list).
  // Only cards out of place move, so a focused card that stays in order keeps focus; one that
  // has to move, and stays shown, gets it back.
  const visible = new Set(shown.map((d) => d.name));
  const focused = document.activeElement instanceof HTMLElement && cards.contains(document.activeElement) ? document.activeElement : null;
  placeInOrder(cards, list.map((d) => cardFor.get(d.name)!));
  for (const [name, card] of cardFor) card.hidden = !visible.has(name);
  if (focused && document.activeElement !== focused && !focused.closest("[hidden]")) focused.focus({ preventScroll: true });
  cards.dataset.managed = "";
  empty.hidden = list.length > 0;
  more.hidden = shown.length === list.length;
  more.textContent = `Show All ${formatCount(list.length)} Datasets`;
  writeUrl();
}

/** A filter changed: show the first cards of the new list. */
function refilter(): void {
  expanded = false;
  void refresh();
}

function clearAll(): void {
  const hadBrush = filters.brush !== null;
  Object.assign(filters, { ...NO_FILTERS, formats: new Set(), galleries: new Set() });
  syncControls();
  if (hadBrush) chart?.clearBrush();
  refilter();
}

search.addEventListener("input", () => {
  filters.query = search.value;
  refilter();
});
sort.addEventListener("change", () => {
  filters.sort = sort.value as Sort;
  void refresh();
});
const toggle = <T>(set: Set<T>, value: T, button: HTMLButtonElement) => {
  const on = button.getAttribute("aria-pressed") !== "true";
  button.setAttribute("aria-pressed", String(on));
  if (on) set.add(value);
  else set.delete(value);
};
formatChips.forEach((b) => b.addEventListener("click", () => {
  toggle(filters.formats, b.dataset.format as FormatGroup, b);
  refilter();
}));
galleryChips.forEach((b) => b.addEventListener("click", () => {
  // The y values change meaning. Vega's clear event stream resets the visible brush too.
  filters.brush = null;
  toggle(filters.galleries, b.dataset.gallery as Gallery, b);
  // Counting a different gallery keeps the reader's Show All choice.
  void refresh();
}));
more.addEventListener("click", () => {
  expanded = true;
  if (catalog) update();
  else {
    // Nothing is filtered yet: every card is already in order in the page.
    cards.dataset.expanded = "";
    more.hidden = true;
    writeUrl();
  }
});

// --- The chart -----------------------------------------------------------------------------
let hydrating: Promise<void> | null = null;
let chartCodeFailed = false;
// Fetch the controller and its runtime together, rather than waiting for one script
// before discovering the next. Preparing code never replaces a linked static point.
const prepareChart = onceUnlessFailed(async () => {
  const [controller] = await Promise.all([import("./catalog-chart"), loadVega()]);
  return controller;
});
prepareOnIntent($(".filters"), chartHost, () => prepareChart());
function chartError(): void {
  hydrating = null;
  chartHost.querySelector(".load-error")?.remove();
  const retry = h("button", { class: "btn", type: "button" }, "Retry chart");
  retry.addEventListener("click", () => {
    // Browsers can cache a failed module import until the document is reloaded.
    if (chartCodeFailed && navigator.onLine) location.reload();
    else void hydrate();
  });
  chartHost.append(h("p", { class: "muted load-error", role: "status" }, "The live chart couldn't load. ", retry));
}
function hydrate(): Promise<void> {
  return (hydrating ??= (async () => {
    chartHost.querySelector(".load-error")?.remove();
    if (chart) {
      await chart.redraw();
      update();
      return;
    }
    const [c, { mountCatalogChart }] = await Promise.all([load(), prepareChart().catch((err) => {
      chartCodeFailed = true;
      throw err;
    })]);
    const onBrush = (b: Brush | null) => {
      // Every redraw reports "no brush"; only a real change refilters.
      if (JSON.stringify(b) === JSON.stringify(filters.brush)) return;
      filters.brush = b;
      expanded = false;
      update();
    };
    const options = () => ({
      brush: !phone.matches,
      height: phone.matches ? 214 : 240,
      layout: catalogLayout(chartHost.getBoundingClientRect().width),
      labels: catalogLayout(chartHost.getBoundingClientRect().width).labels,
      galleries: GALLERIES.filter((g) => filters.galleries.has(g)),
      matched: isFiltered({ ...filters, brush: null }) ? baseMatches(c, filters).map((d) => d.name) : null,
      monoFont: token("--font-mono"),
    });
    // Prepared modules can resolve immediately. Paint the selected filter before Vega
    // compiles and draws, rather than putting all of that work into the input event.
    await afterPaint();
    chart = await mountCatalogChart(chartHost, chartRows(c, formatBytes), options, onBrush, chartError);
    update();
  })().catch((err: unknown) => {
    // Loading Vega itself can also fail after the small chart controller is available.
    chartCodeFailed ||= err instanceof Error && err.name === "ChartCodeError";
    chartError();
    hydrating = null;
  }));
}
// A phone's first tap uses the static SVG's native link. Replacing it between
// pointerdown and click loses the tap; filtering can safely load the live chart.
chartHost.addEventListener("pointerenter", (event) => {
  if (event.pointerType === "mouse") void hydrate();
}, { passive: true });
chartHost.addEventListener("focusin", (event) => {
  if (event.target instanceof Element && event.target.matches(":focus-visible")) void hydrate();
});

phone.addEventListener("change", () => {
  update();
});

// --- Links into the page ------------------------------------------------------------------
// "Browse Datasets" jumps to the list; the search box takes focus.
document.querySelectorAll<HTMLAnchorElement>("[data-browse]").forEach((link) => {
  link.addEventListener("click", (event) => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    setTimeout(() => search.focus({ preventScroll: true }));
  });
});
// Reveal before the browser follows an in-page link, including a repeated link to
// the current hash after its item was closed. Keep native URL/history navigation.
const openTarget = (hash = location.hash, scroll = false) => {
  let id: string;
  try { id = decodeURIComponent(hash.slice(1)); } catch { return; }
  const target = id ? document.getElementById(id) : null;
  if (target instanceof HTMLDetailsElement && target.classList.contains("about-item")) {
    target.classList.add("about-reveal");
    target.open = true;
    // Resolve the natural height with transitions disabled before anchor scrolling.
    target.getBoundingClientRect();
    target.classList.remove("about-reveal");
    target.querySelector("summary")?.focus({ preventScroll: true });
    if (scroll) target.scrollIntoView({ block: "start", behavior: "instant" });
  }
};
document.querySelectorAll<HTMLAnchorElement>("[data-open-details]").forEach((link) => {
  link.addEventListener("click", (event) => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    openTarget(link.hash);
  });
});
window.addEventListener("hashchange", () => {
  if (!openLegacy()) openTarget(location.hash, true);
});
openTarget(location.hash, true);

// Filters from the URL (a shared link, or Back from a dataset): apply them straight away.
readUrl();
syncControls();
if (isFiltered(filters) || filters.galleries.size || filters.sort !== "used" || expanded) void refresh();
else whenIdle(() => void load().catch(() => {}));
