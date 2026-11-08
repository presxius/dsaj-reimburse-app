<script lang="ts">
	import { goto } from '$app/navigation';
	import { fly } from 'svelte/transition';
	import StatusBadge from './StatusBadge.svelte';
	import EmptyState from './EmptyState.svelte';
	import CategoryIcon from './CategoryIcon.svelte';
	import { ease, ms, slider } from '#lib/motion.ts';
	import { api, query } from '#lib/services/api.ts';
	import { ALL_STATUSES, CATEGORY_LABEL, STATUS_LABEL, formatDate, formatRupiah } from '#lib/labels.ts';
	import { notifyError } from '#lib/session.svelte.ts';
	import type { Category, Reimbursement, Status } from '#lib/types/index.ts';

	let {
		tabs,
		showEmployee = true,
		showCategoryFilter = true
	}: {
		/** Tab status preset, mis. [{label:'Perlu diproses', status:'submitted,under_review'}] */
		tabs?: { label: string; status: string }[];
		showEmployee?: boolean;
		showCategoryFilter?: boolean;
	} = $props();

	let tab = $state(0);
	let status = $state('');
	let category = $state<Category | ''>('');
	let q = $state('');
	let items = $state<Reimbursement[]>([]);
	let loading = $state(true);
	const [send, receive] = slider();
	const cols = $derived(showEmployee ? 6 : 5);

	async function load() {
		loading = true;
		try {
			const s = tabs ? tabs[tab].status : status;
			items = await api.get<Reimbursement[]>(
				'/reimbursements' + query({ status: s, category, q: q.trim() })
			);
		} catch (e) {
			notifyError(e);
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		// Muat ulang saat filter berubah (pencarian ditunda sedikit).
		void [tab, status, category];
		const term = q;
		const t = setTimeout(load, term ? 300 : 0);
		return () => clearTimeout(t);
	});
</script>

<div class="card p-0">
	{#if tabs}
		<div class="flex gap-1 overflow-x-auto border-b border-line px-3 pt-2" role="tablist">
			{#each tabs as t, i (t.label)}
				<button
					role="tab"
					aria-selected={tab === i}
					class="relative px-3 py-2.5 text-sm font-medium whitespace-nowrap transition-colors {tab === i
						? 'text-fg'
						: 'text-muted hover:text-fg'}"
					onclick={() => (tab = i)}
				>
					{t.label}
					{#if tab === i}
						<span
							class="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-accent"
							in:receive={{ key: 'tab' }}
							out:send={{ key: 'tab' }}
						></span>
					{/if}
				</button>
			{/each}
		</div>
	{/if}

	<div class="flex flex-wrap gap-2 p-3">
		<input class="input max-w-xs" type="search" placeholder="Cari kode, merchant, keterangan..." bind:value={q} />
		{#if !tabs}
			<select class="input w-auto" bind:value={status}>
				<option value="">Semua status</option>
				{#each ALL_STATUSES as s (s)}
					<option value={s}>{STATUS_LABEL[s as Status]}</option>
				{/each}
			</select>
		{/if}
		{#if showCategoryFilter}
			<select class="input w-auto" bind:value={category}>
				<option value="">Semua kategori</option>
				<option value="transport">Transportasi</option>
				<option value="consumption">Konsumsi</option>
			</select>
		{/if}
	</div>

	<div class="overflow-x-auto">
		<table class="table-base">
			<thead>
				<tr>
					<th>Pengajuan</th>
					{#if showEmployee}<th>Karyawan</th>{/if}
					<th>Tgl Transaksi</th>
					<th>Keterangan</th>
					<th class="text-right">Nominal</th>
					<th>Status</th>
				</tr>
			</thead>
			<tbody>
				{#if loading}
					{#each { length: 5 }, i (i)}
						<tr>
							<td><div class="flex items-center gap-3"><div class="skeleton h-9 w-9 rounded-lg"></div><div class="skeleton h-3 w-28"></div></div></td>
							{#if showEmployee}<td><div class="skeleton h-3 w-24"></div></td>{/if}
							<td><div class="skeleton h-3 w-20"></div></td>
							<td><div class="skeleton h-3 w-40"></div></td>
							<td><div class="skeleton ml-auto h-3 w-20"></div></td>
							<td><div class="skeleton h-5 w-20 rounded-full"></div></td>
						</tr>
					{/each}
				{:else if items.length === 0}
					<tr>
						<td colspan={cols}>
							<EmptyState
								title={q.trim() ? `Tidak ada hasil untuk "${q.trim()}"` : 'Belum ada pengajuan di sini'}
								hint={q.trim() ? 'Coba kata kunci lain atau ubah filter.' : undefined}
							/>
						</td>
					</tr>
				{:else}
					{#each items as r, i (r.id)}
						<tr
							class="group cursor-pointer transition-colors hover:bg-subtle"
							onclick={() => goto(`/reimburse/${r.id}`)}
							in:fly|global={{ y: 6, delay: ms(Math.min(i, 10) * 30), duration: ms(260), easing: ease }}
						>
							<td>
								<div class="flex items-center gap-3">
									<CategoryIcon category={r.category} />
									<div>
										<a
											class="num font-medium text-fg group-hover:text-accent"
											href="/reimburse/{r.id}"
											onclick={(e) => e.stopPropagation()}>{r.code}</a
										>
										<div class="text-xs text-faint">{CATEGORY_LABEL[r.category]}</div>
									</div>
								</div>
							</td>
							{#if showEmployee}
								<td>
									<div>{r.employee.name}</div>
									<div class="text-xs text-faint">{r.employee.department ?? ''}</div>
								</td>
							{/if}
							<td class="whitespace-nowrap">{formatDate(r.transaction_date)}</td>
							<td class="max-w-xs truncate" title={r.description}>{r.description}</td>
							<td class="num text-right whitespace-nowrap">{formatRupiah(r.amount)}</td>
							<td><StatusBadge status={r.status} /></td>
						</tr>
					{/each}
				{/if}
			</tbody>
		</table>
	</div>
</div>
