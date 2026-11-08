<script lang="ts">
	import { untrack } from 'svelte';
	import UploadSimple from 'phosphor-svelte/lib/UploadSimpleIcon';
	import Car from 'phosphor-svelte/lib/CarIcon';
	import ForkKnife from 'phosphor-svelte/lib/ForkKnifeIcon';
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
	const CATEGORIES: [Category, string][] = [
		['transport', 'Transportasi'],
		['consumption', 'Konsumsi']
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
	let saving = $state(false);
	let ocrConfirmed = $state(false);
	let fromOcr = $state<Record<string, boolean>>({});
	let dragging = $state(false);
	let fileInput: HTMLInputElement;

	const ocr = $derived(receipt?.ocr ?? null);
	const needsConfirm = $derived(ocr?.status === 'completed');

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
		<span class="ml-1 rounded bg-accent-soft px-1.5 py-0.5 text-[10px] font-medium text-accent"
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
		<h2 class="font-semibold text-fg">1. Bukti transaksi</h2>
		<label class="flex cursor-pointer items-center gap-2.5 text-sm text-muted">
			<input type="checkbox" class="check" bind:checked={useOcr} />
			Baca struk otomatis dengan OCR
		</label>
		<label
			class="group flex cursor-pointer flex-col items-center gap-2 rounded-xl border-2 border-dashed px-4 py-8 text-center transition-all duration-200 focus-within:border-accent {dragging
				? 'scale-[1.01] border-accent bg-accent-soft'
				: 'border-line hover:border-accent/60 hover:bg-accent-soft/50'} {uploading ? 'pointer-events-none opacity-60' : ''}"
			ondragenter={(e) => {
				e.preventDefault();
				dragging = true;
			}}
			ondragover={(e) => e.preventDefault()}
			ondragleave={(e) => {
				if (!e.currentTarget.contains(e.relatedTarget as Node)) dragging = false;
			}}
			ondrop={onDrop}
		>
			<span
				class="grid h-11 w-11 place-items-center rounded-full bg-accent-soft text-accent transition-transform duration-300 ease-out-expo group-hover:-translate-y-0.5 {dragging
					? '-translate-y-1'
					: ''}"
			>
				<UploadSimple size={22} weight="bold" />
			</span>
			<span class="text-sm font-medium">
				{dragging ? 'Lepaskan untuk mengunggah' : receipt ? 'Ganti foto struk' : 'Pilih atau tarik foto struk ke sini'}
			</span>
			<span class="text-xs text-muted">JPG, JPEG, atau PNG, maksimal 5 MB</span>
			<input
				bind:this={fileInput}
				type="file"
				accept="image/jpeg,image/png"
				class="sr-only"
				onchange={(e) => {
					const f = e.currentTarget.files?.[0];
					if (f) handleFile(f);
				}}
				disabled={uploading}
			/>
		</label>

		{#if previewUrl}
			<div class="relative min-h-32 overflow-hidden rounded-lg border border-line bg-subtle">
				<img
					src={previewUrl}
					alt="Pratinjau struk"
					class="max-h-96 w-full object-contain transition-[filter] duration-300 {uploading ? 'brightness-90' : ''}"
				/>
				{#if uploading && useOcr}
					<div class="scan-line"></div>
				{/if}
				{#if uploading}
					<div
						class="absolute inset-x-3 bottom-3 rounded-lg bg-surface/90 px-3 py-2 text-center text-xs font-medium text-accent backdrop-blur"
						role="status"
					>
						{useOcr ? 'Membaca struk...' : 'Mengunggah...'}
					</div>
				{/if}
			</div>
		{/if}

		{#if ocr}
			<div
				class="rounded-lg border p-3 text-sm {ocr.status === 'completed'
					? 'border-line bg-subtle'
					: 'border-warn/30 bg-warn/10'}"
			>
				{#if ocr.status === 'completed'}
					<p class="mb-2 font-medium text-fg">Hasil pembacaan OCR (draft)</p>
					<dl class="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
						<dt class="text-muted">Merchant</dt>
						<dd>{ocr.merchant ?? 'Tidak terbaca'}</dd>
						<dt class="text-muted">Tanggal</dt>
						<dd>{ocr.transaction_date ?? 'Tidak terbaca'}</dd>
						<dt class="text-muted">Total</dt>
						<dd class="num">{ocr.total_amount != null ? formatRupiah(ocr.total_amount) : 'Tidak terbaca'}</dd>
					</dl>
					{#if ocr.raw_text}
						<details class="mt-2">
							<summary class="cursor-pointer text-xs text-muted">Lihat teks mentah</summary>
							<pre class="mt-1 max-h-40 overflow-auto text-xs whitespace-pre-wrap">{ocr.raw_text}</pre>
						</details>
					{/if}
				{:else}
					<p class="text-fg">
						OCR tidak berhasil: {ocr.error ?? 'gambar tidak dapat diproses'}. Silakan isi formulir
						secara manual.
					</p>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Kolom kanan: data pengajuan -->
	<div class="card space-y-4">
		<h2 class="font-semibold text-fg">2. Detail pengeluaran</h2>
		<div>
			<span class="label">Kategori</span>
			<div class="relative grid grid-cols-2 rounded-lg bg-subtle p-1">
				<span
					class="absolute inset-y-1 left-1 w-[calc(50%-4px)] rounded-md border border-line bg-surface shadow-[0_1px_2px_var(--shadow)] transition-transform duration-300 ease-out-expo"
					style="transform: translateX({category === 'consumption' ? '100%' : '0'})"
					aria-hidden="true"
				></span>
				{#each CATEGORIES as [value, text] (value)}
					{@const on = category === value}
					<label
						class="relative flex cursor-pointer items-center justify-center gap-2 rounded-md px-3 py-2 text-sm transition-colors has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-accent {on
							? 'font-medium text-fg'
							: 'text-muted hover:text-fg'}"
					>
						<input type="radio" class="sr-only" bind:group={category} {value} />
						{#if value === 'transport'}
							<Car size={16} weight={on ? 'fill' : 'regular'} class={on ? 'text-accent' : ''} />
						{:else}
							<ForkKnife size={16} weight={on ? 'fill' : 'regular'} class={on ? 'text-accent' : ''} />
						{/if}
						{text}
					</label>
				{/each}
			</div>
		</div>
		<div>
			<label class="label" for="merchant">Merchant / penyedia {@render ocrTag('merchant')}</label>
			<input id="merchant" class="input {fromOcr.merchant ? 'ocr-flash' : ''}" bind:value={merchant}
				placeholder="mis. Blue Taxi, Kopi Senja" />
		</div>
		<div class="grid gap-4 sm:grid-cols-2">
			<div>
				<label class="label" for="date">Tanggal transaksi * {@render ocrTag('date')}</label>
				<input id="date" type="date" class="input {fromOcr.date ? 'ocr-flash' : ''}" max={today}
					bind:value={transactionDate} required />
			</div>
			<div>
				<label class="label" for="amount">Nominal (Rp) * {@render ocrTag('amount')}</label>
				<input id="amount" type="number" min="1" step="any" class="input num {fromOcr.amount ? 'ocr-flash' : ''}"
					bind:value={amount} required />
			</div>
		</div>
		<div>
			<label class="label" for="desc">Keterangan / keperluan *</label>
			<textarea id="desc" rows="3" class="input" bind:value={description} required
				placeholder="mis. Taksi ke kantor klien PT ABC untuk meeting"></textarea>
		</div>

		{#if needsConfirm}
			<label
				class="flex cursor-pointer items-start gap-2.5 rounded-lg border p-3 text-sm text-fg transition-colors duration-300 {ocrConfirmed
					? 'border-accent/40 bg-accent-soft'
					: 'border-warn/30 bg-warn/10'}"
			>
				<input type="checkbox" class="check mt-px" bind:checked={ocrConfirmed} />
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
