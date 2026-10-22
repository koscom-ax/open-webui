import { describe, expect, it } from 'vitest';
import { scopeSvgIds } from './index';

const page = `<svg xmlns="http://www.w3.org/2000/svg"><defs><clipPath id="cell-clip-12"><rect width="1" height="1"/></clipPath><linearGradient id='g1'/></defs><g clip-path="url(#cell-clip-12)" style="fill:url(#g1);background:url(http://x/y.png)"><text>url(#cell-clip-12) id="cell-clip-12"</text><use xlink:href="#g1"/><use href = "#cell-clip-12"/><use href="#missing"/></g></svg>`;

describe('scopeSvgIds', () => {
	it('prefixes ids and rewrites references', () => {
		const out = scopeSvgIds(page, 'p1-');
		expect(out).toContain('id="p1-cell-clip-12"');
		expect(out).toContain("id='p1-g1'");
		expect(out).toContain('clip-path="url(#p1-cell-clip-12)"');
		expect(out).toContain('fill:url(#p1-g1)');
		expect(out).toContain('xlink:href="#p1-g1"');
		expect(out).toContain('href = "#p1-cell-clip-12"');
	});
	it('leaves external urls and unknown refs untouched', () => {
		const out = scopeSvgIds(page, 'p1-');
		expect(out).toContain('url(http://x/y.png)');
		expect(out).toContain('href="#missing"');
	});
	it('returns input unchanged without ids', () => {
		expect(scopeSvgIds('<svg><text>a</text></svg>', 'p-')).toBe('<svg><text>a</text></svg>');
	});
	it('makes identical pages disjoint', () => {
		const ids = (s: string) => [...s.matchAll(/\sid=["']([^"']+)["']/g)].map((m) => m[1]);
		const a = ids(scopeSvgIds(page, 'a-'));
		const b = ids(scopeSvgIds(page, 'b-'));
		expect(a.filter((x) => b.includes(x))).toEqual([]);
	});
});
