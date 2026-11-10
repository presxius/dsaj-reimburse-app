<script lang="ts">
	import { STATUS_HINT, STATUS_LABEL } from '#lib/labels.ts';
	import type { Status } from '#lib/types/index.ts';

	let { status, pill = false }: { status: Status; pill?: boolean } = $props();

	// Seberapa jauh pengajuan berjalan di alur; digambar sebagai isian lingkaran.
	const PROGRESS: Partial<Record<Status, number>> = {
		draft: 0,
		submitted: 0.25,
		under_review: 0.45,
		pending_approval: 0.62,
		approved: 0.8,
		processing_payment: 0.92
	};
	const C = 2 * Math.PI * 2.6; // keliling lingkaran isian

	const progress = $derived(PROGRESS[status]);
	const tone = $derived(
		status === 'rejected'
			? 'text-danger'
			: status === 'revision_required'
				? 'text-warn'
				: status === 'draft'
					? 'text-muted'
					: 'text-ink-2'
	);
</script>

<span
	class="inline-flex items-center gap-1.5 text-[13px] font-medium whitespace-nowrap {tone} {pill
		? 'h-7 rounded-full border border-line bg-surface pr-2.5 pl-2 shadow-raise'
		: ''}"
	title={STATUS_HINT[status]}
>
	<svg viewBox="0 0 16 16" class="size-[15px] shrink-0" aria-hidden="true">
		{#if status === 'paid'}
			<circle cx="8" cy="8" r="7.25" fill="var(--lime)" stroke="var(--lime-deep)" stroke-width="1" />
			<path d="m5.1 8.3 2 2 3.9-4.3" fill="none" stroke="var(--on-lime)" stroke-width="1.7"
				stroke-linecap="round" stroke-linejoin="round" />
		{:else if status === 'rejected'}
			<circle cx="8" cy="8" r="7.25" fill="currentColor" />
			<path d="m5.6 5.6 4.8 4.8m0-4.8-4.8 4.8" stroke="var(--surface)" stroke-width="1.6"
				stroke-linecap="round" />
		{:else if status === 'revision_required'}
			<circle cx="8" cy="8" r="7.25" fill="currentColor" />
			<path d="M8 4.6v4.1" stroke="var(--surface)" stroke-width="1.7" stroke-linecap="round" />
			<circle cx="8" cy="11.2" r="1" fill="var(--surface)" />
		{:else}
			<circle cx="8" cy="8" r="6.4" fill="none" stroke="currentColor" stroke-width="1.5"
				stroke-dasharray={status === 'draft' ? '2.2 2.4' : undefined} opacity={status === 'draft' ? 0.8 : 0.45} />
			{#if progress}
				<circle cx="8" cy="8" r="2.6" fill="none" stroke="currentColor" stroke-width="5.2"
					stroke-dasharray="{progress * C} {C}" transform="rotate(-90 8 8)"
					style="animation: pie-in 700ms var(--ease) 120ms both" />
			{/if}
		{/if}
	</svg>
	{STATUS_LABEL[status]}
</span>
