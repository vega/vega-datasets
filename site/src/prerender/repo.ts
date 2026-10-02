/** The repository's data files, read when the site is built. */
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

/** The repository root: the build runs from it or from site/ (found by its datapackage.json). */
export const REPO_ROOT = (() => {
  let dir = process.cwd();
  for (let i = 0; i < 4; i++) {
    if (existsSync(path.join(dir, "datapackage.json")) && existsSync(path.join(dir, "data"))) return dir;
    dir = path.dirname(dir);
  }
  throw new Error(`Can't find the repository root (datapackage.json) above ${process.cwd()}`);
})();

/** A file under data/, as text. */
export function readData(file: string): string {
  return readFileSync(path.join(REPO_ROOT, "data", file), "utf8");
}

/** Read a dataset's public URL (jsDelivr or GitHub Pages) from the local copy, as the tests do. */
export function readDataUrl(url: string): string {
  const rel = url.split("/data/").pop();
  if (!rel) throw new Error(`Not a vega-datasets data URL: ${url}`);
  return readData(rel);
}
