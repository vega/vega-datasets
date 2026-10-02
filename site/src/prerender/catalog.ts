/**
 * The catalog, as the pages read it when the site is built: site/generated/catalog.json,
 * written by scripts/build_site_catalog.py (run `npm run site:build`, which does both).
 */
import file from "../../generated/catalog.json";
import { Catalog, type CatalogFile } from "../lib/catalog";

export const catalog = new Catalog(file as unknown as CatalogFile);
