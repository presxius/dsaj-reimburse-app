<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import ArrowUUpLeft from 'phosphor-svelte/lib/ArrowUUpLeftIcon';
	import ReimbursementForm from '#lib/components/ReimbursementForm.svelte';
	import PageHeader from '#lib/components/PageHeader.svelte';
	import { ROLE_LABEL } from '#lib/labels.ts';
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

	const lastReturn = $derived(item?.history.findLast((h) => h.to_status === 'revision_required') ?? null);
</script>

<PageHeader
	eyebrow={item ? item.code : 'Memuat…'}
	title={item?.status === 'draft' ? 'Lanjutkan Draft' : 'Perbaiki Pengajuan'}
	description="Perbarui data atau struk, lalu kirim kembali."
/>

{#if item}
	{#if !['draft', 'revision_required'].includes(item.status)}
		<p class="panel p-6 text-muted">Pengajuan ini tidak dapat diubah lagi.</p>
	{:else}
		{#if lastReturn?.note}
			<div class="reveal mb-5 flex items-start gap-3.5 rounded-2xl border border-warn/35 bg-warn/[0.07] p-4 sm:p-5" style="--d: 100ms">
				<span class="grid size-8 shrink-0 place-items-center rounded-full bg-warn text-white"><ArrowUUpLeft size={16} weight="bold" /></span>
				<div>
					<p class="text-[13px] text-muted">
						Dikembalikan oleh <span class="font-medium text-ink">{lastReturn.actor.name}</span> · {ROLE_LABEL[lastReturn.actor.role]}
					</p>
					<p class="mt-1 text-[15px] text-ink">“{lastReturn.note}”</p>
				</div>
			</div>
		{/if}
		<ReimbursementForm initial={item} onsaved={(r) => goto(`/reimburse/${r.id}`)} />
	{/if}
{/if}
