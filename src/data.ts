import * as d3 from "d3-dsv";
import pkg from '../package.json';
import urls from "./urls.js";
import stringOverrides from "./stringOverrides.js";

const version = pkg.version;
type Name = keyof typeof urls;

// Modified from https://github.com/d3/d3-dsv/blob/a2facce660bb4895b56c62a655d0f252efc3d99f/src/autoType.js to add skipFields.
// Original code is Copyright 2013-2021 Mike Bostock.
function autoType(object: Record<string, any>, skipFields?: Set<string>) {
  for (const key in object) {
    if (skipFields?.has(key)) continue;
    let value = object[key].trim(), number, m;
    if (!value) value = null;
    else if (value === "true") value = true;
    else if (value === "false") value = false;
    else if (value === "NaN") value = NaN;
    else if (!isNaN(number = +value)) value = number;
    else if (m = value.match(/^([-+]\d{2})?\d{4}(-\d{2}(-\d{2})?)?(T\d{2}:\d{2}(:\d{2}(\.\d{3})?)?(Z|[-+]\d{2}:\d{2})?)?$/)) {
      value = new Date(value);
    }
    else continue;
    object[key] = value;
  }
  return object;
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
      const skipFields = stringOverrides[name];
      return d3.csvParse(text, (row) => autoType(row, skipFields));
    } else {
      return await result.text();
    }
  };
  f.url = url;
  data[name] = f;
}

export default data;
