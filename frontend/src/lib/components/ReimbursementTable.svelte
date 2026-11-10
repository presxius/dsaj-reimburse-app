<script lang="ts">
	import { goto } from '$app/navigation';
	import MagnifyingGlass from 'phosphor-svelte/lib/MagnifyingGlassIcon';
	import CaretRight from 'phosphor-svelte/lib/CaretRightIcon';
	import Car from 'phosphor-svelte/lib/CarIcon';
	import ForkKnife from 'phosphor-svelte/lib/ForkKnifeIcon';
	import StatusBadge from './StatusBadge.svelte';
	import EmptyState from './EmptyState.svelte';
	import CategoryIcon from './CategoryIcon.svelte';
	import Segmented from './Segmented.svelte';
	import Tabs from './Tabs.svelte';
	import { api, query } from '#lib/services/api.ts';
	import { ALL_STATUSES, CATEGORY_LABEL, STATUS_LABEL, formatDate, formatRupiah } from '#lib/labels.ts';
	import { notifyError } from '#lib/session.svelte.ts';
	import type { Category, Reimbursement } from '#lib/types/index.ts';

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
	let searchEl: HTMLInputElement;
	const cols = $derived(showEmployee ? 7 : 6);

	const CATEGORIES: { value: Category | ''; label: string; icon?: typeof Car }[] = [
		{ value: '', label: 'Semua' },
		{ value: 'transport', label: 'Transportasi', icon: Car },
		{ value: 'consumption', label: 'Konsumsi', icon: ForkKnife }
	];

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

	// Tekan "/" di mana saja untuk langsung mencari.
	function onkeydown(e: KeyboardEvent) {
		const el = e.target as HTMLElement;
		if (e.key !== '/' || el.closest('input, textarea, select, [contenteditable]')) return;
		e.preventDefault();
		searchEl.focus();
	}
</script>

<svelte:window {onkeydown} />

