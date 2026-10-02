/**
 * How to load a file (components/SnippetTabs.astro): switching tabs (ARIA tabs: arrow
 * keys, Home and End), a Copy button on the URL and on each panel (if the clipboard is
 * blocked or unavailable, Copy selects the text), and the reader's tool, remembered across
 * pages in this browser.
 */
import { h } from "./dom";

/** Where the reader's tool is kept (localStorage). */
export const TOOL_KEY = "vega-datasets-tool";

function rememberedTool(): string | null {
  try {
    return localStorage.getItem(TOOL_KEY);
  } catch {
    return null; // Storage blocked (private mode, disabled site data): start on the first tab.
  }
}

function rememberTool(tool: string): void {
  try {
    localStorage.setItem(TOOL_KEY, tool);
  } catch {
    // Storage blocked: the pick holds on this page only.
  }
}

function copyButton(code: HTMLElement): HTMLButtonElement {
  const btn = h("button", { class: "copy-btn", type: "button", "aria-live": "polite" }, "Copy");
  let reset: ReturnType<typeof setTimeout> | undefined;
  btn.addEventListener("click", async () => {
    clearTimeout(reset);
    delete btn.dataset.copied;
    try {
      if (!navigator.clipboard?.writeText) throw new Error("Clipboard unavailable");
      await navigator.clipboard.writeText(code.textContent ?? "");
      btn.textContent = "Copied";
      btn.dataset.copied = "true";
      reset = setTimeout(() => {
        btn.textContent = "Copy";
        delete btn.dataset.copied;
      }, 1600);
    } catch {
      const sel = window.getSelection();
      if (sel) {
        const range = document.createRange();
        range.selectNodeContents(code);
        sel.removeAllRanges();
        sel.addRange(range);
      }
      btn.textContent = "Copy selected text";
    }
  });
  return btn;
}

export function enhanceSnippets(root: HTMLElement): void {
  const tabs = [...root.querySelectorAll<HTMLButtonElement>('[role="tab"]')];
  const panels = tabs.map((t) => document.getElementById(t.getAttribute("aria-controls") ?? ""));
  for (const block of [root.querySelector<HTMLElement>("[data-snippet-url]"), ...panels]) {
    const code = block?.querySelector("code");
    if (block && code) block.prepend(copyButton(code));
  }
  const select = (i: number, focus: boolean) => {
    tabs.forEach((t, j) => {
      t.setAttribute("aria-selected", String(i === j));
      t.tabIndex = i === j ? 0 : -1;
      panels[j]?.toggleAttribute("hidden", i !== j);
    });
    if (focus) tabs[i]?.focus();
  };
  const pick = (i: number, focus: boolean) => {
    select(i, focus);
    const tool = tabs[i]?.dataset.tool;
    if (tool) rememberTool(tool);
  };
  const remembered = tabs.findIndex((t) => t.dataset.tool === rememberedTool());
  if (remembered > 0) select(remembered, false);
  tabs.forEach((t, i) => {
    t.addEventListener("click", () => pick(i, false));
    t.addEventListener("keydown", (e) => {
      const n = tabs.length;
      const next = ({ ArrowRight: (i + 1) % n, ArrowLeft: (i - 1 + n) % n, Home: 0, End: n - 1 } as Record<string, number>)[e.key];
      if (next === undefined) return;
      e.preventDefault();
      pick(next, true);
    });
  });
}
