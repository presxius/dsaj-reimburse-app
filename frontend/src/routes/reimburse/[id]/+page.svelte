<script lang="ts">
	import { page } from '$app/state';
	import { fly } from 'svelte/transition';
	import ArrowLeft from 'phosphor-svelte/lib/ArrowLeftIcon';
	import Receipt from 'phosphor-svelte/lib/ReceiptIcon';
	import CategoryIcon from '#lib/components/CategoryIcon.svelte';
	import Stamp from '#lib/components/Stamp.svelte';
	import StatusBadge from '#lib/components/StatusBadge.svelte';
	import StatusTracker from '#lib/components/StatusTracker.svelte';
	import {
		ACTION_LABEL,
		CATEGORY_LABEL,
		ROLE_LABEL,
		STATUS_LABEL,
		formatDate,
		formatRupiah
	} from '#lib/labels.ts';
	import { ease, ms } from '#lib/motion.ts';
	import { api } from '#lib/services/api.ts';
	import { auth, notify, notifyError } from '#lib/session.svelte.ts';
	import type { Action, ReimbursementDetail } from '#lib/types/index.ts';

	const NOTE_REQUIRED: Action[] = ['admin_return', 'admin_reject', 'approver_return', 'approver_reject'];
	const DANGER: Action[] = ['admin_reject', 'approver_reject'];
	const WARNING: Action[] = ['admin_return', 'approver_return'];

	let item = $state<ReimbursementDetail | null>(null);
	let notFound = $state(false);
	let note = $state('');
	let busy = $state(false);
	let imgFailed = $state(false);
	let payment = $state({ payment_date: new Date().toLocaleDateString('en-CA'), reference: '', amount: 0 });

	async function load() {
		try {
			item = await api.get<ReimbursementDetail>(`/reimbursements/${page.params.id}`);
			payment.amount = item.amount;
		} catch (e) {
			notFound = true;
			notifyError(e);
		}
	}

	$effect(() => {
		void page.params.id;
		load();
	});

	// "submit" ditangani lewat halaman edit (perlu konfirmasi OCR).
	const actions = $derived((item?.actions ?? []).filter((a) => a !== 'submit'));
	const canEdit = $derived(
		item && auth.user?.id === item.employee.id && ['draft', 'revision_required'].includes(item.status)
	);
	const ocr = $derived(item?.receipt?.ocr ?? null);
	const timeline = $derived(item ? [...item.history].reverse() : []);

	async function run(action: Action) {
		if (!item) return;
		if (NOTE_REQUIRED.includes(action) && !note.trim()) {
			return notify('Alasan / catatan wajib diisi.', 'error');
		}
		if (DANGER.includes(action) && !confirm('Yakin menolak pengajuan ini?')) return;
		busy = true;
		try {
			const body = action === 'mark_paid' ? { ...payment, note } : { note };
			item = await api.post<ReimbursementDetail>(`/reimbursements/${item.id}/actions/${action}`, body);
			note = '';
			notify(`Berhasil: ${ACTION_LABEL[action]}.`);
		} catch (e) {
			notifyError(e);
		} finally {
			busy = false;
		}
	}
</script>

