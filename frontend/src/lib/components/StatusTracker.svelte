<script lang="ts">
	import Check from 'phosphor-svelte/lib/CheckIcon';
	import X from 'phosphor-svelte/lib/XIcon';
	import ArrowUUpLeft from 'phosphor-svelte/lib/ArrowUUpLeftIcon';
	import type { HistoryEntry, Status } from '#lib/types/index.ts';

	let { status, history }: { status: Status; history: HistoryEntry[] } = $props();

	const STEPS = ['Diajukan', 'Verifikasi admin', 'Persetujuan atasan', 'Pembayaran', 'Lunas'];
	// Label pendek untuk layar sempit: 5 kolom di ponsel tidak muat kata panjang.
	const SHORT = ['Diajukan', 'Verifikasi', 'Atasan', 'Bayar', 'Lunas'];

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
	const caption = $derived(
		status === 'rejected' ? 'Ditolak' : status === 'revision_required' ? 'Perlu revisi' : 'Saat ini'
	);

	// Garis terisi dari 0 saat pertama tampil, lalu mengikuti perubahan status.
	let shown = $state(false);
	$effect(() => {
		const id = requestAnimationFrame(() => (shown = true));
		return () => cancelAnimationFrame(id);
	});
</script>

<div class="relative">
	<div class="absolute top-[13px] right-[10%] left-[10%] h-[3px] rounded-full bg-line" aria-hidden="true">
		<div
			class="h-full origin-left rounded-full transition-transform duration-[1100ms] ease-snap {status === 'paid'
				? 'bg-lime-deep'
				: 'bg-ink'}"
			style="transform: scaleX({shown ? progress : 0})"
		></div>
	</div>
	<ol class="relative grid grid-cols-5" aria-label="Progres pengajuan">
		{#each STEPS as label, i (label)}
			{@const done = i < current}
			{@const active = i === current}
			{@const stop = active && halted}
			{@const last = i === STEPS.length - 1}
			<li class="flex flex-col items-center gap-2 text-center" aria-current={active ? 'step' : undefined}>
				<span
					class="grid size-[29px] place-items-center rounded-full border-2 text-xs transition-[background-color,border-color,color,transform] duration-500 ease-spring
					{done
						? last
							? 'border-lime-deep bg-lime text-on-lime'
							: 'border-chip bg-chip text-on-chip'
						: stop
							? status === 'rejected'
								? 'border-danger bg-danger text-white'
								: 'border-warn bg-warn text-white'
							: active
								? 'border-ink bg-surface'
								: 'border-line-strong bg-surface text-faint'} {shown ? 'scale-100' : 'scale-75'}"
					style="transition-delay: {shown ? 120 + i * 110 : 0}ms"
				>
					{#if done}
						<Check size={14} weight="bold" />
					{:else if stop && status === 'rejected'}
						<X size={14} weight="bold" />
					{:else if stop}
						<ArrowUUpLeft size={14} weight="bold" />
					{:else if active}
						<span class="size-2.5 rounded-full bg-lime" style="animation: halo 1.8s var(--ease) infinite"></span>
					{:else}
						<span class="code text-[11px]">{i + 1}</span>
					{/if}
				</span>
				<span class="text-[11.5px] leading-tight sm:text-[13px] {done || active ? 'font-medium text-ink' : 'text-faint'}">
					<span class="sm:hidden">{SHORT[i]}</span><span class="max-sm:hidden">{label}</span>
				</span>
				{#if active}
					<span class="eyebrow -mt-1 hidden text-[10px] sm:block {stop ? (status === 'rejected' ? 'text-danger' : 'text-warn') : ''}"
						>{caption}</span
					>
				{/if}
			</li>
		{/each}
	</ol>
</div>
