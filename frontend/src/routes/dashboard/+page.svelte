<script lang="ts">
	import Plus from 'phosphor-svelte/lib/PlusIcon';
	import ArrowRight from 'phosphor-svelte/lib/ArrowRightIcon';
	import CaretRight from 'phosphor-svelte/lib/CaretRightIcon';
	import CountUp from '#lib/components/CountUp.svelte';
	import EmptyState from '#lib/components/EmptyState.svelte';
	import CategoryIcon from '#lib/components/CategoryIcon.svelte';
	import StatusBadge from '#lib/components/StatusBadge.svelte';
	import { CATEGORY_LABEL, ROLE_LABEL, formatDate, formatRupiah } from '#lib/labels.ts';
	import { api } from '#lib/services/api.ts';
	import { auth, notifyError } from '#lib/session.svelte.ts';
	import type { Reimbursement, Role, Status, Summary } from '#lib/types/index.ts';

	type Dashboard = Summary & { recent: Reimbursement[] };

	let data = $state<Dashboard | null>(null);

	// Status yang paling relevan untuk tiap role.
	const FOCUS: Record<Role, Status[]> = {
		employee: ['submitted', 'revision_required', 'pending_approval', 'paid'],
		admin_transport: ['submitted', 'under_review', 'pending_approval', 'rejected'],
		admin_consumption: ['submitted', 'under_review', 'pending_approval', 'rejected'],
		approver: ['pending_approval', 'approved', 'rejected', 'paid'],
		finance: ['approved', 'processing_payment', 'paid'],
		super_admin: ['submitted', 'pending_approval', 'approved', 'paid']
	};

	// Antrean kerja tiap role: halaman tujuan dan status yang menunggu tindakannya.
	const QUEUE: Record<Role, { href: string; statuses: Status[]; label: string }> = {
		employee: { href: '/reimburse', statuses: ['revision_required'], label: 'Lihat riwayat' },
		admin_transport: { href: '/verification', statuses: ['submitted', 'under_review'], label: 'Buka verifikasi' },
		admin_consumption: { href: '/verification', statuses: ['submitted', 'under_review'], label: 'Buka verifikasi' },
		approver: { href: '/approval', statuses: ['pending_approval'], label: 'Buka persetujuan' },
		finance: { href: '/finance', statuses: ['approved', 'processing_payment'], label: 'Buka pembayaran' },
		super_admin: { href: '/reimburse', statuses: [], label: 'Semua pengajuan' }
	};

	// Tahap untuk bilah pipeline; urutan = urutan segmen.
	const STAGES: { label: string; statuses: Status[]; color: string }[] = [
		{ label: 'Dalam proses', statuses: ['submitted', 'under_review', 'pending_approval', 'approved', 'processing_payment'], color: 'bg-ink' },
		{ label: 'Perlu revisi', statuses: ['revision_required'], color: 'bg-warn' },
		{ label: 'Dibayar', statuses: ['paid'], color: 'bg-lime' },
		{ label: 'Ditolak', statuses: ['rejected'], color: 'bg-danger' },
		{ label: 'Draft', statuses: ['draft'], color: 'bg-line-strong' }
	];

	$effect(() => {
		api
			.get<Dashboard>('/dashboard')
			.then((d) => (data = d))
			.catch(notifyError);
	});

	const role = $derived(auth.user!.role);
	const queue = $derived(QUEUE[role]);
	const firstName = $derived(auth.user!.name.split(' ')[0]);
	const count = (statuses: Status[]) => statuses.reduce((n, s) => n + (data?.by_status[s]?.count ?? 0), 0);

	const now = new Date();
	const hour = now.getHours();
	const greeting = hour < 11 ? 'Selamat pagi' : hour < 15 ? 'Selamat siang' : hour < 19 ? 'Selamat sore' : 'Selamat malam';
	const today = now.toLocaleDateString('id-ID', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

	const stages = $derived(STAGES.map((s) => ({ ...s, count: count(s.statuses) })).filter((s) => s.count > 0));
	const waiting = $derived(count(queue.statuses));
	const summary = $derived.by(() => {
		if (!data) return '';
		if (role === 'employee') {
			const active = count(STAGES[0].statuses);
			if (waiting) return `${waiting} pengajuan dikembalikan dan perlu Anda perbaiki.`;
			return active ? `${active} pengajuan sedang berjalan.` : 'Tidak ada pengajuan yang sedang berjalan.';
		}
		if (role === 'super_admin') return 'Ringkasan seluruh pengajuan reimburse.';
		const what = role === 'approver' ? 'persetujuan' : role === 'finance' ? 'pembayaran' : 'verifikasi';
		return waiting ? `${waiting} pengajuan menunggu ${what} Anda.` : `Tidak ada pengajuan yang menunggu ${what}.`;
	});
</script>

<header class="mb-8 flex flex-wrap items-end justify-between gap-x-6 gap-y-5 lg:mb-10">
	<div>
		<p class="eyebrow reveal">{today} · {ROLE_LABEL[role]}</p>
		<h1 class="display reveal mt-3 text-[2.4rem] text-ink sm:text-[3.25rem]" style="--d: 40ms">
			{greeting}, <span class="mark">{firstName}</span>.
		</h1>
		<p class="reveal mt-3 min-h-6 text-[15px] text-muted" style="--d: 80ms">{summary}</p>
	</div>
	<!-- Karyawan sudah punya tombol "Ajukan" di header (desktop) dan tab bar (mobile). -->
	{#if role !== 'employee'}
		<div class="reveal flex gap-2" style="--d: 120ms">
			<a href={queue.href} class="group btn btn-secondary btn-lg">
				{queue.label}
				<ArrowRight size={16} class="transition-transform duration-300 ease-spring group-hover:translate-x-1" />
			</a>
		</div>
	{/if}
</header>

{#if !data}
	<div class="grid gap-4 lg:grid-cols-12">
		<div class="panel space-y-4 p-6 lg:col-span-7">
			<div class="skeleton h-3 w-24"></div>
			<div class="skeleton h-14 w-64"></div>
			<div class="skeleton h-3 w-40"></div>
			<div class="grid grid-cols-2 gap-4 pt-8"><div class="skeleton h-16"></div><div class="skeleton h-16"></div></div>
		</div>
		<div class="panel space-y-3 p-6 lg:col-span-5">
			<div class="skeleton h-3 w-28"></div>
			<div class="skeleton h-2.5 w-full rounded-full"></div>
			{#each { length: 4 }, i (i)}<div class="skeleton h-9 w-full"></div>{/each}
		</div>
	</div>
{:else}
	<div class="grid gap-4 lg:grid-cols-12">
		<!-- Total -->
		<section class="panel reveal flex flex-col justify-between gap-10 p-6 sm:p-7 lg:col-span-7" style="--d: 140ms">
			<div>
				<p class="eyebrow">Total nominal pengajuan</p>
				<div class="display num mt-3 text-[2.75rem] text-ink sm:text-[3.75rem]">
					<CountUp value={data.total_amount} format={formatRupiah} />
				</div>
				<p class="mt-2 text-muted">
					<span class="num font-medium text-ink"><CountUp value={data.total_count} /></span> pengajuan tercatat
				</p>
			</div>
			<div class="grid grid-cols-2 gap-3">
				{#each ['transport', 'consumption'] as const as c (c)}
					{@const b = data.by_category[c]}
					{@const share = data.total_amount ? (b?.amount ?? 0) / data.total_amount : 0}
					<div class="group rounded-xl bg-sunken/70 p-4 transition-colors duration-200 hover:bg-sunken">
						<div class="flex items-center gap-2.5">
							<CategoryIcon category={c} size="sm" />
							<span class="text-[13px] font-medium text-ink-2">{CATEGORY_LABEL[c]}</span>
						</div>
						<div class="num mt-3 text-lg font-semibold text-ink">{formatRupiah(b?.amount ?? 0)}</div>
						<div class="mt-0.5 text-[12px] text-muted">{b?.count ?? 0} pengajuan · {Math.round(share * 100)}%</div>
						<div class="mt-3 h-1 overflow-hidden rounded-full bg-line">
							<div class="grow-x h-full rounded-full bg-ink" style="width: {share * 100}%; --d: 400ms"></div>
						</div>
					</div>
				{/each}
			</div>
		</section>

		<!-- Pipeline & status -->
		<section class="panel reveal p-6 sm:p-7 lg:col-span-5" style="--d: 200ms">
			<p class="eyebrow">Status pengajuan</p>
			<div class="mt-4 flex h-2.5 gap-[3px] overflow-hidden rounded-full bg-line" aria-hidden="true">
				{#each stages as s, i (s.label)}
					<div class="grow-x h-full first:rounded-l-full last:rounded-r-full {s.color}"
						style="flex: {s.count} 1 0%; --d: {300 + i * 90}ms"></div>
				{/each}
			</div>
			<div class="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-muted">
				{#each stages as s (s.label)}
					<span class="inline-flex items-center gap-1.5"><span class="size-2 rounded-full {s.color}"></span>{s.label}
						<span class="num font-medium text-ink">{s.count}</span></span
					>
				{:else}
					<span>Belum ada data.</span>
				{/each}
			</div>

			<ul class="mt-5 -mx-2">
				{#each FOCUS[role] as s, i (s)}
					{@const empty = !data.by_status[s]?.count}
					<li class="row-in" style="--d: {260 + i * 50}ms">
						<a href={queue.href}
							class="group flex items-center justify-between gap-3 rounded-xl px-2 py-2.5 transition-[background-color,opacity] duration-150 hover:bg-sunken hover:opacity-100 {empty
								? 'opacity-50'
								: ''}">
							<StatusBadge status={s} />
							<span class="flex items-center gap-3">
								<span class="num text-[12px] text-muted">{formatRupiah(data.by_status[s]?.amount ?? 0)}</span>
								<span class="display num w-8 text-right text-xl text-ink">{data.by_status[s]?.count ?? 0}</span>
								<CaretRight size={14} class="text-faint transition-transform duration-200 group-hover:translate-x-0.5 group-hover:text-ink" />
							</span>
						</a>
					</li>
				{/each}
			</ul>
		</section>

		<!-- Terbaru -->
		<section class="panel reveal overflow-hidden lg:col-span-12" style="--d: 260ms">
			<div class="flex items-center justify-between px-6 pt-5 pb-3">
				<h2 class="display text-xl text-ink">Pengajuan terbaru</h2>
				{#if role === 'employee' || role === 'super_admin'}
					<a href="/reimburse" class="group inline-flex items-center gap-1 text-[13px] font-medium text-muted transition-colors hover:text-ink">
						Lihat semua <ArrowRight size={14} class="transition-transform duration-200 group-hover:translate-x-0.5" />
					</a>
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
				<ul class="px-3 pb-3">
					{#each data.recent as r, i (r.id)}
						<li class="row-in" style="--d: {320 + i * 40}ms">
							<a href="/reimburse/{r.id}"
								class="group grid grid-cols-[auto_1fr_auto] items-center gap-3 rounded-xl px-3 py-3 transition-colors duration-150 hover:bg-sunken/70 sm:grid-cols-[auto_1fr_9rem_8rem_auto]">
								<CategoryIcon category={r.category} />
								<div class="min-w-0">
									<div class="truncate font-medium text-ink">{r.merchant ?? r.description}</div>
									<div class="truncate text-[12.5px] text-muted">
										<span class="code">{r.code}</span> · {role === 'employee' ? formatDate(r.transaction_date) : r.employee.name}
									</div>
								</div>
								<div class="hidden sm:block"><StatusBadge status={r.status} /></div>
								<div class="num text-right font-semibold text-ink">
									{formatRupiah(r.amount)}
									<div class="mt-0.5 font-normal sm:hidden"><StatusBadge status={r.status} /></div>
								</div>
								<CaretRight size={14}
									class="hidden text-faint opacity-0 transition-all duration-200 group-hover:translate-x-0.5 group-hover:opacity-100 sm:block" />
							</a>
						</li>
					{/each}
				</ul>
			{/if}
		</section>
	</div>
{/if}
