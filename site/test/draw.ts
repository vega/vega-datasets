/** Draw a Vega-Lite spec the way the page does (the expression interpreter, no eval), for tests. */
import * as vega from 'vega';
import { expressionInterpreter } from 'vega-interpreter';
import { compile, type TopLevelSpec } from 'vega-lite';
import { expect } from 'vitest';

type Spec = Record<string, unknown>;

/** Compile to Vega (no warnings) and run it on `rows` in place of the spec's file, with the page's CSP-safe settings. */
export async function draw(spec: Spec, rows: object[], signals: Record<string, unknown> = {}): Promise<vega.View> {
  const warnings: string[] = [];
  const logger = {
    level: () => logger,
    error: (...m: unknown[]) => { throw new Error(m.join(' ')); },
    warn: (...m: unknown[]) => { warnings.push(m.join(' ')); return logger; },
    info: () => logger,
    debug: () => logger,
  };
  // The rows replace the file; the spec's own data format (its parse) still applies.
  const { url: _, ...data } = (spec.data ?? {}) as Record<string, unknown>;
  const { spec: vg } = compile({ ...spec, data: { ...data, values: rows } } as TopLevelSpec, { logger: logger as never });
  expect(warnings).toEqual([]);
  const view = new vega.View(vega.parse(vg, undefined, { ast: true }), { renderer: 'none', expr: expressionInterpreter } as vega.ViewOptions);
  for (const [k, v] of Object.entries(signals)) view.signal(k, v);
  await view.runAsync();
  return view;
}

/** Every row of every dataset in the view that has `key` (e.g. an aggregate's output field). */
export function rowsWith(view: vega.View, key: string): Record<string, unknown>[] {
  const names = (view.getState({ data: vega.truthy, signals: vega.falsy }).data ?? {}) as Record<string, unknown>;
  return Object.keys(names).flatMap((n) => (view.data(n) as Record<string, unknown>[]).filter((r) => key in r));
}
