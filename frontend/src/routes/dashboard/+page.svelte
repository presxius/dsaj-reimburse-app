<script lang="ts">
	import StatusBadge from '#lib/components/StatusBadge.svelte';
	import { CATEGORY_LABEL, ROLE_LABEL, STATUS_LABEL, formatDate, formatRupiah } from '#lib/labels.ts';
	import { api } from '#lib/services/api.ts';
	import { auth, notifyError } from '#lib/session.svelte.ts';
	import type { Reimbursement, Role, Status, Summary } from '#lib/types/index.ts';

	type Dashboard = Summary & { recent: Reimbursement[] };

	let data = $state<Dashboard | null>(null);

	// Kartu status yang paling relevan untuk tiap role.
	const FOCUS: Record<Role, Status[]> = {
		employee: ['submitted', 'revision_required', 'pending_approval', 'paid'],
		admin_transport: ['submitted', 'under_review', 'pending_approval', 'rejected'],
		admin_consumption: ['submitted', 'under_review', 'pending_approval', 'rejected'],
		approver: ['pending_approval', 'approved', 'rejected', 'paid'],
		finance: ['approved', 'processing_payment', 'paid'],
		super_admin: ['submitted', 'pending_approval', 'approved', 'paid']
	};

	$effect(() => {
		api
			.get<Dashboard>('/dashboard')
			.then((d) => (data = d))
			.catch(notifyError);
	});

	const role = $derived(auth.user!.role);
</script>

<div class="mb-6">
	<h1 class="text-2xl font-bold text-slate-800">Halo, {auth.user!.name}</h1>
	<p class="text-sm text-slate-500">{ROLE_LABEL[role]}</p>
</div>

{#if !data}
	<p class="text-slate-400">Memuat...</p>
{:else}
	<div class="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-5">
		<div class="card bg-brand-900 text-white">
			<div class="text-xs text-slate-300">Total pengajuan</div>
			<div class="mt-1 text-2xl font-bold">{data.total_count}</div>
			<div class="mt-1 text-xs text-slate-300">{formatRupiah(data.total_amount)}</div>
		</div>
		{#each FOCUS[role] as s (s)}
			<div class="card">
				<div class="text-xs text-slate-500">{STATUS_LABEL[s]}</div>
				<div class="mt-1 text-2xl font-bold text-slate-800">{data.by_status[s]?.count ?? 0}</div>
				<div class="mt-1 text-xs text-slate-500">{formatRupiah(data.by_status[s]?.amount ?? 0)}</div>
			</div>
		{/each}
	</div>

	<div class="grid gap-6 lg:grid-cols-3">
		<div class="card lg:col-span-2">
			<div class="mb-3 flex items-center justify-between">
				<h2 class="font-semibold text-slate-800">Pengajuan terbaru</h2>
				{#if role === 'employee'}
					<a href="/reimburse/new" class="btn btn-primary">+ Ajukan reimburse</a>
				{/if}
			</div>
			{#if data.recent.length === 0}
				<p class="py-6 text-center text-sm text-slate-400">Belum ada pengajuan.</p>
			{:else}
				<ul class="divide-y divide-slate-100">
					{#each data.recent as r (r.id)}
						<li>
							<a href="/reimburse/{r.id}" class="flex items-center justify-between gap-3 py-3 hover:bg-slate-50">
								<div class="min-w-0">
									<div class="text-sm font-medium text-slate-800">
										{r.code} · {CATEGORY_LABEL[r.category]}
									</div>
									<div class="truncate text-xs text-slate-500">
										{role !== 'employee' ? r.employee.name + ' · ' : ''}{formatDate(r.transaction_date)} · {r.description}
									</div>
								</div>
								<div class="shrink-0 text-right">
									<div class="text-sm font-medium">{formatRupiah(r.amount)}</div>
									<StatusBadge status={r.status} />
								</div>
							</a>
						</li>
					{/each}
				</ul>
			{/if}
		</div>

		<div class="card">
			<h2 class="mb-3 font-semibold text-slate-800">Per kategori</h2>
			{#each ['transport', 'consumption'] as const as c (c)}
				<div class="flex justify-between border-b border-slate-100 py-2 text-sm">
					<span>{CATEGORY_LABEL[c]}</span>
					<span class="text-right">
						<span class="font-medium">{data.by_category[c]?.count ?? 0}</span>
						<span class="block text-xs text-slate-500">{formatRupiah(data.by_category[c]?.amount ?? 0)}</span>
					</span>
				</div>
			{/each}
		</div>
	</div>
{/if}
