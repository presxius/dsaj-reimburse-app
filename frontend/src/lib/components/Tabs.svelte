<script lang="ts">
	let {
		tabs,
		active = $bindable(0),
		label
	}: { tabs: string[]; active?: number; label: string } = $props();

	let list: HTMLElement;
	let bar = $state<{ x: number; w: number } | null>(null);
	let animate = $state(false);

	const tabEls = () => list.querySelectorAll<HTMLElement>('[role="tab"]');

	function measure() {
		const el = list ? tabEls()[active] : undefined;
		if (el) bar = { x: el.offsetLeft, w: el.offsetWidth };
	}

	$effect(() => {
		void active;
		measure();
	});

	$effect(() => {
		// Ukur ulang saat lebar berubah atau font selesai dimuat; animasi baru aktif setelah posisi awal.
		const ro = new ResizeObserver(measure);
		ro.observe(list);
		document.fonts?.ready.then(measure);
		const id = requestAnimationFrame(() => (animate = true));
		return () => {
			ro.disconnect();
			cancelAnimationFrame(id);
		};
	});

	function onkeydown(e: KeyboardEvent) {
		const step = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
		if (!step) return;
		e.preventDefault();
		active = (active + step + tabs.length) % tabs.length;
		tabEls()[active].focus();
	}
</script>

<!-- Indikator berada di dalam kontainer scroll agar ikut bergeser saat tab di-scroll (mobile). -->
<div
	bind:this={list}
	class="relative flex gap-1 overflow-x-auto px-3 [scrollbar-width:none]"
	role="tablist"
	aria-label={label}
	tabindex="-1"
	{onkeydown}
>
	{#each tabs as t, i (t)}
		<button
			role="tab"
			aria-selected={active === i}
			tabindex={active === i ? 0 : -1}
			class="relative my-1.5 h-9 shrink-0 rounded-lg px-3 text-sm font-medium whitespace-nowrap transition-colors duration-200 {active ===
			i
				? 'text-ink'
				: 'text-muted hover:bg-sunken hover:text-ink'}"
			onclick={() => (active = i)}
		>
			{t}
		</button>
	{/each}
	{#if bar}
		<span
			class="pointer-events-none absolute bottom-0 left-0 h-[2px] rounded-full bg-ink {animate
				? 'transition-[transform,width] duration-[420ms] ease-spring'
				: ''}"
			style="width: {bar.w - 16}px; transform: translateX({bar.x + 8}px)"
			aria-hidden="true"
		></span>
	{/if}
</div>
