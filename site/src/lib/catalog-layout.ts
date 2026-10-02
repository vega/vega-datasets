/** Shared reference drawings. Keep this separate from the spec builder so choosing
 * a layout does not bring chart code into the initial page script. CSS selects the
 * static drawing by container width; ResizeObserver selects the same live layout.
 * At a 320px viewport the smallest rendered axis font is 10px. */
export const CATALOG_LAYOUTS = [
  { maxWidth: 480, width: 400, height: 270, fontSize: 14, labels: 5 },
  { maxWidth: 760, width: 640, height: 270, fontSize: 14, labels: 7 },
  { maxWidth: 1040, width: 920, height: 290, fontSize: 14, labels: 9 },
  { maxWidth: Infinity, width: 1242, height: 300, fontSize: 13, labels: 9 },
] as const;
export type CatalogLayout = typeof CATALOG_LAYOUTS[number];
export const catalogLayout = (width: number): CatalogLayout =>
  CATALOG_LAYOUTS.find((layout) => width <= layout.maxWidth) ?? CATALOG_LAYOUTS[3];
