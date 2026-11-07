<script lang="ts">
	import { page } from '$app/state';
	import ArrowLeft from 'phosphor-svelte/lib/ArrowLeft';
	import StatusBadge from '#lib/components/StatusBadge.svelte';
	import {
		ACTION_LABEL,
		CATEGORY_LABEL,
		ROLE_LABEL,
		STATUS_LABEL,
		formatDate,
		formatRupiah
	} from '#lib/labels.ts';
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

{#if notFound}
	<p class="card text-muted">Pengajuan tidak ditemukan atau Anda tidak memiliki akses.</p>
{:else if !item}
	<p class="text-faint">Memuat...</p>
{:else}
	<div class="mb-6 flex flex-wrap items-center justify-between gap-3">
		<div>
			<button onclick={() => history.back()} class="mb-1 inline-flex items-center gap-1 text-sm text-muted hover:text-fg"><ArrowLeft size={14} /> Kembali</button>
			<h1 class="text-2xl font-semibold tracking-tight">{item.code}</h1>
		</div>
		<div class="flex items-center gap-3">
			<StatusBadge status={item.status} />
			{#if canEdit}
				<a href="/reimburse/{item.id}/edit" class="btn btn-primary">
					{item.status === 'draft' ? 'Lanjutkan & kirim' : 'Perbaiki pengajuan'}
				</a>
			{/if}
		</div>
	</div>

	<div class="grid gap-6 lg:grid-cols-3">
		<div class="space-y-6 lg:col-span-2">
			<div class="card">
				<h2 class="mb-4 font-semibold text-fg">Detail pengajuan</h2>
				<dl class="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
					<div><dt class="text-muted">Karyawan</dt><dd class="font-medium">{item.employee.name}</dd></div>
					<div><dt class="text-muted">Departemen</dt><dd>{item.employee.department ?? '-'}</dd></div>
					<div><dt class="text-muted">Kategori</dt><dd>{CATEGORY_LABEL[item.category]}</dd></div>
					<div><dt class="text-muted">Merchant</dt><dd>{item.merchant ?? '-'}</dd></div>
					<div><dt class="text-muted">Tanggal transaksi</dt><dd>{formatDate(item.transaction_date)}</dd></div>
					<div>
						<dt class="text-muted">Nominal</dt>
						<dd class="text-lg font-semibold text-fg">{formatRupiah(item.amount)}</dd>
					</div>
					<div class="sm:col-span-2"><dt class="text-muted">Keterangan</dt><dd>{item.description}</dd></div>
					<div><dt class="text-muted">Dikirim</dt><dd>{formatDate(item.submitted_at, true)}</dd></div>
				</dl>
			</div>

			<div class="card">
				<h2 class="mb-4 font-semibold text-fg">Bukti transaksi</h2>
				{#if item.receipt}
					<a href="/api/receipts/{item.receipt.id}/file" target="_blank" rel="noopener">
						<img
							src="/api/receipts/{item.receipt.id}/file"
							alt="Struk {item.code}"
							class="max-h-[32rem] w-full rounded-lg border object-contain"
						/>
					</a>
					<p class="mt-2 text-xs text-muted">
						{item.receipt.original_filename} · {(item.receipt.file_size / 1024).toFixed(0)} KB · klik untuk
						memperbesar
					</p>
					{#if ocr}
						<div class="mt-4 rounded-lg bg-subtle p-3 text-sm">
							<div class="mb-1 font-medium text-fg">Data OCR (hanya data bantu)</div>
							{#if ocr.status === 'completed'}
								<p class="text-muted">
									Merchant: {ocr.merchant ?? '-'} · Tanggal: {ocr.transaction_date ?? '-'} · Total:
									{ocr.total_amount != null ? formatRupiah(ocr.total_amount) : '-'}
								</p>
								<p class="mt-1 text-xs text-muted">
									{item.ocr_confirmed ? 'Dikonfirmasi karyawan' : 'Belum dikonfirmasi'}{item.ocr_corrected
										? ' · ada koreksi/penambahan manual'
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
		</div>

		<div class="space-y-6">
			{#if actions.length > 0}
				<div class="card space-y-3 border-accent ring-2 ring-accent-soft">
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
								<input id="pamt" type="number" min="1" class="input" bind:value={payment.amount} />
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
					<dl class="space-y-1">
						<div class="flex justify-between"><dt class="text-muted">Status</dt><dd>{item.payment.status === 'paid' ? 'Dibayar' : 'Diproses'}</dd></div>
						<div class="flex justify-between"><dt class="text-muted">Tanggal</dt><dd>{formatDate(item.payment.payment_date)}</dd></div>
						<div class="flex justify-between"><dt class="text-muted">Referensi</dt><dd>{item.payment.reference ?? '-'}</dd></div>
						<div class="flex justify-between"><dt class="text-muted">Nominal</dt><dd>{formatRupiah(item.payment.amount)}</dd></div>
						<div class="flex justify-between"><dt class="text-muted">Oleh</dt><dd>{item.payment.processed_by}</dd></div>
					</dl>
				</div>
			{/if}

			<div class="card">
				<h2 class="mb-3 font-semibold text-fg">Riwayat status</h2>
				{#if item.history.length === 0}
					<p class="text-sm text-faint">Belum dikirim.</p>
				{:else}
					<ol class="relative space-y-4 border-l border-line pl-4">
						{#each item.history as h (h.id)}
							<li class="text-sm">
								<span class="absolute -left-1.5 mt-1 h-3 w-3 rounded-full bg-accent"></span>
								<div class="font-medium text-fg">{STATUS_LABEL[h.to_status]}</div>
								<div class="text-xs text-muted">
									{h.actor.name} ({ROLE_LABEL[h.actor.role]}) · {formatDate(h.created_at, true)}
								</div>
								{#if h.note}
									<div class="mt-1 rounded bg-subtle px-2 py-1 text-fg">“{h.note}”</div>
								{/if}
							</li>
						{/each}
					</ol>
				{/if}
			</div>
		</div>
	</div>
{/if}
