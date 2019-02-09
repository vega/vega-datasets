import urls from './urls';

type Name = keyof typeof urls;

const data: {[key in Name]: () => Promise<Response> & {url: string}} = {} as any;

for (const name of (Object.keys(urls) as Name[])) {
    const url = urls[name];
    const f: any = function() {
        return fetch(url);
    }
    f.url = url;
    data[name] = f;
}

export default data;