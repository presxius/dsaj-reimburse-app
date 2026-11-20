<script lang="ts">
	import { slide } from 'svelte/transition';
	import ArrowUUpLeft from 'phosphor-svelte/lib/ArrowUUpLeftIcon';
	import CaretRight from 'phosphor-svelte/lib/CaretRightIcon';
	import Check from 'phosphor-svelte/lib/CheckIcon';
	import FilePdf from 'phosphor-svelte/lib/FilePdfIcon';
	import Plus from 'phosphor-svelte/lib/PlusIcon';
	import Trash from 'phosphor-svelte/lib/TrashIcon';
	import WarningCircle from 'phosphor-svelte/lib/WarningCircleIcon';
	import X from 'phosphor-svelte/lib/XIcon';
	import AmountInput from './AmountInput.svelte';
	import Spinner from './Spinner.svelte';
	import { ACCEPTED_TYPES, MAX_FILES_PER_ITEM, failedOcrOf, isLow, ocrOf, thumbUrl } from '#lib/draft.ts';
	import type { DraftItem } from '#lib/draft.ts';
	import { STATUS_LABEL, formatDate, formatRupiah } from '#lib/labels.ts';
	import { ease, ms } from '#lib/motion.ts';
	import type { OcrField } from '#lib/types/index.ts';

	let {
		item = $bindable(),
		index,
		problem = null,
		onaddfiles,
		onremove
	}: {
		item: DraftItem;
		index: number;
		/** Kesalahan yang menghalangi pengiriman; ditampilkan setelah percobaan kirim. */
		problem?: string | null;
		onaddfiles: (files: File[]) => void;
		onremove: () => void;
	} = $props();

	const today = new Date().toLocaleDateString('en-CA');
	const n = $derived(String(index + 1).padStart(2, '0'));
	const ocr = $derived(ocrOf(item));
	const failed = $derived(failedOcrOf(item));
	const uploading = $derived(item.files.some((f) => f.status !== 'done'));
	const canAddFile = $derived(item.files.length < MAX_FILES_PER_ITEM);
	const ocrRows = $derived.by((): { k: string; f: OcrField; v: string | null }[] => {
		if (!ocr) return [];
		return [
			{ k: 'Merchant', f: 'merchant', v: ocr.merchant },
			{ k: 'Tanggal', f: 'transaction_date', v: ocr.transaction_date ? formatDate(ocr.transaction_date) : null },
			{ k: 'Total', f: 'total_amount', v: ocr.total_amount != null ? formatRupiah(ocr.total_amount) : null }
		];
	});
	let dragging = $state(false);
	let fileInput = $state<HTMLInputElement>();

	function pick(list: FileList | null | undefined) {
		const files = [...(list ?? [])];
		if (files.length) onaddfiles(files);
		if (fileInput) fileInput.value = '';
	}

	function removeFile(key: string) {
		item.files = item.files.filter((f) => f.key !== key);
	}
</script>