{#snippet row(label: string, value: string)}
	<div class="flex justify-between gap-4 py-1">
		<dt class="text-muted">{label}</dt>
		<dd class="text-right text-fg">{value}</dd>
	</div>
{/snippet}

{#if notFound}
	<p class="card text-muted">Pengajuan tidak ditemukan atau Anda tidak memiliki akses.</p>
{:else if !item}
	<div class="space-y-6">
		<div class="skeleton h-8 w-56"></div>
		<div class="skeleton h-24 w-full rounded-xl"></div>
		<div class="grid gap-6 lg:grid-cols-[1fr_380px]">
			<div class="skeleton h-96 rounded-xl"></div>
			<div class="skeleton h-80 rounded-xl"></div>
		</div>
	</div>
{:else}
	<div class="mb-6 flex flex-wrap items-end justify-between gap-3">
		<div>
			<button
				onclick={() => history.back()}
				class="group mb-2 inline-flex items-center gap-1 text-sm text-muted transition-colors hover:text-fg"
			>
				<ArrowLeft size={14} class="transition-transform duration-200 group-hover:-translate-x-0.5" /> Kembali
			</button>
			<div class="flex items-center gap-3">
				<h1 class="num text-2xl font-semibold">{item.code}</h1>
				<StatusBadge status={item.status} />
			</div>
		</div>
		{#if canEdit}
			<a href="/reimburse/{item.id}/edit" class="btn btn-primary">
				{item.status === 'draft' ? 'Lanjutkan & kirim' : 'Perbaiki pengajuan'}
			</a>
		{/if}
	</div>

	<div class="card mb-6 px-4 py-6 sm:px-8">
		<StatusTracker status={item.status} history={item.history} />
	</div>

	<div class="grid gap-6 lg:grid-cols-[1fr_380px]">
		<div class="space-y-6">
			<div class="card">
				<h2 class="mb-4 font-semibold text-fg">Bukti transaksi</h2>
				{#if item.receipt}
					{#if imgFailed}
						<div class="grid place-items-center gap-2 rounded-lg border border-dashed border-line py-12 text-sm text-faint">
							<Receipt size={28} />
							Gambar struk tidak dapat ditampilkan.
						</div>
					{:else}
					<a
						href="/api/receipts/{item.receipt.id}/file"
						target="_blank"
						rel="noopener"
						class="group block overflow-hidden rounded-lg border border-line bg-subtle"
					>
						<img
							src="/api/receipts/{item.receipt.id}/file"
							alt="Struk {item.code}"
							onerror={() => (imgFailed = true)}
							class="max-h-[32rem] w-full object-contain transition-transform duration-500 ease-out-expo group-hover:scale-[1.02]"
						/>
					</a>
					{/if}
					<p class="mt-2 text-xs text-muted">
						{item.receipt.original_filename}, {(item.receipt.file_size / 1024).toFixed(0)} KB{imgFailed ? '.' : '. Klik untuk memperbesar.'}
					</p>
					{#if ocr}
						<div class="mt-4 rounded-lg bg-subtle p-3 text-sm">
							<div class="mb-1 font-medium text-fg">Data OCR (hanya data bantu)</div>
							{#if ocr.status === 'completed'}
								<dl class="grid grid-cols-[auto_1fr] gap-x-4 gap-y-0.5 text-muted">
									<dt>Merchant</dt><dd class="text-fg">{ocr.merchant ?? '-'}</dd>
									<dt>Tanggal</dt><dd class="text-fg">{ocr.transaction_date ?? '-'}</dd>
									<dt>Total</dt>
									<dd class="num text-fg">{ocr.total_amount != null ? formatRupiah(ocr.total_amount) : '-'}</dd>
								</dl>
								<p class="mt-2 text-xs text-muted">
									{item.ocr_confirmed ? 'Dikonfirmasi karyawan' : 'Belum dikonfirmasi'}{item.ocr_corrected
										? ', ada koreksi atau penambahan manual'
										: ''}
								</p>
							{:else}
								<p class="text-muted">OCR gagal ({ocr.error}); data diisi manual.</p>
							{/if}
						</div>
					{/if}
				{:else}
					<p class="text-sm text-faint">Belum ada bukti transaksi.</p>
				{/if}
			</div>

			<div class="card">
				<h2 class="mb-4 font-semibold text-fg">Riwayat status</h2>
				{#if timeline.length === 0}
					<p class="text-sm text-faint">Belum dikirim.</p>
				{:else}
					<div class="relative">
						<span class="absolute top-2 bottom-2 left-[5px] w-px bg-line" aria-hidden="true"></span>
						<ol class="space-y-5 pl-6">
						{#each timeline as h, i (h.id)}
							<li class="relative text-sm" in:fly|global={{ x: -6, delay: ms(50 * i), duration: ms(260), easing: ease }}>
								<span
									class="absolute top-1 -left-6 h-[11px] w-[11px] rounded-full border-2 {i === 0
										? 'border-accent bg-accent'
										: 'border-line bg-surface'}"
								></span>
								<div class="font-medium text-fg">{STATUS_LABEL[h.to_status]}</div>
								<div class="text-xs text-muted">{h.actor.name}, {ROLE_LABEL[h.actor.role]}</div>
								<div class="num text-xs text-faint">{formatDate(h.created_at, true)}</div>
								{#if h.note}
									<div class="mt-1.5 rounded-lg bg-subtle px-3 py-2 text-fg">“{h.note}”</div>
								{/if}
							</li>
						{/each}
					</ol>
					</div>
				{/if}
			</div>
		</div>

		<div class="space-y-6">
			<div class="slip-wrap">
				<div class="slip text-sm">
					<div class="flex items-center gap-3">
						<CategoryIcon category={item.category} />
						<div class="min-w-0">
							<div class="truncate font-medium">{item.merchant ?? 'Merchant tidak diisi'}</div>
							<div class="text-xs text-muted">{CATEGORY_LABEL[item.category]}</div>
						</div>
					</div>
					<p class="mt-3 text-muted">{item.description}</p>
					<hr class="slip-rule" />
					<dl>
						{@render row('Karyawan', item.employee.name)}
						{@render row('Departemen', item.employee.department ?? '-')}
						{@render row('Tgl transaksi', formatDate(item.transaction_date))}
						{@render row('Dikirim', formatDate(item.submitted_at, true))}
					</dl>
					<hr class="slip-rule" />
					<div class="flex items-baseline justify-between font-mono">
						<span class="text-xs tracking-widest text-muted">TOTAL</span>
						<span class="text-xl font-semibold">{formatRupiah(item.amount)}</span>
					</div>
					{#key item.status}
						<Stamp status={item.status} class="absolute top-5 right-4" />
					{/key}
				</div>
			</div>

			{#if actions.length > 0}
				<div class="card space-y-3 border-accent/50 ring-4 ring-accent-soft">
					<h2 class="font-semibold text-fg">Tindakan</h2>
					{#if actions.includes('mark_paid')}
						<div class="space-y-3">
							<div>
								<label class="label" for="pdate">Tanggal pembayaran *</label>
								<input id="pdate" type="date" class="input" bind:value={payment.payment_date} />
							</div>
							<div>
								<label class="label" for="pref">Referensi transaksi *</label>
								<input id="pref" class="input" placeholder="mis. no. transfer" bind:value={payment.reference} />
							</div>
							<div>
								<label class="label" for="pamt">Nominal dibayar (Rp)</label>
								<input id="pamt" type="number" min="1" class="input num" bind:value={payment.amount} />
							</div>
						</div>
					{/if}
					<div>
						<label class="label" for="note">
							Catatan {actions.some((a) => NOTE_REQUIRED.includes(a)) ? '(wajib untuk revisi/tolak)' : '(opsional)'}
						</label>
						<textarea id="note" rows="3" class="input" bind:value={note}></textarea>
					</div>
					<div class="flex flex-col gap-2">
						{#each actions as a (a)}
							<button
								class="btn {DANGER.includes(a) ? 'btn-danger' : WARNING.includes(a) ? 'btn-warning' : 'btn-primary'}"
								disabled={busy}
								onclick={() => run(a)}>{ACTION_LABEL[a]}</button
							>
						{/each}
					</div>
				</div>
			{/if}

			{#if item.payment}
				<div class="card text-sm">
					<h2 class="mb-3 font-semibold text-fg">Pembayaran</h2>
					<dl>
						{@render row('Status', item.payment.status === 'paid' ? 'Dibayar' : 'Diproses')}
						{@render row('Tanggal', formatDate(item.payment.payment_date))}
						{@render row('Referensi', item.payment.reference ?? '-')}
						{@render row('Nominal', formatRupiah(item.payment.amount))}
						{@render row('Oleh', item.payment.processed_by)}
					</dl>
				</div>
			{/if}
		</div>
	</div>
{/if}
