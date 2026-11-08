<script lang="ts">
	import type { Status } from '#lib/types/index.ts';

	let { status, class: cls = '' }: { status: Status; class?: string } = $props();

	const STAMP: Partial<Record<Status, { label: string; tone: string }>> = {
		paid: { label: 'Lunas', tone: 'text-accent' },
		rejected: { label: 'Ditolak', tone: 'text-danger' },
		revision_required: { label: 'Revisi', tone: 'text-warn' }
	};

	const s = $derived(STAMP[status]);
</script>

{#if s}
	<span class="stamp {s.tone} {cls}" aria-hidden="true">{s.label}</span>
{/if}
