import urls from './urls';
import * as d3 from 'd3-dsv';

type Name = keyof typeof urls;

const data: {[key in Name]: () => Promise<any | any[] | string> & {url: string}} = {} as any;

for (const name of (Object.keys(urls) as Name[])) {
    const url = urls[name];
    const f: any = async function() {
        const result = await fetch(url);

        if (name.endsWith('.json')) {
            return await result.json();
        } else if (name.endsWith('.csv')) {
            // TODO: remove "as any" once @types/d3-dsv has been updated
            return d3.csvParse(await result.text(), (d3 as any).autoType);
        } else {
            return await result.text();
        }
    }
    f.url = url;
    data[name] = f;
}

export default data;
