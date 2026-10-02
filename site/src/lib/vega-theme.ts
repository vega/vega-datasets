/**
 * Vega config built from the page's light palette, or from the system colors in a
 * forced-colors mode (Windows High Contrast). Marks keep
 * Vega's defaults (tableau10, which the --chart-* tokens mirror); only the chrome around
 * them (axes, legends, text) follows the page. No DOM here: the build resolves tokens from
 * site.css, the browser from the live stylesheet and the forced palette (client/theme.ts).
 *
 * SVG charts also follow forced-color changes without redrawing: site.css restyles Vega's axis,
 * legend and label classes from the same tokens (see "Vega's SVG" there), and in forced
 * colors with the system colors, which also reaches the charts drawn at build time.
 * Canvas charts paint pixels that CSS can't reach, so they take every color from here.
 */
type Config = Record<string, unknown>;

/** The forced palette's system colors, as concrete values. */
export interface SystemColors {
  canvasText: string;
  canvas: string;
  grayText: string;
  highlight: string;
}

/**
 * The colors of a chart's chrome: text, axis and legend rules, grid lines, the ground
 * behind marks, and the brush. Data marks keep their own colors (tableau10 and the
 * --chart-* tokens), in forced colors too.
 */
export interface ChartInk {
  forced: boolean;
  ink: string;
  strong: string;
  muted: string;
  rule: string;
  grid: string;
  surface: string;
  brush: string;
}

/** Chart chrome from the theme tokens (`token` resolves one). */
export function tokenInk(token: (name: string) => string): ChartInk {
  return {
    forced: false,
    ink: token("--ink"),
    strong: token("--ink-strong"),
    muted: token("--ink-muted"),
    rule: token("--rule"),
    grid: token("--rule-faint"),
    surface: token("--surface"),
    brush: token("--ink"),
  };
}

/**
 * Chart chrome in a forced-colors mode: text and rules in CanvasText (a muted gray could
 * fall below contrast on the forced ground), grid lines in GrayText, the brush in Highlight.
 */
export function forcedInk(c: SystemColors): ChartInk {
  return {
    forced: true,
    ink: c.canvasText,
    strong: c.canvasText,
    muted: c.canvasText,
    rule: c.canvasText,
    grid: c.grayText,
    surface: c.canvas,
    brush: c.highlight,
  };
}

/** How light a color is (0 black, 1 white; WCAG relative luminance), from #rgb, #rrggbb or rgb(). */
export function luminance(color: string): number {
  const hex = color.trim().match(/^#([\da-f]{3}|[\da-f]{6})$/i)?.[1];
  const rgb = hex
    ? (hex.length === 3 ? [...hex].map((h) => h + h) : hex.match(/../g)!).map((h) => parseInt(h, 16))
    : (color.match(/\d+(?:\.\d+)?/g) ?? ["0", "0", "0"]).slice(0, 3).map(Number);
  const [r, g, b] = rgb.map((v) => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r! + 0.7152 * g! + 0.0722 * b!;
}

/**
 * The sequential ramp for heatmaps (the density overview), from few to many: the fewest
 * rows sit closest to the ground and the most stand out, so it runs light to dark on a
 * light ground and dim to bright on a dark forced-colors ground.
 */
export const HEATMAP_ON_LIGHT = ["#deebf7", "#6baed6", "#08306b"] as const;
export const HEATMAP_ON_DARK = ["#1b3150", "#3b7dc4", "#d4e8ff"] as const;

export function heatmapRamp(surface: string): readonly string[] {
  return luminance(surface) < 0.2 ? HEATMAP_ON_DARK : HEATMAP_ON_LIGHT;
}

/**
 * The config for chart chrome `c`, in `font`. It sets every color Vega draws the chrome
 * with: the canvas renderer paints pixels, and forced-colors mode leaves SVG attributes alone.
 */
export function chartConfig(c: ChartInk, font: string): Config {
  const guide = {
    labelColor: c.muted,
    titleColor: c.ink,
    labelFontSize: 11,
    titleFontSize: 11,
    titleFontWeight: "bold",
  };
  return {
    background: null,
    font,
    view: { stroke: null },
    range: { heatmap: [...heatmapRamp(c.surface)] },
    axis: { ...guide, domainColor: c.rule, tickColor: c.rule, gridColor: c.grid, gridWidth: 1 },
    // The base colors draw a legend's symbols when no color scale does (size, shape).
    legend: { ...guide, symbolBaseStrokeColor: c.rule },
    header: { labelColor: c.ink, titleColor: c.ink },
    title: { color: c.strong, subtitleColor: c.ink },
    text: { color: c.ink },
    selection: {
      interval: { mark: { fill: c.brush, fillOpacity: c.forced ? 0.25 : 0.08, stroke: c.forced ? c.brush : c.muted, strokeWidth: 1 } },
    },
  };
}

/** The config for a theme's tokens (the build's light theme, say). */
export function themeConfig(token: (name: string) => string): Config {
  return chartConfig(tokenInk(token), token("--font-sans"));
}
