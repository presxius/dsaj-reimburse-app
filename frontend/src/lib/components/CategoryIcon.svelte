<script lang="ts">
	import Car from 'phosphor-svelte/lib/CarIcon';
	import ForkKnife from 'phosphor-svelte/lib/ForkKnifeIcon';
	import { CATEGORY_LABEL } from '#lib/labels.ts';
	import type { Category } from '#lib/types/index.ts';

	let { category }: { category: Category } = $props();
</script>

<span
	class="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-line bg-surface text-muted transition-colors group-hover:border-accent/40 group-hover:text-accent"
	title={CATEGORY_LABEL[category]}
>
	{#if category === 'transport'}<Car size={18} />{:else}<ForkKnife size={18} />{/if}
</span>
