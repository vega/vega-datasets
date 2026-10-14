/**
 * A dataset page, live: the section links mark the section in view, the examples
 * filter by gallery and expand, Explore draws when it comes near the screen, and the
 * left and right arrow keys step to the neighboring datasets (only while nothing on
 * the page has focus, so they never steal a widget's keys).
 */
import type { Dataset } from "../lib/catalog";
import { formatCount } from "../lib/format";
import { datasetStep } from "../lib/keys";
import { readJson } from "./dom";

const EXAMPLES_SHOWN = 8;

// --- Section links: mark the section in view --------------------------------------------------
const links = [...document.querySelectorAll<HTMLAnchorElement>(".section-nav a.tab[href^='#']")];
const sections = links.map((a) => document.getElementById(a.hash.slice(1))).filter((s): s is HTMLElement => s !== null);
const visible = new Map<string, boolean>();
const spy = new IntersectionObserver((entries) => {
  for (const e of entries) visible.set(e.target.id, e.isIntersecting);
  const current = sections.find((s) => visible.get(s.id)) ?? null;
  for (const a of links) {
    if (current && a.hash === `#${current.id}`) a.setAttribute("aria-current", "true");
    else a.removeAttribute("aria-current");
  }
}, { rootMargin: "-30% 0px -60% 0px" });
sections.forEach((s) => spy.observe(s));

// --- Examples: filter by gallery, show all ----------------------------------------------------
const examples = document.querySelector<HTMLElement>("[data-examples]");
if (examples) {
  const items = [...examples.querySelectorAll<HTMLLIElement>("li.ex")];
  const more = examples.querySelector<HTMLButtonElement>(".more");
  const grid = examples.querySelector<HTMLElement>(".ex-grid");
  let filter = "";
  let expanded = false;
  const draw = () => {
    const list = items.filter((li) => !filter || li.dataset.gallery === filter);
    const shown = new Set(expanded ? list : list.slice(0, EXAMPLES_SHOWN));
    for (const li of items) li.hidden = !shown.has(li);
    grid?.setAttribute("data-managed", "");
    if (more) {
      more.hidden = shown.size === list.length;
      more.textContent = `Show All ${formatCount(list.length)} Examples`;
    }
  };
  examples.querySelectorAll<HTMLButtonElement>(".seg [data-gallery]").forEach((b) => {
    b.addEventListener("click", () => {
      filter = b.dataset.gallery ?? "";
      expanded = false;
      examples.querySelectorAll(".seg [data-gallery]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      draw();
    });
  });
  more?.addEventListener("click", () => {
    expanded = true;
    draw();
  });
}

// --- Explore: load the chart code when the section comes near the screen ----------------------
const explore = document.querySelector<HTMLElement>("[data-explore]");
if (explore) {
  const near = new IntersectionObserver((entries) => {
    if (!entries.some((e) => e.isIntersecting)) return;
    near.disconnect();
    void import("./explore").then((m) => m.enhanceExplore(explore, readJson<Dataset>("dataset-data")));
  }, { rootMargin: "400px 0px" });
  near.observe(explore);
}

// --- Arrow keys step between datasets, only when focus is on the page itself ------------------
document.addEventListener("keydown", (e) => {
  const target = document.activeElement;
  const onPage = !target || target === document.body || target === document.documentElement || target.id === "page";
  const step = datasetStep(e, onPage);
  const link = step ? document.querySelector<HTMLAnchorElement>(`a[data-step="${step > 0 ? "next" : "prev"}"]`) : null;
  if (link) location.href = link.href;
});