<div class="panel reveal overflow-hidden" style="--d: 140ms">
	{#if tabs}
		<div class="border-b border-line">
			<Tabs tabs={tabs.map((t) => t.label)} bind:active={tab} label="Saring berdasarkan status" />
		</div>
	{/if}

	<div class="flex flex-wrap items-center gap-2.5 border-b border-line p-3">
		<div class="relative w-full sm:w-72">
			<MagnifyingGlass size={16} class="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-faint" />
			<input
				bind:this={searchEl}
				class="input h-9 min-h-9 pr-9 pl-9"
				type="search"
				placeholder="Cari pengajuan…"
				aria-label="Cari pengajuan"
				bind:value={q}
			/>
			<span class="kbd pointer-events-none absolute top-1/2 right-2.5 hidden -translate-y-1/2 sm:inline-grid">/</span>
		</div>
		{#if !tabs}
			<select class="input h-9 min-h-9 w-auto py-1" bind:value={status} aria-label="Status">
				<option value="">Semua status</option>
				{#each ALL_STATUSES as s (s)}
					<option value={s}>{STATUS_LABEL[s]}</option>
				{/each}
			</select>
		{/if}
		{#if showCategoryFilter}
			<div class="w-full sm:w-[22rem]">
				<Segmented options={CATEGORIES} bind:value={category} label="Kategori" size="sm" />
			</div>
		{/if}
		<span class="num ml-auto hidden text-[12px] text-muted sm:block" aria-live="polite">
			{loading ? 'Memuat…' : `${items.length} pengajuan`}
		</span>
	</div>

	<!-- Desktop: tabel -->
	<div class="hidden overflow-x-auto md:block">
		<table class="table">
			<thead>
				<tr>
					<th>Pengajuan</th>
					{#if showEmployee}<th>Karyawan</th>{/if}
					<th>Keterangan</th>
					<th>Tanggal</th>
					<th class="text-right">Nominal</th>
					<th>Status</th>
					<th class="w-8"><span class="sr-only">Buka</span></th>
				</tr>
			</thead>
			<tbody>
				{#if loading}
					{#each { length: 5 }, i (i)}
						<tr>
							<td><div class="flex items-center gap-3"><div class="skeleton size-9 rounded-[10px]"></div><div class="space-y-1.5"><div class="skeleton h-3 w-32"></div><div class="skeleton h-2.5 w-24"></div></div></div></td>
							{#if showEmployee}<td><div class="skeleton h-3 w-24"></div></td>{/if}
							<td><div class="skeleton h-3 w-40"></div></td>
							<td><div class="skeleton h-3 w-20"></div></td>
							<td><div class="skeleton ml-auto h-3 w-20"></div></td>
							<td><div class="skeleton h-3 w-24"></div></td>
							<td></td>
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
						<tr class="group row-link row-in" style="--d: {Math.min(i, 12) * 25}ms" onclick={() => goto(`/reimburse/${r.id}`)}>
							<td>
								<div class="flex items-center gap-3">
									<CategoryIcon category={r.category} />
									<div class="min-w-0">
										<a class="block max-w-[15rem] truncate font-medium text-ink" href="/reimburse/{r.id}"
											onclick={(e) => e.stopPropagation()}>{r.merchant ?? CATEGORY_LABEL[r.category]}</a>
										<div class="code text-[12px] text-muted">{r.code}</div>
									</div>
								</div>
							</td>
							{#if showEmployee}
								<td>
									<div class="text-ink">{r.employee.name}</div>
									<div class="text-[12px] text-muted">{r.employee.department ?? ''}</div>
								</td>
							{/if}
							<td class="max-w-[16rem] truncate text-ink-2" title={r.description}>{r.description}</td>
							<td class="num whitespace-nowrap text-ink-2">{formatDate(r.transaction_date)}</td>
							<td class="num text-right font-semibold whitespace-nowrap text-ink">{formatRupiah(r.amount)}</td>
							<td><StatusBadge status={r.status} /></td>
							<td>
								<CaretRight size={14} class="text-faint opacity-0 transition-all duration-200 group-hover:translate-x-0.5 group-hover:opacity-100" />
							</td>
						</tr>
					{/each}
				{/if}
			</tbody>
		</table>
	</div>

	<!-- Mobile: daftar -->
	<ul class="divide-y divide-line md:hidden">
		{#if loading}
			{#each { length: 4 }, i (i)}
				<li class="flex items-center gap-3 p-4">
					<div class="skeleton size-9 rounded-[10px]"></div>
					<div class="flex-1 space-y-1.5"><div class="skeleton h-3 w-2/3"></div><div class="skeleton h-2.5 w-1/3"></div></div>
				</li>
			{/each}
		{:else if items.length === 0}
			<li>
				<EmptyState title={q.trim() ? `Tidak ada hasil untuk "${q.trim()}"` : 'Belum ada pengajuan di sini'}
					hint={q.trim() ? 'Coba kata kunci lain atau ubah filter.' : undefined} />
			</li>
		{:else}
			{#each items as r, i (r.id)}
				<li class="row-in" style="--d: {Math.min(i, 12) * 25}ms">
					<a href="/reimburse/{r.id}" class="group flex items-start gap-3 p-4 transition-colors active:bg-sunken">
						<CategoryIcon category={r.category} />
						<div class="min-w-0 flex-1">
							<div class="flex items-baseline justify-between gap-3">
								<span class="truncate font-medium text-ink">{r.merchant ?? CATEGORY_LABEL[r.category]}</span>
								<span class="num shrink-0 font-semibold text-ink">{formatRupiah(r.amount)}</span>
							</div>
							<div class="mt-0.5 truncate text-[12.5px] text-muted">
								<span class="code">{r.code}</span> · {showEmployee ? r.employee.name : formatDate(r.transaction_date)}
							</div>
							<div class="mt-2"><StatusBadge status={r.status} /></div>
						</div>
					</a>
				</li>
			{/each}
		{/if}
	</ul>
</div>
