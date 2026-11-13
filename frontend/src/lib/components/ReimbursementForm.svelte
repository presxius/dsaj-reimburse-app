<script lang="ts">
	import { untrack } from 'svelte';
	import { slide } from 'svelte/transition';
	import UploadSimple from 'phosphor-svelte/lib/UploadSimpleIcon';
	import ArrowsClockwise from 'phosphor-svelte/lib/ArrowsClockwiseIcon';
	import ArrowRight from 'phosphor-svelte/lib/ArrowRightIcon';
	import CaretRight from 'phosphor-svelte/lib/CaretRightIcon';
	import Check from 'phosphor-svelte/lib/CheckIcon';
	import WarningCircle from 'phosphor-svelte/lib/WarningCircleIcon';
	import Car from 'phosphor-svelte/lib/CarIcon';
	import ForkKnife from 'phosphor-svelte/lib/ForkKnifeIcon';
	import Segmented from './Segmented.svelte';
	import AmountInput from './AmountInput.svelte';
	import Spinner from './Spinner.svelte';
	import { api } from '#lib/services/api.ts';
	import { OCR_LOW_CONFIDENCE, STATUS_LABEL, formatDate, formatRupiah } from '#lib/labels.ts';
	import { ease, ms } from '#lib/motion.ts';
	import { notify, notifyError } from '#lib/session.svelte.ts';
	import type {
		Category,
		DuplicateMatch,
		OcrField,
		Receipt,
		ReimbursementDetail,
		UploadedReceipt
	} from '#lib/types/index.ts';

	let {
		initial,
		onsaved
	}: { initial?: ReimbursementDetail; onsaved: (r: ReimbursementDetail) => void } = $props();

	const MAX_SIZE = 5 * 1024 * 1024;
	const today = new Date().toLocaleDateString('en-CA');
	const CATEGORIES: { value: Category; label: string; icon: typeof Car }[] = [
		{ value: 'transport', label: 'Transportasi', icon: Car },
		{ value: 'consumption', label: 'Konsumsi', icon: ForkKnife }
	];

	// Nilai awal hanya dipakai sekali saat form dibuat.
	const init = untrack(() => initial);
	let category = $state<Category>(init?.category ?? 'transport');
	let merchant = $state(init?.merchant ?? '');
	let transactionDate = $state(init?.transaction_date ?? '');
	let amount = $state<number | null>(init?.amount ?? null);
	let description = $state(init?.description ?? '');
	let receipt = $state<Receipt | null>(init?.receipt ?? null);
	let previewUrl = $state<string | null>(init?.receipt ? `/api/receipts/${init.receipt.id}/file` : null);
	let useOcr = $state(true);
	let uploading = $state(false);
	let saving = $state<'draft' | 'submit' | null>(null);
	let ocrConfirmed = $state(false);
	let fromOcr = $state<Record<string, boolean>>({});
	let duplicates = $state<DuplicateMatch[]>([]);
	let dragging = $state(false);
	let fileInput: HTMLInputElement;

	const ocr = $derived(receipt?.ocr ?? null);
	const confidence = (f: OcrField) => ocr?.confidence?.[f] ?? null;
	const isLow = (f: OcrField) => {
		const c = confidence(f);
		return c != null && c < OCR_LOW_CONFIDENCE;
	};
	const ocrRows = $derived.by((): { k: string; f: OcrField; v: string | null }[] => {
		if (!ocr) return [];
		return [
			{ k: 'Merchant', f: 'merchant', v: ocr.merchant },
			{ k: 'Tanggal', f: 'transaction_date', v: ocr.transaction_date ? formatDate(ocr.transaction_date) : null },
			{ k: 'Total', f: 'total_amount', v: ocr.total_amount != null ? formatRupiah(ocr.total_amount) : null }
		];
	});
	const anyLow = $derived(ocrRows.some((r) => r.v && isLow(r.f)));
	const needsConfirm = $derived(ocr?.status === 'completed');
	const busy = $derived(!!saving || uploading);

	function onDrop(e: DragEvent) {
		e.preventDefault();
		dragging = false;
		const file = e.dataTransfer?.files[0];
		if (file && !uploading) handleFile(file);
	}

	async function handleFile(file: File) {
		if (!['image/jpeg', 'image/png'].includes(file.type)) {
			notify('Format file harus JPG, JPEG, atau PNG.', 'error');
			fileInput.value = '';
			return;
		}
		if (file.size > MAX_SIZE) {
			notify('Ukuran file maksimal 5 MB.', 'error');
			fileInput.value = '';
			return;
		}
		previewUrl = URL.createObjectURL(file);
		uploading = true;
		ocrConfirmed = false;
		fromOcr = {};
		duplicates = [];
		try {
			const fd = new FormData();
			fd.append('file', file);
			const uploaded = await api.post<UploadedReceipt>(useOcr ? '/ocr/scan' : '/receipts', fd);
			receipt = uploaded;
			// Saat merevisi, pengajuan ini sendiri bukan duplikat.
			duplicates = (uploaded.duplicates ?? []).filter((d) => d.id !== init?.id);
			const r = uploaded.ocr;
			if (r?.status === 'completed') {
				// Isi hanya field yang berhasil dibaca; sisanya biarkan untuk diisi manual.
				if (r.merchant) merchant = r.merchant;
				if (r.transaction_date) transactionDate = r.transaction_date;
				if (r.total_amount != null) amount = r.total_amount;
				fromOcr = {
					merchant: !!r.merchant,
					date: !!r.transaction_date,
					amount: r.total_amount != null
				};
				notify('Struk terbaca. Periksa kembali hasil OCR sebelum mengirim.');
			} else if (r?.status === 'failed') {
				notify('OCR gagal. Silakan isi formulir secara manual.', 'error');
			}
		} catch (err) {
			receipt = null;
			previewUrl = null;
			fileInput.value = '';
			notifyError(err);
		} finally {
			uploading = false;
		}
	}

	async function save(submit: boolean) {
		if (submit && !receipt) return notify('Bukti transaksi wajib dilampirkan.', 'error');
		if (submit && needsConfirm && !ocrConfirmed)
			return notify('Centang konfirmasi pemeriksaan hasil OCR.', 'error');
		saving = submit ? 'submit' : 'draft';
		try {
			const body = {
				category,
				merchant,
				transaction_date: transactionDate,
				amount,
				description,
				receipt_id: receipt?.id ?? null,
				submit,
				ocr_confirmed: ocrConfirmed
			};
			const r = init
				? await api.put<ReimbursementDetail>(`/reimbursements/${init.id}`, body)
				: await api.post<ReimbursementDetail>('/reimbursements', body);
			notify(submit ? `Pengajuan ${r.code} berhasil dikirim.` : 'Draft tersimpan.');
			onsaved(r);
		} catch (err) {
			notifyError(err);
		} finally {
			saving = null;
		}
	}

	const dragHandlers = {
		ondragenter: (e: DragEvent) => {
			e.preventDefault();
			dragging = true;
		},
		ondragover: (e: DragEvent) => e.preventDefault(),
		ondragleave: (e: DragEvent & { currentTarget: HTMLElement }) => {
			if (!e.currentTarget.contains(e.relatedTarget as Node)) dragging = false;
		},
		ondrop: onDrop
	};
