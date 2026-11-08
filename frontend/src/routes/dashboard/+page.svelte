<script lang="ts">
	import { fly } from 'svelte/transition';
	import Plus from 'phosphor-svelte/lib/PlusIcon';
	import CaretRight from 'phosphor-svelte/lib/CaretRightIcon';
	import CountUp from '#lib/components/CountUp.svelte';
	import EmptyState from '#lib/components/EmptyState.svelte';
	import CategoryIcon from '#lib/components/CategoryIcon.svelte';
	import StatusBadge from '#lib/components/StatusBadge.svelte';
	import { CATEGORY_LABEL, ROLE_LABEL, STATUS_LABEL, formatDate, formatRupiah } from '#lib/labels.ts';
	import { ease, ms } from '#lib/motion.ts';
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
	const focus = $derived(FOCUS[role]);
	const firstName = $derived(auth.user!.name.split(' ')[0]);

	const now = new Date();
	const hour = now.getHours();
	const greeting = hour < 11 ? 'Selamat pagi' : hour < 15 ? 'Selamat siang' : hour < 19 ? 'Selamat sore' : 'Selamat malam';
	const today = now.toLocaleDateString('id-ID', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

	const share = $derived.by(() => {
		const t = data?.by_category.transport?.amount ?? 0;
		const c = data?.by_category.consumption?.amount ?? 0;
		return t + c === 0 ? null : t / (t + c);
	});
</script>

<div class="mb-8 flex flex-wrap items-end justify-between gap-4">
	<div>
		<p class="text-sm text-muted">{today}</p>
		<h1 class="mt-1 text-3xl font-semibold tracking-tight">{greeting}, {firstName}.</h1>
		<p class="mt-1 text-sm text-faint">{ROLE_LABEL[role]}</p>
	</div>
	{#if role === 'employee'}
		<a href="/reimburse/new" class="group btn btn-primary">
			<Plus size={16} weight="bold" class="transition-transform duration-300 group-hover:rotate-90" />
			Ajukan reimburse
		</a>
	{/if}
</div>

{#if !data}
	<div class="mb-6 grid gap-4 lg:grid-cols-4">
		<div class="card space-y-3 lg:col-span-2 lg:row-span-2">
			<div class="skeleton h-3 w-28"></div>
			<div class="skeleton h-10 w-20"></div>
			<div class="skeleton h-4 w-36"></div>
			<div class="skeleton mt-8 h-2 w-full"></div>
		</div>
		{#each { length: 4 }, i (i)}
			<div class="card space-y-3">
				<div class="skeleton h-3 w-20"></div>
				<div class="skeleton h-7 w-10"></div>
			</div>
		{/each}
	</div>
	<div class="card space-y-4">
		{#each { length: 4 }, i (i)}
			<div class="flex items-center gap-3">
				<div class="skeleton h-9 w-9 rounded-lg"></div>
				<div class="flex-1 space-y-2"><div class="skeleton h-3 w-1/3"></div><div class="skeleton h-3 w-1/2"></div></div>
			</div>
		{/each}
	</div>
{:else}
	<div class="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
		<div class="card col-span-2 flex flex-col justify-between gap-6 lg:row-span-2">
			<div>
				<div class="text-sm text-muted">Total pengajuan</div>
				<div class="num mt-2 text-5xl font-semibold"><CountUp value={data.total_count} /></div>
				<div class="num mt-2 text-lg text-muted">
					<CountUp value={data.total_amount} format={formatRupiah} />
				</div>
			</div>
			<div>
				<div class="flex h-2 gap-1 overflow-hidden rounded-full" aria-hidden="true">
					{#if share === null}
						<div class="flex-1 bg-subtle"></div>
					{:else}
						<div
							class="origin-left rounded-full bg-accent"
							style="flex: {share}"
							in:fly|global={{ x: -40, duration: ms(600), easing: ease }}
						></div>
						<div class="rounded-full bg-faint/50" style="flex: {1 - share}"></div>
					{/if}
				</div>
				<dl class="mt-3 grid grid-cols-2 gap-4 text-sm">
					{#each ['transport', 'consumption'] as const as c, i (c)}
						<div>
							<dt class="flex items-center gap-1.5 text-muted">
								<span class="h-2 w-2 rounded-full {i === 0 ? 'bg-accent' : 'bg-faint/50'}"></span>
								{CATEGORY_LABEL[c]}
							</dt>
							<dd class="num mt-0.5 font-medium">{formatRupiah(data.by_category[c]?.amount ?? 0)}</dd>
							<dd class="text-xs text-faint">{data.by_category[c]?.count ?? 0} pengajuan</dd>
						</div>
					{/each}
				</dl>
			</div>
		</div>
		{#each focus as s, i (s)}
			<div
				class="card transition-colors hover:border-faint/60 {i === focus.length - 1 && focus.length % 2 === 1
					? 'col-span-2'
					: ''}"
				in:fly|global={{ y: 8, delay: ms(60 * i), duration: ms(300), easing: ease }}
			>
				<div class="text-xs text-muted">{STATUS_LABEL[s]}</div>
				<div class="num mt-2 text-3xl font-semibold"><CountUp value={data.by_status[s]?.count ?? 0} /></div>
				<div class="num mt-1 text-xs text-faint">{formatRupiah(data.by_status[s]?.amount ?? 0)}</div>
			</div>
		{/each}
	</div>

	<section class="card p-0">
		<div class="flex items-center justify-between px-5 pt-5 pb-2">
			<h2 class="font-semibold text-fg">Pengajuan terbaru</h2>
			{#if role === 'employee' || role === 'super_admin'}
				<a href="/reimburse" class="text-sm text-muted transition-colors hover:text-accent">Lihat semua</a>
			{/if}
		</div>
		{#if data.recent.length === 0}
			<EmptyState
				title="Belum ada pengajuan"
				hint={role === 'employee' ? 'Foto struk transportasi atau konsumsi Anda, lalu ajukan dari sini.' : 'Pengajuan baru akan muncul di sini.'}
			>
				{#if role === 'employee'}
					<a href="/reimburse/new" class="btn btn-primary"><Plus size={16} weight="bold" /> Ajukan reimburse</a>
				{/if}
			</EmptyState>
		{:else}
			<ul class="px-2 pb-2">
				{#each data.recent as r, i (r.id)}
					<li in:fly|global={{ y: 6, delay: ms(40 * i), duration: ms(280), easing: ease }}>
						<a
							href="/reimburse/{r.id}"
							class="group flex items-center gap-3 rounded-lg px-3 py-3 transition-colors hover:bg-subtle"
						>
							<CategoryIcon category={r.category} />
							<div class="min-w-0 flex-1">
								<div class="truncate text-sm font-medium text-fg">{r.merchant ?? r.description}</div>
								<div class="truncate text-xs text-muted">
									<span class="num">{r.code}</span>
									<span class="mx-1 text-faint">/</span>{role !== 'employee' ? r.employee.name : formatDate(r.transaction_date)}
								</div>
							</div>
							<div class="flex shrink-0 flex-col items-end gap-1">
								<div class="num text-sm font-medium">{formatRupiah(r.amount)}</div>
								<StatusBadge status={r.status} />
							</div>
							<CaretRight
								size={14}
								class="-ml-1 shrink-0 text-faint opacity-0 transition-all duration-200 group-hover:translate-x-0.5 group-hover:opacity-100"
							/>
						</a>
					</li>
				{/each}
			</ul>
		{/if}
	</section>
{/if}
