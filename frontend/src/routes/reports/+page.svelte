<script lang="ts">
	import DownloadSimple from 'phosphor-svelte/lib/DownloadSimpleIcon';
	import ArrowRight from 'phosphor-svelte/lib/ArrowRightIcon';
	import Car from 'phosphor-svelte/lib/CarIcon';
	import ForkKnife from 'phosphor-svelte/lib/ForkKnifeIcon';
	import StatusBadge from '#lib/components/StatusBadge.svelte';
	import CountUp from '#lib/components/CountUp.svelte';
	import EmptyState from '#lib/components/EmptyState.svelte';
	import PageHeader from '#lib/components/PageHeader.svelte';
	import Segmented from '#lib/components/Segmented.svelte';
	import { ALL_STATUSES, CATEGORY_LABEL, STATUS_LABEL, formatDate, formatRupiah } from '#lib/labels.ts';
	import { api, query } from '#lib/services/api.ts';
	import { auth, notifyError } from '#lib/session.svelte.ts';
	import type { Category, ReportRow, Summary } from '#lib/types/index.ts';

	const firstOfMonth = new Date(new Date().getFullYear(), new Date().getMonth(), 1)
		.toLocaleDateString('en-CA');
	const isAdmin = ['admin_transport', 'admin_consumption'].includes(auth.user!.role);
	const CATEGORIES: { value: Category | ''; label: string; icon?: typeof Car }[] = [
		{ value: '', label: 'Semua' },
		{ value: 'transport', label: 'Transportasi', icon: Car },
		{ value: 'consumption', label: 'Konsumsi', icon: ForkKnife }
	];

	let filters = $state<{ category: Category | ''; status: string; date_from: string; date_to: string }>({
		category: '',
		status: '',
		date_from: firstOfMonth,
		date_to: ''
	});
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

<PageHeader
	eyebrow="Rekap"
	title="Laporan Reimburse"
	description="Rekap pengajuan per periode. Unduh sebagai CSV untuk diolah di Excel."
>
	{#snippet actions()}
		<a class="group btn btn-secondary" href="/api/reports/export{qs}" download>
			<DownloadSimple size={16} class="transition-transform duration-300 ease-spring group-hover:translate-y-0.5" />
			Unduh CSV
		</a>
	{/snippet}
</PageHeader>

<section class="panel reveal mb-5 flex flex-wrap items-end gap-4 p-4 sm:p-5" style="--d: 120ms">
	<div>
		<span class="label">Periode transaksi</span>
		<div class="flex items-center gap-2">
			<input id="from" type="date" class="input w-[10.5rem]" bind:value={filters.date_from} aria-label="Dari tanggal" />
			<ArrowRight size={14} class="shrink-0 text-faint" />
			<input id="to" type="date" class="input w-[10.5rem]" bind:value={filters.date_to} aria-label="Sampai tanggal" />
		</div>
	</div>
	{#if !isAdmin}
		<div class="w-full sm:w-[22rem]">
			<span class="label">Kategori</span>
			<Segmented options={CATEGORIES} bind:value={filters.category} label="Kategori" />
		</div>
	{/if}
	<div class="w-full sm:w-52">
		<label class="label" for="st">Status</label>
		<select id="st" class="input" bind:value={filters.status}>
			<option value="">Semua status</option>
			{#each ALL_STATUSES as s (s)}
				<option value={s}>{STATUS_LABEL[s]}</option>
			{/each}
		</select>
	</div>
</section>

{#if !data}
	<div class="skeleton mb-5 h-32 rounded-2xl"></div>
	<div class="skeleton h-72 rounded-2xl"></div>
{:else}
	{@const s = data.summary}
	<!-- Kisi statistik bergaris tipis: gap-px di atas latar garis. -->
	<section class="reveal mb-5 grid gap-px overflow-hidden rounded-2xl border border-line bg-line shadow-raise sm:grid-cols-2 lg:grid-cols-4"
		style="--d: 180ms">
		<div class="bg-surface p-5">
			<p class="eyebrow">Jumlah pengajuan</p>
			<p class="display num mt-3 text-[2rem] text-ink"><CountUp value={s.total_count} /></p>
		</div>
		<div class="bg-surface p-5">
			<p class="eyebrow">Total nominal</p>
			<p class="display num mt-3 text-[2rem] text-ink"><CountUp value={s.total_amount} format={formatRupiah} /></p>
		</div>
		{#each ['transport', 'consumption'] as const as c, i (c)}
			{@const share = s.total_amount ? (s.by_category[c]?.amount ?? 0) / s.total_amount : 0}
			<div class="bg-surface p-5">
				<p class="eyebrow">{CATEGORY_LABEL[c]}</p>
				<p class="display num mt-3 text-[1.6rem] text-ink"><CountUp value={s.by_category[c]?.amount ?? 0} format={formatRupiah} /></p>
				<div class="mt-3 flex items-center gap-3">
					<div class="h-1 flex-1 overflow-hidden rounded-full bg-line">
						<div class="grow-x h-full rounded-full {i === 0 ? 'bg-ink' : 'bg-lime-deep'}" style="width: {share * 100}%; --d: {400 + i * 100}ms"></div>
					</div>
					<span class="num text-[12px] text-muted">{s.by_category[c]?.count ?? 0} · {Math.round(share * 100)}%</span>
				</div>
			</div>
		{/each}
	</section>

	<section class="panel reveal overflow-hidden" style="--d: 240ms">
		{#if data.rows.length === 0}
			<EmptyState title="Tidak ada data pada periode ini" hint="Ubah rentang tanggal atau filter untuk melihat data." />
		{:else}
			<div class="overflow-x-auto">
				<table class="table text-[13.5px]">
					<thead>
						<tr>
							<th>Kode</th><th>Karyawan</th><th>Kategori</th><th>Tgl transaksi</th><th>Merchant</th>
							<th class="text-right">Nominal</th><th>Status</th><th>Dibayar</th><th>Referensi</th>
						</tr>
					</thead>
					<tbody>
						{#each data.rows as r, i (r.id)}
							<tr class="row-in hover:bg-sunken/50" style="--d: {Math.min(i, 15) * 20}ms">
								<td><a class="code font-medium text-ink underline decoration-line-strong underline-offset-4 transition-colors hover:decoration-ink" href="/reimburse/{r.id}">{r.code}</a></td>
								<td class="whitespace-nowrap text-ink">{r.employee.name}</td>
								<td class="text-ink-2">{CATEGORY_LABEL[r.category]}</td>
								<td class="num whitespace-nowrap text-ink-2">{formatDate(r.transaction_date)}</td>
								<td class="max-w-[14rem] truncate text-ink-2">{r.merchant ?? '-'}</td>
								<td class="num text-right font-semibold whitespace-nowrap text-ink">{formatRupiah(r.amount)}</td>
								<td><StatusBadge status={r.status} /></td>
								<td class="num whitespace-nowrap text-ink-2">{formatDate(r.payment_date)}</td>
								<td class="code text-ink-2">{r.payment_reference ?? '-'}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</section>
{/if}
