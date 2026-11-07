<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import ReimbursementForm from '#lib/components/ReimbursementForm.svelte';
	import { api } from '#lib/services/api.ts';
	import { notifyError } from '#lib/session.svelte.ts';
	import type { ReimbursementDetail } from '#lib/types/index.ts';

	let item = $state<ReimbursementDetail | null>(null);

	$effect(() => {
		api
			.get<ReimbursementDetail>(`/reimbursements/${page.params.id}`)
			.then((r) => (item = r))
			.catch(notifyError);
	});

	const lastNote = $derived(
		item?.history.findLast((h) => h.to_status === 'revision_required')?.note ?? null
	);
</script>

<h1 class="mb-2 text-2xl font-semibold tracking-tight">Perbaiki Pengajuan {item?.code ?? ''}</h1>

{#if item}
	{#if !['draft', 'revision_required'].includes(item.status)}
		<p class="card text-sm text-muted">Pengajuan ini tidak dapat diubah lagi.</p>
	{:else}
		{#if lastNote}
			<div class="mb-6 rounded-lg border border-warn/30 bg-warn/10 p-4 text-sm text-fg">
				<strong>Catatan perbaikan:</strong>
				{lastNote}
			</div>
		{/if}
		<ReimbursementForm initial={item} onsaved={(r) => goto(`/reimburse/${r.id}`)} />
	{/if}
{/if}
