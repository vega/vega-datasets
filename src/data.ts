import * as d3 from "d3-dsv";
import pkg from '../package.json';
import urls from "./urls.js";
import schemas from "./schemas.js";

const version = pkg.version;
type Name = keyof typeof urls;

// Inline type inference (mirrors d3.autoType, zero allocation)
const fixtz = new Date("2019-01-01T00:00").getHours() || new Date("2019-07-01T00:00").getHours();
const dateRegex = /^([-+]\d{2})?\d{4}(-\d{2}(-\d{2})?)?(T\d{2}:\d{2}(:\d{2}(\.\d{3})?)?(Z|[-+]\d{2}:\d{2})?)?$/;

function inferType(value: string): any {
  const v = value.trim();
  if (!v) return null;
  if (v === "true") return true;
  if (v === "false") return false;
  if (v === "NaN") return NaN;

  const num = +v;
  if (!isNaN(num)) return num;

  const m = v.match(dateRegex);
  if (m) {
    let dateStr = v;
    if (fixtz && m[4] && !m[7]) dateStr = v.replace(/-/g, "/").replace(/T/, " ");
    return new Date(dateStr);
  }

  return value;
}

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
      const protectedKeys = new Set(schemas[name] || []);

      return d3.csvParse(text, (row) => {
        for (const key in row) {
          if (protectedKeys.has(key)) continue;  // Keep as string
          (row as any)[key] = inferType(row[key]!);
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