</script>

{#snippet step(n: string, title: string)}
	<h2 class="flex items-center gap-3">
		<span class="code grid size-7 place-items-center rounded-lg bg-chip text-[11px] text-on-chip">{n}</span>
		<span class="display text-[1.35rem] text-ink">{title}</span>
	</h2>
{/snippet}

{#snippet ocrTag(key: string, field: OcrField)}
	{#if fromOcr[key]}
		{#if isLow(field)}
			<span class="tag-ocr tag-ocr-low"
				title="OCR kurang yakin ({Math.round((confidence(field) ?? 0) * 100)}%). Cocokkan dengan struk.">OCR · cek</span>
		{:else}
			<span class="tag-ocr" title="Diisi dari hasil OCR">OCR</span>
		{/if}
	{/if}
{/snippet}

<form
	class="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.08fr)] lg:items-start"
	onsubmit={(e) => {
		e.preventDefault();
		save(true);
	}}
>
	<!-- Kolom kiri: struk -->
	<section class="panel reveal p-5 sm:p-6 lg:sticky lg:top-24" style="--d: 120ms">
		<div class="flex flex-wrap items-center justify-between gap-3">
			{@render step('01', 'Bukti transaksi')}
			<label class="flex cursor-pointer items-center gap-2.5 text-[13px] text-muted select-none">
				Baca otomatis (OCR)
				<button type="button" role="switch" aria-checked={useOcr} class="switch" onclick={() => (useOcr = !useOcr)}
					aria-label="Baca struk otomatis dengan OCR"></button>
			</label>
		</div>

		<input
			bind:this={fileInput}
			id="receipt-file"
			type="file"
			accept="image/jpeg,image/png"
			class="peer sr-only"
			onchange={(e) => {
				const f = e.currentTarget.files?.[0];
				if (f) handleFile(f);
			}}
			disabled={uploading}
		/>

		<div class="mt-5 rounded-2xl peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-ink" {...dragHandlers}>
			{#if !previewUrl}
				<label
					for="receipt-file"
					class="group relative flex min-h-[20rem] cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-[1.5px] border-dashed px-6 text-center transition-[background-color,border-color,transform] duration-300 ease-snap {dragging
						? 'scale-[1.015] border-ink bg-lime/20'
						: 'border-line-strong hover:border-faint hover:bg-sunken/60'}"
				>
					<span
						class="grid size-14 place-items-center rounded-2xl bg-chip text-on-chip shadow-pop transition-transform duration-500 ease-spring group-hover:-translate-y-1 group-hover:-rotate-6 {dragging
							? '-translate-y-2 scale-110 -rotate-6'
							: ''}"
					>
						<UploadSimple size={26} weight="bold" />
					</span>
					<span class="display mt-2 text-xl text-ink">
						{dragging ? 'Lepaskan untuk mengunggah' : 'Tarik foto struk ke sini'}
					</span>
					<span class="text-sm text-muted">
						atau <span class="font-medium text-ink underline decoration-line-strong decoration-2 underline-offset-4 transition-colors group-hover:decoration-lime-deep">pilih dari perangkat</span>
					</span>
					<span class="eyebrow mt-3">JPG · PNG · maks 5 MB</span>
				</label>
			{:else}
				<div class="relative overflow-hidden rounded-2xl border border-line bg-sunken {dragging ? 'ring-2 ring-ink' : ''}">
					<img
						src={previewUrl}
						alt="Pratinjau struk"
						class="max-h-[30rem] w-full object-contain transition-[filter,transform] duration-700 ease-snap {uploading
							? 'scale-[1.015] brightness-[0.82] saturate-50'
							: ''}"
					/>
					{#if uploading && useOcr}<div class="scan-beam"></div>{/if}
					{#if uploading}
						<div class="absolute inset-x-0 bottom-4 flex justify-center" role="status">
							<span class="inline-flex items-center gap-2 rounded-full bg-primary px-3.5 py-1.5 text-[13px] font-medium text-on-primary shadow-float">
								<Spinner size={14} />
								{useOcr ? 'Membaca struk…' : 'Mengunggah…'}
							</span>
						</div>
					{:else}
						<label for="receipt-file" class="group btn btn-secondary btn-sm absolute top-3 right-3 cursor-pointer">
							<ArrowsClockwise size={14} class="transition-transform duration-500 ease-spring group-hover:rotate-180" />
							Ganti struk
						</label>
					{/if}
				</div>
			{/if}
		</div>

		{#if ocr && !uploading}
			<div class="mt-4" transition:slide={{ duration: ms(320), easing: ease }}>
				{#if ocr.status === 'completed'}
					<div class="rounded-xl border border-line bg-sunken/60 p-4">
						<div class="mb-3 flex items-center justify-between">
							<span class="eyebrow">Hasil pembacaan OCR</span>
							<span class="tag-ocr">DRAFT</span>
						</div>
						<dl class="space-y-2 text-[13.5px]">
							{#each ocrRows as { k, f, v }, i (k)}
								{@const c = v ? confidence(f) : null}
								<div class="row-in flex items-center gap-3" style="--d: {i * 70}ms">
									<span class="grid size-5 shrink-0 place-items-center rounded-full {v ? (isLow(f) ? 'bg-warn/20 text-warn' : 'bg-lime text-on-lime') : 'bg-line text-faint'}">
										{#if v && isLow(f)}<WarningCircle size={12} weight="bold" />{:else if v}<Check size={11} weight="bold" />{:else}<span class="h-[1.5px] w-2 rounded bg-current"></span>{/if}
									</span>
									<dt class="w-20 shrink-0 text-muted">{k}</dt>
									<dd class="min-w-0 flex-1 truncate {v ? 'font-medium text-ink' : 'text-faint italic'} {k === 'Total' ? 'num' : ''}">
										{v ?? 'tidak terbaca'}
									</dd>
									{#if c != null}
										<span class="num shrink-0 text-[11.5px] {isLow(f) ? 'font-semibold text-warn' : 'text-faint'}"
											title="Skor keyakinan OCR">{Math.round(c * 100)}%</span>
									{/if}
								</div>
							{/each}
						</dl>
						{#if anyLow}
							<p class="mt-3 text-[12px] text-warn">Field bertanda kuning kurang jelas terbaca. Cocokkan dengan struk.</p>
						{/if}
						{#if ocr.raw_text}
							<details class="group mt-3 border-t border-line pt-3">
								<summary class="flex cursor-pointer list-none items-center gap-1.5 text-[12px] font-medium text-muted transition-colors hover:text-ink">
									<CaretRight size={12} class="transition-transform duration-200 group-open:rotate-90" /> Teks mentah
								</summary>
								<pre class="code mt-2 max-h-48 overflow-auto rounded-lg bg-surface p-3 text-[11.5px] leading-relaxed whitespace-pre-wrap text-ink-2">{ocr.raw_text}</pre>
							</details>
						{/if}
					</div>
				{:else}
					<div class="flex items-start gap-3 rounded-xl border border-warn/35 bg-warn/[0.07] p-4 text-[13.5px] text-ink">
						<WarningCircle size={18} weight="fill" class="mt-px shrink-0 text-warn" />
						<p>OCR tidak berhasil: {ocr.error ?? 'gambar tidak dapat diproses'}. Silakan isi formulir secara manual.</p>
					</div>
				{/if}
			</div>
		{/if}

		{#if duplicates.length > 0 && !uploading}
			<div class="mt-4 flex items-start gap-3 rounded-xl border border-warn/35 bg-warn/[0.07] p-4 text-[13.5px] text-ink"
				transition:slide={{ duration: ms(320), easing: ease }}>
				<WarningCircle size={18} weight="fill" class="mt-px shrink-0 text-warn" />
				<div>
					<p class="font-semibold">Struk ini sudah pernah diajukan.</p>
					<ul class="mt-1 space-y-0.5 text-muted">
						{#each duplicates as d (d.id)}
							<li>
								<a href="/reimburse/{d.id}" target="_blank" rel="noopener" class="code font-medium text-ink underline underline-offset-2">{d.code}</a>
								· {STATUS_LABEL[d.status]} · <span class="num">{formatRupiah(d.amount)}</span>
							</li>
						{/each}
					</ul>
					<p class="mt-1.5 text-[12.5px] text-muted">Pastikan ini bukan pengajuan ganda. Admin juga akan melihat peringatan ini.</p>
				</div>
			</div>
		{/if}
	</section>

	<!-- Kolom kanan: data pengajuan -->
	<section class="panel reveal p-5 sm:p-6" style="--d: 180ms">
		{@render step('02', 'Detail pengeluaran')}

		<div class="mt-6 space-y-5">
			<div>
				<span class="label">Kategori</span>
				<Segmented options={CATEGORIES} bind:value={category} label="Kategori" />
			</div>
			<div>
				<label class="label" for="merchant">Merchant / penyedia {@render ocrTag('merchant', 'merchant')}</label>
				<input id="merchant" class="input {fromOcr.merchant ? 'ocr-flash' : ''}" bind:value={merchant}
					placeholder="mis. Blue Taxi, Kopi Senja" />
			</div>
			<div class="grid gap-5 sm:grid-cols-2">
				<div>
					<label class="label" for="date">Tanggal transaksi <span class="text-danger">*</span> {@render ocrTag('date', 'transaction_date')}</label>
					<input id="date" type="date" class="input {fromOcr.date ? 'ocr-flash' : ''}" max={today}
						bind:value={transactionDate} required />
				</div>
				<div>
					<label class="label" for="amount">Nominal <span class="text-danger">*</span> {@render ocrTag('amount', 'total_amount')}</label>
					<AmountInput id="amount" bind:value={amount} required class={fromOcr.amount ? 'ocr-flash' : ''} />
				</div>
			</div>
			<div>
				<label class="label" for="desc">Keterangan / keperluan <span class="text-danger">*</span></label>
				<textarea id="desc" rows="3" class="input" bind:value={description} required
					placeholder="mis. Taksi ke kantor klien PT ABC untuk meeting"></textarea>
			</div>

			{#if needsConfirm}
				<label
					class="flex cursor-pointer items-start gap-3 rounded-xl border p-4 text-[13.5px] text-ink-2 transition-[background-color,border-color] duration-300 {ocrConfirmed
						? 'border-lime-deep bg-lime/25'
						: 'border-warn/40 bg-warn/[0.07]'}"
					transition:slide={{ duration: ms(320), easing: ease }}
				>
					<input type="checkbox" class="check mt-0.5" bind:checked={ocrConfirmed} />
					<span>
						<span class="font-semibold text-ink">Saya sudah memeriksa hasil OCR.</span>
						Merchant, tanggal, dan nominal sudah saya cocokkan dengan struk asli.
					</span>
				</label>
			{/if}
		</div>

		<div class="mt-7 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-5">
			<p class="text-[12px] text-muted"><span class="text-danger">*</span> wajib diisi</p>
			<div class="flex gap-2">
				<button type="button" class="btn btn-secondary" disabled={busy} onclick={() => save(false)}>
					{#if saving === 'draft'}<Spinner size={14} />{/if} Simpan draft
				</button>
				<button type="submit" class="group btn btn-primary" disabled={busy}>
					{#if saving === 'submit'}
						<Spinner size={14} /> Mengirim…
					{:else}
						Kirim pengajuan
						<ArrowRight size={15} weight="bold" class="transition-transform duration-300 ease-spring group-hover:translate-x-1" />
					{/if}
				</button>
			</div>
		</div>
	</section>
</form>
