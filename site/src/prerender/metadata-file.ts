/**
 * Where each dataset's metadata is edited: its `[[resources]]` block in the metadata TOML,
 * on the repository that built the site (SITE_REPO), read when the site is built.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import type { Dataset } from "../lib/catalog";
import { ADDITIONS_FILE, entryUrl, resourceLines } from "../lib/completeness";
import { siteRepo } from "../lib/seo";
import { REPO_ROOT } from "./repo";

export const EDIT_REPO = siteRepo(process.env);
/** The metadata file on GitHub, in the repository that built the site. */
export const METADATA_FILE_URL = `${EDIT_REPO}/blob/main/_data/datapackage_additions.toml`;

const lines = resourceLines(readFileSync(path.join(REPO_ROOT, ADDITIONS_FILE), "utf8"));

/** A link to the dataset's block in the metadata file (the file itself when its block isn't found). */
export function metadataEntry(d: Dataset): string {
  return entryUrl(METADATA_FILE_URL, lines, d.file);
}
