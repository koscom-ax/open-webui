<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { fade } from 'svelte/transition';

	const statusTextVariations = [
		'🧐 **주신 질문을 꼼꼼히 읽고 의도를 파악하고 있어요.**',
		'🔎 **답변에 꼭 필요한 정보들을 부지런히 찾고 있어요.**',
		'🤔 **어떻게 설명해 드려야 가장 좋을지 고민하고 있어요.**',
		'✍️ **이해하기 쉽도록 답변 내용을 차근차근 정리 중이에요.**',
		'✨ **거의 다 됐어요! 더 좋은 답변을 위해 다듬고 있어요.**',
		'⏳ **잠시만 더 기다려 주세요..**',
		'⏳ **잠시만 더 기다려 주세요..**',
		'⏳ **잠시만 더 기다려 주세요..**',
		'⏳ **잠시만 더 기다려 주세요..**',
		'⏳ **잠시만 더 기다려 주세요..**',
		'⏳ **잠시만 더 기다려 주세요..**',
		'⏳ **잠시만 더 기다려 주세요..**',
		'⏳ **잠시만 더 기다려 주세요..**',
		'⏳ **잠시만 더 기다려 주세요..**',
		'⏳ **잠시만 더 기다려 주세요..**',
		'⏳ **잠시만 더 기다려 주세요..**'
	];

	let statusText = statusTextVariations[0];
	let statusIndex = 0;
	let dotsCount = 1;

	let statusIntervalId: ReturnType<typeof setInterval> | null = null;
	let dotsIntervalId: ReturnType<typeof setInterval> | null = null;

	let dotsText = '.';
	$: dotsText = '.'.repeat(dotsCount);

	const advanceStatusText = () => {
		if (statusTextVariations.length === 0) return;
		statusIndex = (statusIndex + 1) % statusTextVariations.length;
		statusText = statusTextVariations[statusIndex];
		dotsCount = 1;
	};

	const advanceDots = () => {
		dotsCount = dotsCount >= 3 ? 1 : dotsCount + 1;
	};

	onMount(() => {
		statusIndex = 0;
		statusText = statusTextVariations[0] ?? '';
		dotsCount = 1;

		dotsIntervalId = setInterval(advanceDots, 1000);
		statusIntervalId = setInterval(advanceStatusText, 3000);
	});

	onDestroy(() => {
		if (statusIntervalId) clearInterval(statusIntervalId);
		if (dotsIntervalId) clearInterval(dotsIntervalId);
		statusIntervalId = null;
		dotsIntervalId = null;
	});
</script>

<span class="text-sm text-gray-600 dark:text-gray-300 select-none flex items-center">
	{#key statusText}
		<span transition:fade={{ duration: 180 }}>{statusText}</span>
	{/key}
	<span class="w-6 text-left">{dotsText}</span>
</span>
