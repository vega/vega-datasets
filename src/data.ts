import * as d3 from "d3-dsv";
import pkg from '../package.json';
import urls from "./urls.js";

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
      return d3.csvParse(await result.text(), d3.autoType);
    } else {
      return await result.text();
    }
  };
  f.url = url;
  data[name] = f;
}

export default data;
