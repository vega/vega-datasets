/**
 * The density overview of a long table (lib/large-data.ts), binned when the site is built
 * from every row of the local file, so the page shows where the rows fall without
 * downloading the file.
 */
import * as vega from "vega";
import { type Dataset, effectiveMissing } from "../lib/catalog";
import { DENSITY_BINS, type DensityGrid, densityGrid } from "../lib/large-data";
import { markerForms } from "../lib/starter";
import { readData } from "./repo";

/** Every row of a table file, as Vega reads it (CSV and TSV values stay strings). */
export function readRows(d: Dataset): Record<string, unknown>[] {
  return vega.read(readData(d.file), { type: d.format as "csv" | "tsv" | "json" }) as Record<string, unknown>[];
}

/** The grid of two fields, without the rows their documented missing-value markers leave out. */
export function densityOf(d: Dataset, axes: { x: string; y: string }): DensityGrid {
  const markers = (name: string) => d.fields.flatMap((f) => (f.name === name ? markerForms(f, effectiveMissing(d, f) ?? []) : []));
  return densityGrid(readRows(d), axes.x, axes.y, DENSITY_BINS, { x: markers(axes.x), y: markers(axes.y) });
}
