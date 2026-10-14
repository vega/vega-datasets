// @vitest-environment jsdom
// Markdown from the repository's own files, rendered when the site is built: raw HTML
// is escaped, a link can't add attributes (its href and title are escaped), and entity
// references in a link decode once, as the browser reads the attribute.
import { describe, expect, test } from 'vitest';
import { escapeHtml, markdownToHtml } from '../src/lib/markdown';

/** The one link `source` renders, as the browser parses it: its attribute values, decoded. */
function link(source: string): { href: string | null; title: string | null } {
  const host = document.createElement('div');
  host.innerHTML = markdownToHtml(source);
  const links = host.querySelectorAll('a');
  expect(links, source).toHaveLength(1);
  return { href: links[0]!.getAttribute('href'), title: links[0]!.getAttribute('title') };
}

describe('links', () => {
  test('attribute injection through an href or title is escaped', () => {
    for (const src of [
      '[a](#x"onmouseover="alert(1))',
      '[b](https://e.com/"onfocus="alert(1)"autofocus=")',
      '[c](https://e.com "t\\" onclick=\\"x")',
      '[d](<https://e.com/a b"x>)',
      '[e](https://e.com/&quot;onmouseover=&quot;alert(1) "t&quot; onfocus=&quot;x")',
    ]) {
      const tag = /<a\s[^>]*>/.exec(markdownToHtml(src))?.[0] ?? '';
      // The attribute names, reading each quoted value as a whole.
      const names = [...tag.matchAll(/\s([\w:-]+)(?:="[^"]*")?/g)].map((m) => m[1]!);
      expect(names, src).toContain('href');
      expect(names.filter((n) => !['href', 'title', 'target', 'rel'].includes(n)), src).toEqual([]);
      expect(markdownToHtml(src), src).not.toMatch(/\son\w+="/);
    }
    expect(markdownToHtml('[a](#x"onmouseover="alert(1))')).toContain('href="#x&#34;onmouseover=&#34;alert(1)"');
  });

  test('other sites open in a new tab; in-page and dataset links stay', () => {
    expect(markdownToHtml('[x](https://example.org/a?b=1&c=2)')).toBe('<p><a href="https://example.org/a?b=1&#38;c=2" target="_blank" rel="noopener">x</a></p>\n');
    expect(markdownToHtml('[cars](datasets/cars/)')).toBe('<p><a href="datasets/cars/">cars</a></p>\n');
    expect(markdownToHtml('[top](#browse)')).toBe('<p><a href="#browse">top</a></p>\n');
  });

  test('other schemes and malformed targets lead nowhere', () => {
    expect(markdownToHtml('[x](javascript:alert(1))')).toContain('href="#"');
    expect(markdownToHtml('[x](data:text/html,hi)')).toContain('href="#"');
    expect(markdownToHtml('[x](mailto:a@b.org)')).toContain('href="mailto:a@b.org"');
    // A doubled parenthesis in a description (us_state_capitals) is not a same-site path.
    expect(markdownToHtml('[x]((https://example.org/a)')).toContain('href="#"');
  });

  // CommonMark decodes entity and numeric references in a destination or title exactly once.
  test('entity references in a link are decoded once, as the browser reads the attribute', () => {
    expect(link('[q](https://e.com/?a=1&amp;b=2)').href).toBe('https://e.com/?a=1&b=2');
    expect(link('[q](https://e.com/?a=1&b=2)').href).toBe('https://e.com/?a=1&b=2');
    expect(link('[q](https://e.com/?a=1&amp;amp;b=2)').href).toBe('https://e.com/?a=1&amp;b=2');
    expect(link('[q](https://e.com/?x=1&copy=2)').href).toBe('https://e.com/?x=1&copy=2');
    expect(link('[q](https://e.com/caf&#233;)').href).toBe('https://e.com/café');
    expect(link('[q](https://e.com "A &quot;quoted&quot; title")').title).toBe('A "quoted" title');
    expect(link('[q](#cars "Tom &amp; Jerry &lt;3")').title).toBe('Tom & Jerry <3');
  });

  // An autolink's destination is its literal text: CommonMark decodes no references there.
  test('autolinks and bare URLs keep their text as written', () => {
    expect(link('<https://e.com/?a=1&amp;b=2>').href).toBe('https://e.com/?a=1&amp;b=2');
    expect(link('https://e.com/?a=1&amp;b=2').href).toBe('https://e.com/?a=1&amp;b=2');
    expect(link('<https://e.com/?a=1&b=2>').href).toBe('https://e.com/?a=1&b=2');
  });

  test('a scheme hidden behind references is still blocked', () => {
    for (const source of [
      '[x](javascript&#58;alert(1))',
      '[x](&#106;avascript:alert(1))',
      '[x](&#x6A;avascript&colon;alert(1))',
      '[x](jav&Tab;ascript:alert(1))',
      '[x](data&colon;text/html,hi)',
    ]) {
      expect(link(source).href, source).toBe('#');
    }
  });
});

test('raw HTML is escaped, not passed through', () => {
  expect(markdownToHtml('a <b onclick="x">b</b>')).toBe('<p>a &#60;b onclick=&#34;x&#34;&#62;b&#60;/b&#62;</p>\n');
  expect(escapeHtml(`<"'&>`)).toBe('&#60;&#34;&#39;&#38;&#62;');
  const html = markdownToHtml('Before <script>alert(1)</script> after <img src=x onerror=alert(1)>');
  expect(html).not.toContain('<script');
  expect(html).not.toContain('<img');
  expect(html).toContain('&#60;script&#62;');
});

test('headings nest under the section that holds them, unless the Markdown is the page', () => {
  expect(markdownToHtml('## Versioning').trim()).toBe('<h4>Versioning</h4>');
  expect(markdownToHtml('## Versioning', { sections: true }).trim()).toBe('<h2>Versioning</h2>');
  expect(markdownToHtml('#### Deep').trim()).toBe('<h6>Deep</h6>');
});
