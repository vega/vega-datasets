/**
 * What the home page's search, chips and chart need about every dataset, fetched when
 * the reader first uses them (the cards themselves are in the page's HTML).
 */
import { catalog } from "../prerender/catalog";
import { homeIndex } from "../lib/home-model";

export function GET(): Response {
  return new Response(JSON.stringify(homeIndex(catalog)), { headers: { "Content-Type": "application/json; charset=utf-8" } });
}
