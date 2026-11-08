<script lang="ts">
	import DownloadSimple from 'phosphor-svelte/lib/DownloadSimpleIcon';
	import StatusBadge from '#lib/components/StatusBadge.svelte';
	import CountUp from '#lib/components/CountUp.svelte';
	import { ALL_STATUSES, CATEGORY_LABEL, STATUS_LABEL, formatDate, formatRupiah } from '#lib/labels.ts';
	import { api, query } from '#lib/services/api.ts';
	import { auth, notifyError } from '#lib/session.svelte.ts';
	import type { ReportRow, Summary } from '#lib/types/index.ts';

	const firstOfMonth = new Date(new Date().getFullYear(), new Date().getMonth(), 1)
		.toLocaleDateString('en-CA');
	const isAdmin = ['admin_transport', 'admin_consumption'].includes(auth.user!.role);

	let filters = $state({ category: '', status: '', date_from: firstOfMonth, date_to: '' });
	let data = $state<{ summary: Summary; rows: ReportRow[] } | null>(null);

	const qs = $derived(query({ ...filters }));

	$effect(() => {
		const q = qs;
		api
			.get<{ summary: Summary; rows: ReportRow[] }>('/reports' + q)
			.then((d) => (data = d))
			.catch(notifyError);
	});
</script>

<div class="mb-6 flex flex-wrap items-center justify-between gap-3">
	<h1 class="text-2xl font-semibold tracking-tight">Laporan Reimburse</h1>
	<a class="btn btn-secondary" href="/api/reports/export{qs}" download><DownloadSimple size={16} /> Unduh CSV</a>
</div>

<div class="card mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
	<div>
		<label class="label" for="from">Dari tanggal</label>
		<input id="from" type="date" class="input" bind:value={filters.date_from} />
	</div>
	<div>
		<label class="label" for="to">Sampai tanggal</label>
		<input id="to" type="date" class="input" bind:value={filters.date_to} />
	</div>
	{#if !isAdmin}
		<div>
			<label class="label" for="cat">Kategori</label>
			<select id="cat" class="input" bind:value={filters.category}>
				<option value="">Semua</option>
				<option value="transport">Transportasi</option>
				<option value="consumption">Konsumsi</option>
			</select>
		</div>
	{/if}
	<div>
		<label class="label" for="st">Status</label>
		<select id="st" class="input" bind:value={filters.status}>
			<option value="">Semua</option>
			{#each ALL_STATUSES as s (s)}
				<option value={s}>{STATUS_LABEL[s]}</option>
			{/each}
		</select>
	</div>
</div>

{#if data}
	<div class="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
		<div class="card">
			<div class="text-xs text-muted">Jumlah pengajuan</div>
			<div class="num text-2xl font-semibold"><CountUp value={data.summary.total_count} /></div>
		</div>
		<div class="card">
			<div class="text-xs text-muted">Total nominal</div>
			<div class="num text-xl font-semibold"><CountUp value={data.summary.total_amount} format={formatRupiah} /></div>
		</div>
		{#each ['transport', 'consumption'] as const as c (c)}
			<div class="card">
				<div class="text-xs text-muted">{CATEGORY_LABEL[c]}</div>
				<div class="num text-xl font-semibold"><CountUp value={data.summary.by_category[c]?.amount ?? 0} format={formatRupiah} /></div>
				<div class="text-xs text-muted">{data.summary.by_category[c]?.count ?? 0} pengajuan</div>
			</div>
		{/each}
	</div>

	<div class="card overflow-x-auto p-0">
		<table class="table-base">
			<thead>
				<tr>
					<th>Kode</th><th>Karyawan</th><th>Kategori</th><th>Tgl Transaksi</th><th>Merchant</th>
					<th class="text-right">Nominal</th><th>Status</th><th>Dibayar</th><th>Referensi</th>
				</tr>
			</thead>
			<tbody>
				{#each data.rows as r (r.id)}
					<tr>
						<td><a class="num text-accent hover:underline" href="/reimburse/{r.id}">{r.code}</a></td>
						<td>{r.employee.name}</td>
						<td>{CATEGORY_LABEL[r.category]}</td>
						<td class="whitespace-nowrap">{formatDate(r.transaction_date)}</td>
						<td>{r.merchant ?? '-'}</td>
						<td class="num text-right whitespace-nowrap">{formatRupiah(r.amount)}</td>
						<td><StatusBadge status={r.status} /></td>
						<td class="whitespace-nowrap">{formatDate(r.payment_date)}</td>
						<td>{r.payment_reference ?? '-'}</td>
					</tr>
				{:else}
					<tr><td colspan="9" class="py-8 text-center text-faint">Tidak ada data pada periode ini.</td></tr>
				{/each}
			</tbody>
		</table>
	</div>
{/if}
