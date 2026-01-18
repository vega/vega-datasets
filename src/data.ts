import * as d3 from "d3-dsv";
import pkg from '../package.json';
import urls from "./urls.js";
import stringOverrides from "./stringOverrides.js";

const version = pkg.version;
type Name = keyof typeof urls;

const data: {
  [key in Name]: () => Promise<any | any[] | string> & { url: string };
} & { version: string } = { version } as any;

for (const name of Object.keys(urls) as Name[]) {
  const url = urls[name];
  const f: any = async function () {
    const result = await fetch(url);

    if (name.endsWith(".json")) {
      return await result.json();
    } else if (name.endsWith(".csv")) {
      const text = await result.text();
      const overrideKeys = stringOverrides[name];

      if (!overrideKeys || overrideKeys.length === 0) {
        // No overrides needed - use autoType directly
        return d3.csvParse(text, d3.autoType);
      }

      return d3.csvParse(text, (row) => {
        // Capture original string values for fields that should stay strings
        const originals: Record<string, string> = {};
        for (const key of overrideKeys) {
          if (key in row) originals[key] = row[key]!;
        }

        // Let d3.autoType infer types for all fields
        d3.autoType(row);

        // Restore string values for override fields (e.g., IATA codes like "0E0")
        for (const key in originals) {
          (row as any)[key] = originals[key];
        }
        return row;
      });
    } else {
      return await result.text();
    }
  };
  f.url = url;
  data[name] = f;
}

export default data;
