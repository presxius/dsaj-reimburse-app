<script lang="ts" generics="T extends string">
	import type { Component } from 'svelte';

	let {
		options,
		value = $bindable(),
		label,
		size = 'md'
	}: {
		options: { value: T; label: string; icon?: Component<any> }[];
		value: T;
		label: string;
		size?: 'sm' | 'md';
	} = $props();

	const index = $derived(Math.max(0, options.findIndex((o) => o.value === value)));
	const name = `seg-${Math.random().toString(36).slice(2, 8)}`;
</script>

<!-- Radio asli (tersembunyi) memberi navigasi panah keyboard; "thumb" meluncur ke opsi terpilih. -->
<div
	class="relative grid auto-cols-fr grid-flow-col rounded-[11px] bg-sunken p-1 {size === 'sm' ? 'h-9' : 'h-10'}"
	role="radiogroup"
	aria-label={label}
>
	<span
		class="absolute inset-y-1 left-1 rounded-lg bg-surface shadow-[0_1px_2px_rgb(0_0_0/0.08),0_0_0_1px_var(--line)] transition-transform duration-[380ms] ease-spring"
		style="width: calc((100% - 0.5rem) / {options.length}); transform: translateX({index * 100}%)"
		aria-hidden="true"
	></span>
	{#each options as o (o.value)}
		{@const on = o.value === value}
		<label
			class="relative flex min-w-0 cursor-pointer items-center justify-center gap-1.5 rounded-lg px-2 font-medium sm:px-3 whitespace-nowrap transition-colors duration-200 select-none has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-ink {size ===
			'sm'
				? 'text-[13px]'
				: 'text-sm'} {on ? 'text-ink' : 'text-muted hover:text-ink'}"
		>
			<input type="radio" class="sr-only" {name} value={o.value} bind:group={value} />
			{#if o.icon}
				<!-- Di layar sempit ikon disembunyikan agar label tidak meluber. -->
				<o.icon size={16} weight={on ? 'fill' : 'regular'} class="transition-transform duration-300 ease-spring max-sm:hidden {on ? 'scale-110' : ''}" />
			{/if}
			{o.label}
		</label>
	{/each}
</div>
