/** Prepare chart code when a reader approaches it; never hydrate or move its links. */
export function prepareOnIntent(controls: HTMLElement, chart: HTMLElement, prepare: () => Promise<unknown>): void {
  const connection = (navigator as Navigator & { connection?: { saveData?: boolean; effectiveType?: string } }).connection;
  // Save-Data and very slow connections keep the fully on-demand path.
  if (connection?.saveData || /^(slow-)?2g$/.test(connection?.effectiveType ?? "")) return;
  let started = false;
  const warm = () => {
    if (started) return;
    started = true;
    cleanUp();
    // Background preparation stays quiet. The normal chart action handles failure/retry.
    void prepare().catch(() => {});
  };
  const approach = () => {
    const box = controls.getBoundingClientRect();
    if (box.top < window.innerHeight + 300 && box.bottom > 0) warm();
  };
  const cleanUp = () => {
    window.removeEventListener("scroll", approach);
    for (const el of [controls, chart]) {
      el.removeEventListener("pointerover", warm);
      el.removeEventListener("pointerdown", warm);
      el.removeEventListener("focusin", warm);
    }
  };
  // Deliberately no initial intersection check: opening a page alone downloads no Vega.
  window.addEventListener("scroll", approach, { passive: true });
  for (const el of [controls, chart]) {
    el.addEventListener("pointerover", warm, { passive: true });
    el.addEventListener("pointerdown", warm, { passive: true });
    el.addEventListener("focusin", warm);
  }
}
