<script context="module" lang="ts">
	// rhwp WASM 은 페이지 세션당 한 번만 초기화한다.
	let rhwpPromise: Promise<typeof import('@rhwp/core')> | null = null;
	let measureCtx: CanvasRenderingContext2D | null = null;
	let lastFont = '';
	let instanceCounter = 0;

	const loadRhwp = () => {
		if (!rhwpPromise) {
			rhwpPromise = (async () => {
				(globalThis as any).measureTextWidth = (font: string, text: string) => {
					if (!measureCtx) measureCtx = document.createElement('canvas').getContext('2d');
					if (!measureCtx) return text.length * 8;
					if (font !== lastFont) {
						measureCtx.font = font;
						lastFont = font;
					}
					return measureCtx.measureText(text).width;
				};
				const [mod, wasm] = await Promise.all([
					import('@rhwp/core'),
					import('@rhwp/core/rhwp_bg.wasm?url')
				]);
				await mod.default({ module_or_path: wasm.default });
				return mod;
			})().catch((e) => {
				rhwpPromise = null;
				throw e;
			});
		}
		return rhwpPromise;
	};
</script>

<script lang="ts">
	import { getContext, onDestroy, tick } from 'svelte';
	import DOMPurify from 'dompurify';
	import { scopeSvgIds } from '$lib/utils';
	import Spinner from './Spinner.svelte';

	export let data: ArrayBuffer;
	export let className = 'w-full h-[70vh]';

	const i18n = getContext<any>('i18n');
	const idPrefix = `hwp${++instanceCounter}`;

	let doc: any = null;
	let pages: { w: number; h: number }[] = [];
	let loading = true;
	let error = '';
	let container: HTMLDivElement;
	let observer: IntersectionObserver | null = null;
	let loadToken = 0;
	const rendered = new Set<number>();

	const cleanup = () => {
		observer?.disconnect();
		observer = null;
		rendered.clear();
		try {
			doc?.free();
		} catch (e) {}
		doc = null;
		pages = [];
	};

	const renderPage = (i: number, el: HTMLElement) => {
		if (!doc || rendered.has(i)) return;
		rendered.add(i);
		try {
			const svg = doc.renderPageSvg(i);
			el.innerHTML = DOMPurify.sanitize(scopeSvgIds(svg, `${idPrefix}-p${i}-`), {
				USE_PROFILES: { svg: true, svgFilters: true }
			});
			const node = el.querySelector('svg');
			if (node) {
				node.removeAttribute('width');
				node.removeAttribute('height');
				node.style.width = '100%';
				node.style.height = 'auto';
				node.style.display = 'block';
			}
		} catch (e) {
			console.error('HWP page render error:', i, e instanceof Error ? e.name : 'error');
			el.textContent = $i18n.t('Failed to render this page.');
		}
	};

	const load = async (buf: ArrayBuffer) => {
		const token = ++loadToken;
		cleanup();
		loading = true;
		error = '';
		try {
			const mod = await loadRhwp();
			if (token !== loadToken) return;
			let d: any;
			try {
				d = new mod.HwpDocument(new Uint8Array(buf));
			} catch (e) {
				console.error('HWP open error:', e instanceof Error ? e.name : 'error');
				error = $i18n.t(
					'This document cannot be previewed (encrypted, DRM-protected or corrupted).'
				);
				return;
			}
			doc = d;
			const count = d.pageCount();
			const list: { w: number; h: number }[] = [];
			for (let i = 0; i < count; i++) {
				let w = 794;
				let h = 1123;
				try {
					const info = JSON.parse(d.getPageInfo(i));
					w = Number(info.width) || w;
					h = Number(info.height) || h;
				} catch (e) {}
				list.push({ w, h });
			}
			pages = list;
			loading = false;
			await tick();
			if (token !== loadToken) return;
			observer = new IntersectionObserver(
				(entries) => {
					for (const entry of entries) {
						if (entry.isIntersecting) {
							const el = entry.target as HTMLElement;
							renderPage(Number(el.dataset.page), el);
							observer?.unobserve(el);
						}
					}
				},
				{ root: container, rootMargin: '600px 0px' }
			);
			container.querySelectorAll<HTMLElement>('[data-page]').forEach((el) => observer?.observe(el));
		} catch (e) {
			if (token === loadToken) {
				console.error('HWP viewer error:', e instanceof Error ? e.name : 'error');
				error = $i18n.t('Failed to load HWP preview.');
			}
		} finally {
			if (token === loadToken) loading = false;
		}
	};

	$: if (data) load(data);

	onDestroy(() => {
		++loadToken;
		cleanup();
	});
</script>

<div class="relative {className}">
	{#if loading}
		<div class="flex h-full items-center justify-center">
			<Spinner className="size-5" />
		</div>
	{:else if error}
		<div class="text-red-500 text-sm p-4">{error}</div>
	{/if}
	<div
		bind:this={container}
		class="h-full overflow-auto rounded-lg bg-gray-100 dark:bg-gray-850 p-2 space-y-2 {loading ||
		error
			? 'hidden'
			: ''}"
	>
		{#each pages as page, i (i)}
			<div
				data-page={i}
				class="mx-auto max-w-[900px] bg-white shadow-sm"
				style="aspect-ratio: {page.w} / {page.h};"
			></div>
		{/each}
	</div>
</div>
