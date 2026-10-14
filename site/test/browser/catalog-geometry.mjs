// Run in the browser: CSS-pixel geometry, including text's effective font size.
// Attribute comparisons miss the static/live scaling bug this measures.
export function catalogGeometry() {
  const host = document.querySelector('[data-chart]');
  const svg = [...host.querySelectorAll('svg.marks')].find((s) => s.getBoundingClientRect().width > 0 && !s.closest('.pending'));
  if (!svg) throw new Error('No visible catalog SVG');
  const box = svg.getBoundingClientRect();
  const rect = (el) => {
    const r = el.getBoundingClientRect();
    return { x: r.x - box.x, y: r.y - box.y, width: r.width, height: r.height };
  };
  return {
    width: box.width, height: box.height, hostHeight: host.getBoundingClientRect().height,
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    points: [...svg.querySelectorAll('.mark-symbol.role-mark path')].map((e) => ({ name: e.getAttribute('aria-label')?.split(':')[0], ...rect(e) })),
    text: [...svg.querySelectorAll('text')].filter((e) => e.textContent).map((e) => ({
      text: e.textContent, role: e.closest('g').getAttribute('class'), ...rect(e),
      font: parseFloat(getComputedStyle(e).fontSize) * Math.hypot(e.getScreenCTM().a, e.getScreenCTM().b),
    })),
  };
}
