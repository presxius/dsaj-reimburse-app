<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		eyebrow,
		title,
		description,
		actions
	}: { eyebrow?: string; title: string; description?: string; actions?: Snippet } = $props();
</script>

<header class="mb-8 flex flex-wrap items-end justify-between gap-x-6 gap-y-4">
	<div class="min-w-0">
		{#if eyebrow}<p class="eyebrow reveal mb-3">{eyebrow}</p>{/if}
		<h1 class="display reveal text-[2rem] text-ink sm:text-[2.5rem]" style="--d: 40ms">{title}</h1>
		{#if description}
			<p class="reveal mt-2.5 max-w-xl text-[15px] text-muted" style="--d: 80ms">{description}</p>
		{/if}
	</div>
	{#if actions}
		<div class="reveal flex flex-wrap items-center gap-2" style="--d: 120ms">{@render actions()}</div>
	{/if}
</header>