{#snippet ocrTag(key: 'merchant' | 'date' | 'amount', field: OcrField)}
	{#if item.fromOcr[key]}
		{#if isLow(ocr, field)}
			<span class="tag-ocr tag-ocr-low" title="OCR kurang yakin. Cocokkan dengan struk.">OCR · cek</span>
		{:else}
			<span class="tag-ocr" title="Diisi dari hasil OCR">OCR</span>
		{/if}
	{/if}
{/snippet}

<article
	class="panel relative p-4 transition-[box-shadow] duration-300 sm:p-5 {problem ? 'ring-2 ring-danger/60' : ''}"
	data-item={item.key}
>
	<header class="flex items-center gap-3">
		<span class="code grid size-7 shrink-0 place-items-center rounded-lg bg-chip text-[11px] text-on-chip">{n}</span>
		<span class="min-w-0 flex-1 truncate font-medium text-ink">{item.merchant || 'Item pengeluaran'}</span>
		<span class="num shrink-0 font-semibold text-ink">{item.amount ? formatRupiah(item.amount) : ''}</span>
		<button type="button" class="icon-btn size-8 shrink-0 hover:text-danger" onclick={onremove} aria-label="Hapus item {index + 1}" title="Hapus item">
			<Trash size={16} />
		</button>
	</header>

	{#if item.reviewNote}
		<div class="mt-3 flex items-start gap-2.5 rounded-xl border border-warn/35 bg-warn/[0.07] p-3 text-[13px] text-ink">
			<ArrowUUpLeft size={15} weight="bold" class="mt-0.5 shrink-0 text-warn" />
			<p><span class="font-semibold">Perlu diperbaiki:</span> {item.reviewNote}</p>
		</div>
	{/if}

	<div class="mt-4 grid gap-4 sm:grid-cols-[11rem_minmax(0,1fr)]">
		<!-- File bukti: struk, halaman lanjutan, atau bukti bayar dari transaksi yang sama. -->
		<div
			class="grid grid-cols-3 content-start gap-2 rounded-xl transition-[background-color,outline-color] sm:grid-cols-2 {dragging ? 'bg-lime/20 outline-2 outline-ink outline-dashed' : ''}"
			role="group"
			aria-label="Bukti transaksi item {index + 1}"
			ondragenter={(e) => {
				e.preventDefault();
				e.stopPropagation();
				dragging = true;
			}}
			ondragover={(e) => {
				e.preventDefault();
				e.stopPropagation();
			}}
			ondragleave={(e) => {
				if (!e.currentTarget.contains(e.relatedTarget as Node)) dragging = false;
			}}
			ondrop={(e) => {
				e.preventDefault();
				e.stopPropagation();
				dragging = false;
				if (canAddFile) pick(e.dataTransfer?.files);
			}}
		>
			{#each item.files as f (f.key)}
				{@const src = thumbUrl(f)}
				<div class="group/thumb relative aspect-[3/4] overflow-hidden rounded-lg border border-line bg-sunken"
					in:slide={{ duration: ms(220), easing: ease, axis: 'x' }}>
					{#if src}
						<a href={f.receipt ? `/api/receipts/${f.receipt.id}/file` : f.localUrl} target="_blank" rel="noopener" class="block size-full" title={f.name}>
							<img {src} alt={f.name} class="size-full object-cover transition-[filter,transform] duration-500 ease-snap group-hover/thumb:scale-105 {f.status !== 'done' ? 'brightness-75 saturate-50' : ''} {f.isPdf ? 'bg-white object-top' : ''}" />
						</a>
					{:else}
						<div class="grid size-full place-items-center text-muted"><FilePdf size={26} /></div>
					{/if}
					{#if f.isPdf}
						<span class="pointer-events-none absolute bottom-1 left-1 rounded bg-primary px-1 py-px text-[9.5px] font-semibold text-on-primary">PDF</span>
					{/if}
					{#if f.status !== 'done'}
						<div class="absolute inset-0 grid place-items-center" role="status" aria-label={f.status === 'queued' ? 'Menunggu' : 'Mengunggah'}>
							{#if f.status === 'uploading'}
								<div class="scan-beam"></div>
								<span class="grid size-7 place-items-center rounded-full bg-primary text-on-primary shadow-float"><Spinner size={13} /></span>
							{:else}
								<span class="rounded-full bg-primary/85 px-2 py-0.5 text-[10.5px] font-medium text-on-primary">antre</span>
							{/if}
						</div>
					{:else}
						<button type="button"
							class="absolute top-1 right-1 grid size-6 place-items-center rounded-full bg-primary/85 text-on-primary opacity-0 shadow-float transition-opacity duration-150 group-hover/thumb:opacity-100 focus-visible:opacity-100 max-sm:opacity-100"
							onclick={() => removeFile(f.key)} aria-label="Lepas file {f.name}" title="Lepas file">
							<X size={12} weight="bold" />
						</button>
					{/if}
				</div>
			{/each}
			{#if canAddFile}
				<label
					class="group/add grid aspect-[3/4] cursor-pointer place-items-center rounded-lg border-[1.5px] border-dashed text-center text-[11.5px] text-muted transition-[border-color,background-color,color] duration-200 hover:border-faint hover:bg-sunken/60 hover:text-ink {item.files.length === 0 && problem ? 'border-danger/60' : 'border-line-strong'}"
					title="Tambah file: halaman lanjutan struk atau bukti bayar transaksi yang sama"
				>
					<span class="flex flex-col items-center gap-1 px-1">
						<Plus size={18} class="transition-transform duration-300 ease-spring group-hover/add:rotate-90" />
						{item.files.length ? 'Tambah file' : 'Lampirkan struk'}
					</span>
					<input bind:this={fileInput} type="file" multiple accept={ACCEPTED_TYPES.join(',')} class="sr-only"
						onchange={(e) => pick(e.currentTarget.files)} />
				</label>
			{/if}
		</div>

		<div class="space-y-3.5">
			<div>
				<label class="label" for="m-{item.key}">Merchant / penyedia {@render ocrTag('merchant', 'merchant')}</label>
				<input id="m-{item.key}" class="input {item.fromOcr.merchant ? 'ocr-flash' : ''}" bind:value={item.merchant}
					placeholder="mis. GoRide, Kopi Senja" />
			</div>
			<div class="grid gap-3.5 sm:grid-cols-2">
				<div>
					<label class="label" for="d-{item.key}">Tanggal <span class="text-danger">*</span> {@render ocrTag('date', 'transaction_date')}</label>
					<input id="d-{item.key}" type="date" class="input {item.fromOcr.date ? 'ocr-flash' : ''}" max={today}
						bind:value={item.transaction_date} />
				</div>
				<div>
					<label class="label" for="a-{item.key}">Nominal <span class="text-danger">*</span> {@render ocrTag('amount', 'total_amount')}</label>
					<AmountInput id="a-{item.key}" bind:value={item.amount} class={item.fromOcr.amount ? 'ocr-flash' : ''} />
				</div>
			</div>
			<div>
				<label class="label" for="n-{item.key}">Catatan <span class="font-normal text-muted">· opsional</span></label>
				<input id="n-{item.key}" class="input" bind:value={item.note} placeholder="mis. pulang lembur" />
			</div>
		</div>
	</div>

	{#if ocr && !uploading}
		<details class="group/ocr mt-4 rounded-xl border border-line bg-sunken/60 px-4 py-3" transition:slide={{ duration: ms(260), easing: ease }}>
			<summary class="flex cursor-pointer list-none items-center gap-2 text-[12.5px] font-medium text-muted transition-colors hover:text-ink">
				<CaretRight size={12} class="transition-transform duration-200 group-open/ocr:rotate-90" />
				Hasil pembacaan OCR
				{#if ocrRows.some((r) => r.v && isLow(ocr, r.f))}
					<span class="tag-ocr tag-ocr-low">ada yang kurang jelas</span>
				{/if}
			</summary>
			<dl class="mt-3 space-y-1.5 text-[13px]">
				{#each ocrRows as { k, f, v } (k)}
					{@const c = v ? (ocr.confidence?.[f] ?? null) : null}
					<div class="flex items-center gap-3">
						<span class="grid size-5 shrink-0 place-items-center rounded-full {v ? (isLow(ocr, f) ? 'bg-warn/20 text-warn' : 'bg-lime text-on-lime') : 'bg-line text-faint'}">
							{#if v && isLow(ocr, f)}<WarningCircle size={12} weight="bold" />{:else if v}<Check size={11} weight="bold" />{:else}<span class="h-[1.5px] w-2 rounded bg-current"></span>{/if}
						</span>
						<dt class="w-20 shrink-0 text-muted">{k}</dt>
						<dd class="min-w-0 flex-1 truncate {v ? 'font-medium text-ink' : 'text-faint italic'} {k === 'Total' ? 'num' : ''}">{v ?? 'tidak terbaca'}</dd>
						{#if c != null}
							<span class="num shrink-0 text-[11.5px] {isLow(ocr, f) ? 'font-semibold text-warn' : 'text-faint'}" title="Skor keyakinan OCR">{Math.round(c * 100)}%</span>
						{/if}
					</div>
				{/each}
			</dl>
			{#if ocr.raw_text}
				<pre class="code mt-3 max-h-40 overflow-auto rounded-lg bg-surface p-3 text-[11.5px] leading-relaxed whitespace-pre-wrap text-ink-2">{ocr.raw_text}</pre>
			{/if}
		</details>
	{:else if failed && !uploading}
		<p class="mt-4 flex items-start gap-2 text-[12.5px] text-muted">
			<WarningCircle size={15} weight="fill" class="mt-px shrink-0 text-warn" />
			OCR tidak berhasil ({failed.error ?? 'gambar tidak dapat diproses'}). Isi data item secara manual.
		</p>
	{/if}

	{#if item.duplicates.length > 0}
		<div class="mt-4 flex items-start gap-2.5 rounded-xl border border-warn/35 bg-warn/[0.07] p-3 text-[13px] text-ink" transition:slide={{ duration: ms(260), easing: ease }}>
			<WarningCircle size={16} weight="fill" class="mt-0.5 shrink-0 text-warn" />
			<div>
				<p class="font-semibold">Struk ini sudah pernah diajukan.</p>
				<ul class="mt-0.5 text-muted">
					{#each item.duplicates as d (d.item_id)}
						<li>
							<a href="/reimburse/{d.id}" target="_blank" rel="noopener" class="code font-medium text-ink underline underline-offset-2">{d.code}</a>
							· {STATUS_LABEL[d.status]} · <span class="num">{formatRupiah(d.amount)}</span>
						</li>
					{/each}
				</ul>
			</div>
		</div>
	{/if}

	{#if ocr}
		<label
			class="mt-4 flex cursor-pointer items-start gap-3 rounded-xl border p-3.5 text-[13px] text-ink-2 transition-[background-color,border-color] duration-300 {item.ocrConfirmed
				? 'border-lime-deep bg-lime/25'
				: 'border-warn/40 bg-warn/[0.07]'}"
		>
			<input type="checkbox" class="check mt-0.5" bind:checked={item.ocrConfirmed} />
			<span><span class="font-semibold text-ink">Saya sudah memeriksa hasil OCR item ini</span> terhadap struk asli.</span>
		</label>
	{/if}

	{#if problem}
		<p class="mt-3 text-[12.5px] font-medium text-danger" transition:slide={{ duration: ms(200), easing: ease }}>Item {index + 1}: {problem}</p>
	{/if}
</article>
