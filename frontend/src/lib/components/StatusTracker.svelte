<script lang="ts">
	import Check from 'phosphor-svelte/lib/CheckIcon';
	import X from 'phosphor-svelte/lib/XIcon';
	import ArrowUUpLeft from 'phosphor-svelte/lib/ArrowUUpLeftIcon';
	import type { HistoryEntry, Status } from '#lib/types/index.ts';

	let { status, history }: { status: Status; history: HistoryEntry[] } = $props();

	const STEPS = ['Diajukan', 'Verifikasi admin', 'Persetujuan atasan', 'Pembayaran', 'Lunas'];

	// Indeks tahap yang sedang berjalan; tahap sebelumnya dianggap selesai.
	const CURRENT: Record<Status, number> = {
		draft: 0,
		submitted: 1,
		under_review: 1,
		revision_required: 1,
		rejected: 1,
		pending_approval: 2,
		approved: 3,
		processing_payment: 3,
		paid: STEPS.length
	};

	const halted = $derived(status === 'rejected' || status === 'revision_required');
	const current = $derived.by(() => {
		if (!halted) return CURRENT[status];
		const last = history.findLast((h) => h.to_status === status);
		return last?.action.startsWith('approver') ? 2 : 1;
	});
	const progress = $derived(Math.min(current, STEPS.length - 1) / (STEPS.length - 1));

	// Garis terisi dari 0 saat pertama tampil, lalu mengikuti perubahan status.
	let shown = $state(false);
	$effect(() => {
		const id = requestAnimationFrame(() => (shown = true));
		return () => cancelAnimationFrame(id);
	});
</script>

<div class="relative">
<div class="absolute top-3.5 right-[10%] left-[10%] h-0.5 rounded-full bg-line" aria-hidden="true">
	<div
		class="h-full origin-left rounded-full bg-accent transition-transform duration-700 ease-out-expo"
		style="transform: scaleX({shown ? progress : 0})"
	></div>
</div>
<ol class="relative grid grid-cols-5" aria-label="Progres pengajuan">
	{#each STEPS as label, i (label)}
		{@const done = i < current}
		{@const active = i === current}
		{@const stop = active && halted}
		<li class="relative flex flex-col items-center gap-2 text-center" aria-current={active ? 'step' : undefined}>
			<span
				class="grid h-7 w-7 place-items-center rounded-full border-2 text-xs font-semibold transition-colors duration-300
				{done
					? 'border-accent bg-accent text-on-accent'
					: stop
						? status === 'rejected'
							? 'border-danger bg-danger text-white'
							: 'border-warn bg-warn text-white'
						: active
							? 'border-accent bg-surface text-accent ring-4 ring-accent-soft'
							: 'border-line bg-surface text-faint'}"
				style="transition-delay: {shown ? i * 90 : 0}ms"
			>
				{#if done}
					<Check size={14} weight="bold" />
				{:else if stop && status === 'rejected'}
					<X size={14} weight="bold" />
				{:else if stop}
					<ArrowUUpLeft size={14} weight="bold" />
				{:else}
					<span class="num">{i + 1}</span>
				{/if}
			</span>
			<span
				class="text-[11px] leading-tight sm:text-xs {done || active ? 'font-medium text-fg' : 'text-faint'}"
				>{label}</span
			>
		</li>
	{/each}
</ol>
</div>
