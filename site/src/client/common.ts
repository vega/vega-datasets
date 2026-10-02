/** On every page: snippet tabs and the fields table's histograms. */
import { enhanceSnippets } from "./snippets";
import { enhanceSparkline } from "./sparkline";
import { enhanceProjectMenu } from "./project-menu";

document.querySelectorAll<HTMLDetailsElement>(".vg-projects").forEach(enhanceProjectMenu);

document.querySelectorAll<HTMLElement>("[data-snippets]").forEach(enhanceSnippets);
document.querySelectorAll<HTMLElement>(".spark-wrap").forEach(enhanceSparkline);
