/**
 * The light theme's tokens, read from site.css, for what the build draws: charts
 * rendered to SVG before any stylesheet exists.
 */
import css from "../styles/site.css?raw";

const root = css.match(/\n:root \{([\s\S]*?)\n\}/)?.[1] ?? "";
const values = new Map([...root.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)].map((m) => [m[1]!, m[2]!.trim()]));

/** A light-theme token's value (`--ink` → "#373a3c"). */
export function lightToken(name: string): string {
  const value = values.get(name);
  if (value === undefined) throw new Error(`site.css defines no ${name} in :root`);
  return value;
}
