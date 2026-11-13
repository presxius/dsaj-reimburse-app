<script lang="ts">
	import { page } from '$app/state';
	import ArrowLeft from 'phosphor-svelte/lib/ArrowLeftIcon';
	import ArrowSquareOut from 'phosphor-svelte/lib/ArrowSquareOutIcon';
	import Copy from 'phosphor-svelte/lib/CopyIcon';
	import Check from 'phosphor-svelte/lib/CheckIcon';
	import PencilSimple from 'phosphor-svelte/lib/PencilSimpleIcon';
	import Receipt from 'phosphor-svelte/lib/ReceiptIcon';
	import WarningCircle from 'phosphor-svelte/lib/WarningCircleIcon';
	import CategoryIcon from '#lib/components/CategoryIcon.svelte';
	import StatusBadge from '#lib/components/StatusBadge.svelte';
	import StatusTracker from '#lib/components/StatusTracker.svelte';
	import AmountInput from '#lib/components/AmountInput.svelte';
	import Spinner from '#lib/components/Spinner.svelte';
	import {
		ACTION_LABEL,
		CATEGORY_LABEL,
		DUPLICATE_REASON_LABEL,
		OCR_LOW_CONFIDENCE,
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
	// Penanda status saja, bukan keputusan; tampil sebagai tombol sekunder.
	const SECONDARY: Action[] = ['start_review'];
	const ARM_MS = 3500;

	let item = $state<ReimbursementDetail | null>(null);
	let notFound = $state(false);
	let note = $state('');
	let busy = $state<Action | null>(null);
	let armed = $state<Action | null>(null);
	let noteShake = $state(false);
	let copied = $state(false);
	let imgFailed = $state(false);
	let noteEl = $state<HTMLTextAreaElement>();
	let payment = $state<{ payment_date: string; reference: string; amount: number | null }>({
		payment_date: new Date().toLocaleDateString('en-CA'),
		reference: '',
		amount: 0
	});
	let armTimer: ReturnType<typeof setTimeout> | undefined;

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
	// Urutan tombol: lanjutkan alur dulu, lalu kembalikan, lalu tolak.
	const weight = (a: Action) => (DANGER.includes(a) ? 3 : WARNING.includes(a) ? 2 : SECONDARY.includes(a) ? 1 : 0);
	const sorted = $derived([...actions].sort((a, b) => weight(a) - weight(b)));
	const canEdit = $derived(
		item && auth.user?.id === item.employee.id && ['draft', 'revision_required'].includes(item.status)
	);
	const ocr = $derived(item?.receipt?.ocr ?? null);
	const timeline = $derived(item ? [...item.history].reverse() : []);
	const compare = $derived.by(() => {
		if (!item || ocr?.status !== 'completed') return [];
		const conf = ocr.confidence ?? {};
		return [
			{
				label: 'Merchant',
				ocr: ocr.merchant,
				conf: conf.merchant ?? null,
				final: item.merchant,
				same: (ocr.merchant || null) === (item.merchant || null)
			},
			{
				label: 'Tanggal',
				ocr: ocr.transaction_date ? formatDate(ocr.transaction_date) : null,
				conf: conf.transaction_date ?? null,
				final: formatDate(item.transaction_date),
				same: ocr.transaction_date === item.transaction_date
			},
			{
				label: 'Total',
				ocr: ocr.total_amount != null ? formatRupiah(ocr.total_amount) : null,
				conf: conf.total_amount ?? null,
				final: formatRupiah(item.amount),
				same: ocr.total_amount != null && Number(ocr.total_amount) === Number(item.amount)
			}
		];
	});

	function arm(action: Action) {
		armed = action;
		clearTimeout(armTimer);
		armTimer = setTimeout(() => (armed = null), ARM_MS);
	}

	async function run(action: Action) {
		if (!item) return;
		if (NOTE_REQUIRED.includes(action) && !note.trim()) {
			noteShake = false;
			requestAnimationFrame(() => (noteShake = true));
			noteEl?.focus();
			return notify('Alasan / catatan wajib diisi.', 'error');
		}
		// Penolakan perlu klik kedua dalam beberapa detik, menggantikan dialog confirm().
		if (DANGER.includes(action) && armed !== action) return arm(action);
		armed = null;
		busy = action;
		try {
			const body = action === 'mark_paid' ? { ...payment, note } : { note };
			item = await api.post<ReimbursementDetail>(`/reimbursements/${item.id}/actions/${action}`, body);
			note = '';
			notify(`Berhasil: ${ACTION_LABEL[action]}.`);
		} catch (e) {
			notifyError(e);
		} finally {
			busy = null;
		}
	}

	async function copyCode() {
		if (!item) return;
		try {
			if (navigator.clipboard && isSecureContext) {
				await navigator.clipboard.writeText(item.code);
			} else {
				// Clipboard API hanya ada di HTTPS/localhost; di HTTP pakai cara lama.
				const t = Object.assign(document.createElement('textarea'), { value: item.code });
				document.body.append(t);
				t.select();
				document.execCommand('copy');
				t.remove();
			}
			copied = true;
			setTimeout(() => (copied = false), 1600);
		} catch {
			notify('Kode tidak dapat disalin.', 'error');
		}
	}
</script>

{#snippet row(label: string, value: string)}
	<div class="flex justify-between gap-4 py-2">
		<dt class="text-muted">{label}</dt>
		<dd class="text-right font-medium text-ink">{value}</dd>
	</div>
{/snippet}

{#if notFound}
	<div class="panel p-10 text-center">
		<p class="display text-xl text-ink">Pengajuan tidak ditemukan</p>
		<p class="mt-1.5 text-muted">Pengajuan tidak ada atau Anda tidak memiliki akses.</p>
		<a href="/dashboard" class="btn btn-secondary mt-5">Kembali ke dashboard</a>
	</div>
{:else if !item}
	<div class="space-y-5">
		<div class="skeleton h-3 w-20"></div>
		<div class="skeleton h-12 w-80"></div>
		<div class="skeleton h-28 w-full rounded-2xl"></div>
		<div class="grid gap-5 lg:grid-cols-[1fr_22.5rem]">
			<div class="skeleton h-96 rounded-2xl"></div>
			<div class="skeleton h-80 rounded-2xl"></div>
		</div>
	</div>
{:else}
	<button
		onclick={() => history.back()}
		class="group reveal mb-5 inline-flex items-center gap-1.5 text-[13px] font-medium text-muted transition-colors hover:text-ink"
	>
		<ArrowLeft size={14} class="transition-transform duration-300 ease-spring group-hover:-translate-x-1" /> Kembali
	</button>

	<header class="mb-7 flex flex-wrap items-end justify-between gap-x-8 gap-y-5">
		<div class="min-w-0">
			<div class="reveal flex items-center gap-1.5">
				<span class="eyebrow">{item.code}</span>
				<button class="icon-btn size-7" onclick={copyCode} aria-label="Salin kode pengajuan" title="Salin kode">
					{#if copied}
						<Check size={14} weight="bold" class="text-ok" style="animation: pop-in 320ms var(--spring)" />
					{:else}
						<Copy size={14} />
					{/if}
				</button>
				{#if copied}<span class="text-[12px] text-muted" style="animation: pop-in 260ms var(--ease)">Tersalin</span>{/if}
			</div>
			<h1 class="display reveal mt-1 text-[2.25rem] text-ink sm:text-[2.85rem]" style="--d: 40ms">
				{item.merchant ?? CATEGORY_LABEL[item.category]}
			</h1>
			<div class="reveal mt-3.5 flex flex-wrap items-center gap-x-3 gap-y-2 text-[13.5px] text-muted" style="--d: 80ms">
				<StatusBadge status={item.status} pill />
				<span class="inline-flex items-center gap-2"><CategoryIcon category={item.category} size="sm" /> {CATEGORY_LABEL[item.category]}</span>
				<span class="text-line-strong">/</span>
				<span>{item.employee.name}</span>
				<span class="text-line-strong">/</span>
				<span class="num">{formatDate(item.transaction_date)}</span>
			</div>
		</div>
		<div class="reveal sm:text-right" style="--d: 120ms">
			<p class="eyebrow">Nominal</p>
			<p class="display num mt-1.5 text-[2.5rem] text-ink sm:text-[3rem]">{formatRupiah(item.amount)}</p>
			{#if canEdit}
				<a href="/reimburse/{item.id}/edit" class="group btn btn-primary mt-3">
					<PencilSimple size={15} class="transition-transform duration-300 ease-spring group-hover:-rotate-12" />
					{item.status === 'draft' ? 'Lanjutkan & kirim' : 'Perbaiki pengajuan'}
				</a>
			{/if}
		</div>
	</header>

	{#if item.duplicates?.length}
		<section class="reveal mb-5 flex items-start gap-3 rounded-2xl border border-warn/35 bg-warn/[0.07] p-4 text-[13.5px] text-ink sm:p-5"
			style="--d: 140ms" role="alert">
			<WarningCircle size={20} weight="fill" class="mt-px shrink-0 text-warn" />
			<div class="min-w-0">
				<p class="font-semibold">Kemungkinan pengajuan ganda</p>
				<p class="mt-0.5 text-muted">Pengajuan berikut memiliki struk atau data transaksi yang sama. Periksa sebelum memproses.</p>
				<ul class="mt-2 space-y-1">
					{#each item.duplicates as d (d.id)}
						<li class="flex flex-wrap items-center gap-x-2 gap-y-0.5">
							<a href="/reimburse/{d.id}" class="code font-medium text-ink underline underline-offset-2">{d.code}</a>
							<span class="rounded-full bg-warn/15 px-2 py-0.5 text-[11px] font-semibold text-warn">{DUPLICATE_REASON_LABEL[d.reason]}</span>
							<span class="text-muted">{d.employee} · {formatDate(d.transaction_date)} · <span class="num">{formatRupiah(d.amount)}</span> · {STATUS_LABEL[d.status]}</span>
						</li>
					{/each}
				</ul>
			</div>
		</section>
	{/if}

	<section class="panel reveal mb-5 px-3 py-6 sm:px-8 sm:py-7" style="--d: 160ms">
		<StatusTracker status={item.status} history={item.history} />
	</section>

	<div class="grid gap-5 lg:grid-cols-[minmax(0,1fr)_22.5rem] lg:items-start">
		<div class="space-y-5">
			<section class="panel reveal p-5 sm:p-6" style="--d: 200ms">
				<div class="mb-4 flex items-center justify-between">
					<h2 class="display text-xl text-ink">Bukti transaksi</h2>
					{#if item.receipt && !imgFailed}
						<a href="/api/receipts/{item.receipt.id}/file" target="_blank" rel="noopener"
							class="group inline-flex items-center gap-1 text-[13px] font-medium text-muted transition-colors hover:text-ink">
							Ukuran penuh <ArrowSquareOut size={14} class="transition-transform duration-200 group-hover:-translate-y-px group-hover:translate-x-px" />
						</a>
					{/if}
				</div>
				{#if item.receipt}
					{#if imgFailed}
						<div class="grid place-items-center gap-2 rounded-xl border border-dashed border-line-strong py-14 text-sm text-faint">
							<Receipt size={28} />
							Gambar struk tidak dapat ditampilkan.
						</div>
					{:else}
						<a href="/api/receipts/{item.receipt.id}/file" target="_blank" rel="noopener"
							class="group block overflow-hidden rounded-xl border border-line bg-sunken">
							<img
								src="/api/receipts/{item.receipt.id}/file"
								alt="Struk {item.code}"
								onerror={() => (imgFailed = true)}
								class="max-h-[34rem] w-full object-contain transition-transform duration-700 ease-snap group-hover:scale-[1.025]"
							/>
						</a>
					{/if}
					<p class="mt-2.5 text-[12px] text-muted">
						<span class="code">{item.receipt.original_filename}</span> · {(item.receipt.file_size / 1024).toFixed(0)} KB
					</p>
				{:else}
					<p class="text-sm text-faint">Belum ada bukti transaksi.</p>
				{/if}
			</section>

			{#if ocr}
				<section class="panel reveal p-5 sm:p-6" style="--d: 240ms">
					<div class="mb-4 flex flex-wrap items-center justify-between gap-2">
						<h2 class="display text-xl text-ink">OCR vs diajukan</h2>
						{#if ocr.status === 'completed'}
							<span class="text-[12px] text-muted">
								{item.ocr_confirmed ? 'Dikonfirmasi karyawan' : 'Belum dikonfirmasi'}{item.ocr_corrected ? ' · ada koreksi manual' : ''}
							</span>
						{/if}
					</div>
					{#if ocr.status === 'completed'}
						<div class="overflow-x-auto">
							<table class="table text-[13.5px]">
								<thead><tr><th class="pl-0!">Field</th><th>Hasil OCR</th><th>Diajukan</th><th class="w-24"></th></tr></thead>
								<tbody>
									{#each compare as c, i (c.label)}
										<tr class="row-in" style="--d: {280 + i * 60}ms">
											<td class="pl-0! text-muted">{c.label}</td>
											<td class="{c.ocr ? 'text-ink-2' : 'text-faint italic'} {c.label === 'Total' ? 'num' : ''}">
												{c.ocr ?? 'tidak terbaca'}
												{#if c.ocr && c.conf != null}
													<span class="num ml-1 text-[11px] {c.conf < OCR_LOW_CONFIDENCE ? 'font-semibold text-warn' : 'text-faint'}"
														title="Skor keyakinan OCR">{Math.round(c.conf * 100)}%</span>
												{/if}
											</td>
											<td class="font-medium text-ink {c.label === 'Total' ? 'num' : ''}">{c.final ?? '-'}</td>
											<td class="text-right">
												{#if c.same}
													<span class="inline-flex items-center gap-1 rounded-full bg-lime px-2 py-0.5 text-[11px] font-semibold text-on-lime"><Check size={11} weight="bold" /> Sama</span>
												{:else if c.ocr}
													<span class="inline-flex rounded-full bg-warn/15 px-2 py-0.5 text-[11px] font-semibold text-warn">Dikoreksi</span>
												{:else}
													<span class="inline-flex rounded-full bg-sunken px-2 py-0.5 text-[11px] font-medium text-muted">Manual</span>
												{/if}
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{:else}
						<p class="text-[13.5px] text-muted">OCR gagal ({ocr.error ?? 'tidak diketahui'}); data diisi manual oleh karyawan.</p>
					{/if}
				</section>
			{/if}

			<section class="panel reveal p-5 sm:p-6" style="--d: 280ms">
				<h2 class="display mb-5 text-xl text-ink">Riwayat</h2>
				{#if timeline.length === 0}
					<p class="text-sm text-faint">Belum dikirim.</p>
				{:else}
					<ol class="relative">
						{#each timeline as h, i (h.id)}
							<li class="row-in relative flex gap-4 pb-6 last:pb-0" style="--d: {320 + i * 60}ms">
								{#if i < timeline.length - 1}
									<span class="absolute top-5 bottom-0 left-[5px] w-px bg-line" aria-hidden="true"></span>
								{/if}
								<!-- Simpul timeline kecil; makna status dibawa glyph pada badge. -->
								<span class="relative mt-[5px] size-[11px] shrink-0 rounded-full border-2 {i === 0
									? 'border-lime-deep bg-lime'
									: 'border-line-strong bg-surface'}"
									style={i === 0 ? 'animation: halo 1.8s var(--ease) 3' : ''}></span>
								<div class="min-w-0 flex-1">
									<div class="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
										<StatusBadge status={h.to_status} />
										<span class="num text-[12px] text-faint">{formatDate(h.created_at, true)}</span>
									</div>
									<p class="mt-1 text-[13px] text-muted">
										<span class="text-ink-2">{h.actor.name}</span> · {ROLE_LABEL[h.actor.role]}
									</p>
									{#if h.note}
										<p class="mt-2 rounded-xl rounded-tl-sm bg-sunken px-3.5 py-2.5 text-[13.5px] text-ink">{h.note}</p>
									{/if}
								</div>
							</li>
						{/each}
					</ol>
				{/if}
			</section>
		</div>

		<aside class="space-y-5 lg:sticky lg:top-24">
			{#if actions.length > 0}
				<section class="panel reveal p-5 ring-1 ring-ink" style="--d: 200ms">
					<p class="eyebrow flex items-center gap-2 text-ink">
						<span class="size-2 rounded-full bg-lime" style="animation: halo 1.8s var(--ease) infinite"></span>
						Menunggu tindakan Anda
					</p>
					<div class="mt-4 space-y-4">
						{#if actions.includes('mark_paid')}
							<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
								<div>
									<label class="label" for="pdate">Tanggal pembayaran <span class="text-danger">*</span></label>
									<input id="pdate" type="date" class="input" bind:value={payment.payment_date} />
								</div>
								<div>
									<label class="label" for="pref">Referensi transaksi <span class="text-danger">*</span></label>
									<input id="pref" class="input" placeholder="mis. no. transfer" bind:value={payment.reference} />
								</div>
							</div>
							<div>
								<label class="label" for="pamt">Nominal dibayar</label>
								<AmountInput id="pamt" bind:value={payment.amount} />
							</div>
						{/if}
						<div class={noteShake ? 'shake' : ''}>
							<label class="label" for="note">
								Catatan
								<span class="font-normal text-muted">
									{actions.some((a) => NOTE_REQUIRED.includes(a)) ? '· wajib untuk revisi/tolak' : '· opsional'}
								</span>
							</label>
							<textarea id="note" rows="3" class="input" bind:value={note} bind:this={noteEl}
								placeholder="Tulis alasan atau catatan untuk karyawan…"></textarea>
						</div>
						<div class="flex flex-col gap-2">
							{#each sorted as a (a)}
								{@const danger = DANGER.includes(a)}
								<button
									class="relative overflow-hidden btn {danger
										? armed === a
											? 'btn-danger'
											: 'btn-secondary text-danger hover:border-danger/50!'
										: WARNING.includes(a)
											? 'btn-warn'
											: SECONDARY.includes(a)
												? 'btn-secondary'
												: 'btn-primary'}"
									disabled={!!busy}
									onclick={() => run(a)}
								>
									{#if busy === a}<Spinner size={14} />{/if}
									{armed === a ? 'Klik sekali lagi untuk menolak' : ACTION_LABEL[a]}
									{#if armed === a}
										<span class="absolute bottom-0 left-0 h-[3px] w-full origin-left bg-white/55"
											style="animation: toast-timer {ARM_MS}ms linear forwards" aria-hidden="true"></span>
									{/if}
								</button>
							{/each}
						</div>
					</div>
				</section>
			{/if}

			<section class="panel reveal p-5" style="--d: 240ms">
				<p class="eyebrow">Keperluan</p>
				<p class="mt-2 text-[15px] leading-relaxed text-ink">{item.description}</p>
				<dl class="mt-4 divide-y divide-line border-t border-line text-[13.5px]">
					{@render row('Karyawan', item.employee.name)}
					{@render row('Departemen', item.employee.department ?? '-')}
					{@render row('Tanggal transaksi', formatDate(item.transaction_date))}
					{@render row('Dikirim', formatDate(item.submitted_at, true))}
				</dl>
			</section>

			{#if item.payment}
				<section class="panel reveal p-5" style="--d: 280ms">
					<div class="flex items-center justify-between">
						<p class="eyebrow">Pembayaran</p>
						<StatusBadge status={item.payment.status === 'paid' ? 'paid' : 'processing_payment'} />
					</div>
					<dl class="mt-3 divide-y divide-line text-[13.5px]">
						{@render row('Tanggal', formatDate(item.payment.payment_date))}
						{@render row('Referensi', item.payment.reference ?? '-')}
						{@render row('Nominal', formatRupiah(item.payment.amount))}
						{@render row('Oleh', item.payment.processed_by)}
					</dl>
				</section>
			{/if}
		</aside>
	</div>
{/if}
