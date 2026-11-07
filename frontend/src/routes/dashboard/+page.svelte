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
	<h1 class="text-2xl font-semibold tracking-tight">Halo, {auth.user!.name}</h1>
	<p class="text-sm text-muted">{ROLE_LABEL[role]}</p>
</div>

{#if !data}
	<p class="text-faint">Memuat...</p>
{:else}
	<div class="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-5">
		<div class="card">
			<div class="text-xs text-muted">Total pengajuan</div>
			<div class="num mt-1 text-2xl font-semibold">{data.total_count}</div>
			<div class="mt-1 text-xs text-faint">{formatRupiah(data.total_amount)}</div>
		</div>
		{#each FOCUS[role] as s (s)}
			<div class="card">
				<div class="text-xs text-muted">{STATUS_LABEL[s]}</div>
				<div class="num mt-1 text-2xl font-semibold">{data.by_status[s]?.count ?? 0}</div>
				<div class="mt-1 text-xs text-muted">{formatRupiah(data.by_status[s]?.amount ?? 0)}</div>
			</div>
		{/each}
	</div>

	<div class="grid gap-6 lg:grid-cols-3">
		<div class="card lg:col-span-2">
			<div class="mb-3 flex items-center justify-between">
				<h2 class="font-semibold text-fg">Pengajuan terbaru</h2>
				{#if role === 'employee'}
					<a href="/reimburse/new" class="btn btn-primary">+ Ajukan reimburse</a>
				{/if}
			</div>
			{#if data.recent.length === 0}
				<p class="py-6 text-center text-sm text-faint">Belum ada pengajuan.</p>
			{:else}
				<ul class="divide-y divide-line">
					{#each data.recent as r (r.id)}
						<li>
							<a href="/reimburse/{r.id}" class="flex items-center justify-between gap-3 py-3 hover:bg-subtle">
								<div class="min-w-0">
									<div class="text-sm font-medium text-fg">
										{r.code} · {CATEGORY_LABEL[r.category]}
									</div>
									<div class="truncate text-xs text-muted">
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
			<h2 class="mb-3 font-semibold text-fg">Per kategori</h2>
			{#each ['transport', 'consumption'] as const as c (c)}
				<div class="flex justify-between border-b border-line py-2 text-sm">
					<span>{CATEGORY_LABEL[c]}</span>
					<span class="text-right">
						<span class="font-medium">{data.by_category[c]?.count ?? 0}</span>
						<span class="block text-xs text-muted">{formatRupiah(data.by_category[c]?.amount ?? 0)}</span>
					</span>
				</div>
			{/each}
		</div>
	</div>
{/if}
