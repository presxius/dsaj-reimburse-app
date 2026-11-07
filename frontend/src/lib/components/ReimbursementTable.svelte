<script lang="ts">
	import StatusBadge from './StatusBadge.svelte';
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
		<div class="flex gap-1 overflow-x-auto border-b border-line px-3 pt-3">
			{#each tabs as t, i (t.label)}
				<button
					class="rounded-t-lg px-3 py-2 text-sm font-medium whitespace-nowrap {tab === i
						? 'border-b-2 border-accent text-accent'
						: 'text-muted hover:text-fg'}"
					onclick={() => (tab = i)}>{t.label}</button
				>
			{/each}
		</div>
	{/if}

	<div class="flex flex-wrap gap-2 p-3">
		<input class="input max-w-xs" placeholder="Cari kode, merchant, keterangan..." bind:value={q} />
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
					<th>Kode</th>
					{#if showEmployee}<th>Karyawan</th>{/if}
					<th>Kategori</th>
					<th>Tgl Transaksi</th>
					<th>Keterangan</th>
					<th class="text-right">Nominal</th>
					<th>Status</th>
				</tr>
			</thead>
			<tbody>
				{#if loading}
					<tr><td colspan="7" class="py-8 text-center text-faint">Memuat...</td></tr>
				{:else if items.length === 0}
					<tr><td colspan="7" class="py-8 text-center text-faint">Tidak ada data.</td></tr>
				{:else}
					{#each items as r (r.id)}
						<tr class="hover:bg-subtle">
							<td>
								<a class="font-medium text-accent hover:underline" href="/reimburse/{r.id}"
									>{r.code}</a
								>
							</td>
							{#if showEmployee}
								<td>
									<div>{r.employee.name}</div>
									<div class="text-xs text-faint">{r.employee.department ?? ''}</div>
								</td>
							{/if}
							<td>{CATEGORY_LABEL[r.category]}</td>
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
