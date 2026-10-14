/**
 * Checks edit-link anchors into the metadata TOML without parsing any part of it on its own
 * (a suffix of valid TOML need not be valid: array-of-tables references depend on what came
 * before). The whole file is parsed once for its resources' paths, in order; then the anchors,
 * taken in that order, must each land on a header the module recognizes and strictly increase.
 */
import { parse } from 'smol-toml';
import { isResourcesHeader } from '../src/lib/completeness';

/** What is wrong with `anchors` (file → 1-based line) for the TOML `text`; empty when nothing is. */
export function anchorProblems(text: string, anchors: ReadonlyMap<string, number>): string[] {
  const lines = text.split(/\r?\n/);
  const paths = ((parse(text).resources ?? []) as { path?: string }[]).map((r) => r.path);
  const problems: string[] = [];
  let last = 0;
  paths.forEach((p, i) => {
    const line = p === undefined ? undefined : anchors.get(p);
    if (line === undefined) return void problems.push(`resource ${i + 1} (${p}) has no anchor`);
    if (!isResourcesHeader(lines[line - 1] ?? '')) problems.push(`${p}: line ${line} is not a [[resources]] header`);
    if (line <= last) problems.push(`${p}: line ${line} does not follow the previous resource's (${last})`);
    last = line;
  });
  for (const file of anchors.keys()) if (!paths.includes(file)) problems.push(`${file} is anchored but not a resource`);
  return problems;
}
