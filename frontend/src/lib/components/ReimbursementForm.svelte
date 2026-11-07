<script lang="ts">
	import { untrack } from 'svelte';
	import { api } from '#lib/services/api.ts';
	import { formatRupiah } from '#lib/labels.ts';
	import { notify, notifyError } from '#lib/session.svelte.ts';
	import type { Category, Receipt, ReimbursementDetail } from '#lib/types/index.ts';

	let {
		initial,
		onsaved
	}: { initial?: ReimbursementDetail; onsaved: (r: ReimbursementDetail) => void } = $props();

	const MAX_SIZE = 5 * 1024 * 1024;
	const today = new Date().toLocaleDateString('en-CA');

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
	let saving = $state(false);
	let ocrConfirmed = $state(false);
	let fromOcr = $state<Record<string, boolean>>({});

	const ocr = $derived(receipt?.ocr ?? null);
	const needsConfirm = $derived(ocr?.status === 'completed');

	async function onFile(e: Event) {
		const input = e.currentTarget as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;
		if (!['image/jpeg', 'image/png'].includes(file.type)) {
			notify('Format file harus JPG, JPEG, atau PNG.', 'error');
			input.value = '';
			return;
		}
		if (file.size > MAX_SIZE) {
			notify('Ukuran file maksimal 5 MB.', 'error');
			input.value = '';
			return;
		}
		previewUrl = URL.createObjectURL(file);
		uploading = true;
		ocrConfirmed = false;
		fromOcr = {};
		try {
			const fd = new FormData();
			fd.append('file', file);
			receipt = await api.post<Receipt>(useOcr ? '/ocr/scan' : '/receipts', fd);
			const r = receipt.ocr;
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
			input.value = '';
			notifyError(err);
		} finally {
			uploading = false;
		}
	}

	async function save(submit: boolean) {
		if (submit && !receipt) return notify('Bukti transaksi wajib dilampirkan.', 'error');
		if (submit && needsConfirm && !ocrConfirmed)
			return notify('Centang konfirmasi pemeriksaan hasil OCR.', 'error');
		saving = true;
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
			saving = false;
		}
	}
</script>

{#snippet ocrTag(key: string)}
	{#if fromOcr[key]}
		<span class="ml-1 rounded bg-violet-100 px-1.5 py-0.5 text-[10px] font-semibold text-violet-700"
			>dari OCR</span
		>
	{/if}
{/snippet}

<form
	class="grid gap-6 lg:grid-cols-2"
	onsubmit={(e) => {
		e.preventDefault();
		save(true);
	}}
>
	<!-- Kolom kiri: struk -->
	<div class="card space-y-4">
		<h2 class="font-semibold text-slate-800">1. Bukti transaksi</h2>
		<label class="flex items-center gap-2 text-sm text-slate-600">
			<input type="checkbox" bind:checked={useOcr} />
			Baca struk otomatis dengan OCR
		</label>
		<input
			type="file"
			accept="image/jpeg,image/png"
			class="block w-full text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-brand-50 file:px-4 file:py-2 file:text-brand-700"
			onchange={onFile}
			disabled={uploading}
		/>
		<p class="text-xs text-slate-500">Format JPG/JPEG/PNG, maksimal 5 MB.</p>

		{#if uploading}
			<p class="text-sm text-brand-600">{useOcr ? 'Mengunggah dan membaca struk...' : 'Mengunggah...'}</p>
		{/if}

		{#if previewUrl}
			<img src={previewUrl} alt="Pratinjau struk" class="max-h-96 w-full rounded-lg border object-contain" />
		{/if}

		{#if ocr}
			<div
				class="rounded-lg border p-3 text-sm {ocr.status === 'completed'
					? 'border-violet-200 bg-violet-50'
					: 'border-amber-200 bg-amber-50'}"
			>
				{#if ocr.status === 'completed'}
					<p class="mb-2 font-medium text-violet-800">Hasil pembacaan OCR (draft)</p>
					<dl class="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
						<dt class="text-slate-500">Merchant</dt>
						<dd>{ocr.merchant ?? 'â€” tidak terbaca'}</dd>
						<dt class="text-slate-500">Tanggal</dt>
						<dd>{ocr.transaction_date ?? 'â€” tidak terbaca'}</dd>
						<dt class="text-slate-500">Total</dt>
						<dd>{ocr.total_amount != null ? formatRupiah(ocr.total_amount) : 'â€” tidak terbaca'}</dd>
					</dl>
					{#if ocr.raw_text}
						<details class="mt-2">
							<summary class="cursor-pointer text-xs text-slate-500">Lihat teks mentah</summary>
							<pre class="mt-1 max-h-40 overflow-auto text-xs whitespace-pre-wrap">{ocr.raw_text}</pre>
						</details>
					{/if}
				{:else}
					<p class="text-amber-800">
						OCR tidak berhasil: {ocr.error ?? 'gambar tidak dapat diproses'}. Silakan isi formulir
						secara manual.
					</p>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Kolom kanan: data pengajuan -->
	<div class="card space-y-4">
		<h2 class="font-semibold text-slate-800">2. Detail pengeluaran</h2>
		<div>
			<span class="label">Kategori</span>
			<div class="flex gap-2">
				{#each [['transport', 'Transportasi'], ['consumption', 'Konsumsi']] as [value, text] (value)}
					<label
						class="flex-1 cursor-pointer rounded-lg border px-3 py-2 text-center text-sm {category ===
						value
							? 'border-brand-600 bg-brand-50 font-medium text-brand-700'
							: 'border-slate-300'}"
					>
						<input type="radio" class="sr-only" bind:group={category} {value} />
						{text}
					</label>
				{/each}
			</div>
		</div>
		<div>
			<label class="label" for="merchant">Merchant / penyedia {@render ocrTag('merchant')}</label>
			<input id="merchant" class="input" bind:value={merchant} placeholder="mis. Blue Taxi, Kopi Senja" />
		</div>
		<div class="grid gap-4 sm:grid-cols-2">
			<div>
				<label class="label" for="date">Tanggal transaksi * {@render ocrTag('date')}</label>
				<input id="date" type="date" class="input" max={today} bind:value={transactionDate} required />
			</div>
			<div>
				<label class="label" for="amount">Nominal (Rp) * {@render ocrTag('amount')}</label>
				<input id="amount" type="number" min="1" step="any" class="input" bind:value={amount} required />
			</div>
		</div>
		<div>
			<label class="label" for="desc">Keterangan / keperluan *</label>
			<textarea id="desc" rows="3" class="input" bind:value={description} required
				placeholder="mis. Taksi ke kantor klien PT ABC untuk meeting"></textarea>
		</div>

		{#if needsConfirm}
			<label class="flex items-start gap-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
				<input type="checkbox" class="mt-0.5" bind:checked={ocrConfirmed} />
				Saya sudah membandingkan data di atas dengan struk asli dan memastikan merchant, tanggal, dan
				nominal sudah benar.
			</label>
		{/if}

		<div class="flex flex-wrap justify-end gap-2 pt-2">
			<button type="button" class="btn btn-secondary" disabled={saving || uploading}
				onclick={() => save(false)}>Simpan draft</button
			>
			<button type="submit" class="btn btn-primary" disabled={saving || uploading}>
				{saving ? 'Menyimpan...' : 'Kirim pengajuan'}
			</button>
		</div>
	</div>
</form>
