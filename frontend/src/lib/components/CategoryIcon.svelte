<script lang="ts">
	import Car from 'phosphor-svelte/lib/CarIcon';
	import ForkKnife from 'phosphor-svelte/lib/ForkKnifeIcon';
	import { CATEGORY_LABEL } from '#lib/labels.ts';
	import type { Category } from '#lib/types/index.ts';

	let { category, size = 'md' }: { category: Category; size?: 'sm' | 'md' } = $props();
</script>

<!-- Di dalam baris yang di-hover (.group), ikon "menyala" lime. -->
<span
	class="grid shrink-0 place-items-center bg-sunken text-ink-2 transition-[background-color,color,transform] duration-200 ease-snap group-hover:-rotate-6 group-hover:bg-lime group-hover:text-on-lime {size ===
	'sm'
		? 'size-7 rounded-lg'
		: 'size-9 rounded-[10px]'}"
	title={CATEGORY_LABEL[category]}
>
	{#if category === 'transport'}
		<Car size={size === 'sm' ? 15 : 18} weight="duotone" />
	{:else}
		<ForkKnife size={size === 'sm' ? 15 : 18} weight="duotone" />
	{/if}
</span>
