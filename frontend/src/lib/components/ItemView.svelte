<script lang="ts">
	import { slide } from 'svelte/transition';
	import ArrowUUpLeft from 'phosphor-svelte/lib/ArrowUUpLeftIcon';
	import CaretRight from 'phosphor-svelte/lib/CaretRightIcon';
	import Check from 'phosphor-svelte/lib/CheckIcon';
	import FilePdf from 'phosphor-svelte/lib/FilePdfIcon';
	import Flag from 'phosphor-svelte/lib/FlagIcon';
	import Receipt from 'phosphor-svelte/lib/ReceiptIcon';
	import WarningCircle from 'phosphor-svelte/lib/WarningCircleIcon';
	import { DUPLICATE_REASON_LABEL, OCR_LOW_CONFIDENCE, formatDate, formatRupiah } from '#lib/labels.ts';
	import { ease, ms } from '#lib/motion.ts';
	import type { DuplicateMatch, ReimbursementItem } from '#lib/types/index.ts';

	let {
		item,
		index,
		duplicates = [],
		reviewable = false,
		flagNote = $bindable()
	}: {
		item: ReimbursementItem;
		index: number;
		duplicates?: DuplicateMatch[];
		/** Admin/atasan yang bisa mengembalikan pengajuan boleh menandai item ini. */
		reviewable?: boolean;
		/** Catatan revisi untuk item ini; undefined = tidak ditandai. */
		flagNote?: string;
	} = $props();

	const n = $derived(String(index + 1).padStart(2, '0'));
	const ocr = $derived(item.receipts.find((r) => r.ocr?.status === 'completed')?.ocr ?? null);
	const flagged = $derived(flagNote !== undefined);
	let failedThumbs = $state<Record<number, boolean>>({});

	const compare = $derived.by(() => {
		if (!ocr) return [];
		const conf = ocr.confidence ?? {};
		return [
			{ label: 'Merchant', ocr: ocr.merchant, conf: conf.merchant ?? null, final: item.merchant,
				same: (ocr.merchant || null) === (item.merchant || null) },
			{ label: 'Tanggal', ocr: ocr.transaction_date ? formatDate(ocr.transaction_date) : null,
				conf: conf.transaction_date ?? null, final: formatDate(item.transaction_date),
				same: ocr.transaction_date === item.transaction_date },
			{ label: 'Total', ocr: ocr.total_amount != null ? formatRupiah(ocr.total_amount) : null,
				conf: conf.total_amount ?? null, final: formatRupiah(item.amount),
				same: ocr.total_amount != null && Number(ocr.total_amount) === Number(item.amount) }
		];
	});
	const corrected = $derived(compare.some((c) => !c.same));
</script>

<article class="rounded-2xl border bg-surface p-4 transition-[border-color,box-shadow] duration-300 sm:p-5 {flagged
	? 'border-warn/60 shadow-[0_0_0_3px_color-mix(in_oklab,var(--color-warn)_14%,transparent)]'
	: 'border-line'}">
	<header class="flex flex-wrap items-center gap-x-3 gap-y-1">
		<span class="code grid size-7 shrink-0 place-items-center rounded-lg bg-chip text-[11px] text-on-chip">{n}</span>
		<div class="min-w-0 flex-1">
			<p class="truncate font-medium text-ink">{item.merchant ?? 'Tanpa merchant'}</p>
			<p class="num text-[12.5px] text-muted">{formatDate(item.transaction_date)}</p>
		</div>
		<span class="num font-semibold text-ink">{formatRupiah(item.amount)}</span>
	</header>

	{#if item.review_note}
		<div class="mt-3 flex items-start gap-2.5 rounded-xl border border-warn/35 bg-warn/[0.07] p-3 text-[13px] text-ink">
			<ArrowUUpLeft size={15} weight="bold" class="mt-0.5 shrink-0 text-warn" />
			<p><span class="font-semibold">Perlu diperbaiki:</span> {item.review_note}</p>
		</div>
	{/if}

	{#if item.receipts.length}
		<div class="mt-4 flex gap-2.5 overflow-x-auto pb-1">
			{#each item.receipts as rc (rc.id)}
				{@const pdf = rc.file_type === 'application/pdf'}
				<a href="/api/receipts/{rc.id}/file" target="_blank" rel="noopener" title={rc.original_filename}
					class="group relative block h-44 w-32 shrink-0 overflow-hidden rounded-xl border border-line {pdf ? 'bg-white' : 'bg-sunken'}">
					{#if failedThumbs[rc.id]}
						<span class="grid size-full place-items-center text-faint"><Receipt size={24} /></span>
					{:else}
						<img src="/api/receipts/{rc.id}/{pdf ? 'preview' : 'file'}" alt="Struk {rc.original_filename}"
							onerror={() => (failedThumbs[rc.id] = true)}
							class="size-full object-cover transition-transform duration-500 ease-snap group-hover:scale-105 {pdf ? 'object-top' : ''}" />
					{/if}
					{#if pdf}
						<span class="absolute bottom-1.5 left-1.5 inline-flex items-center gap-1 rounded-full bg-primary px-2 py-0.5 text-[10.5px] font-medium text-on-primary"><FilePdf size={11} /> PDF</span>
					{/if}
				</a>
			{/each}
		</div>
	{:else}
		<p class="mt-4 text-[13px] text-faint">Belum ada bukti transaksi.</p>
	{/if}

	{#if item.note}
		<p class="mt-3 text-[13.5px] text-ink-2"><span class="text-muted">Catatan:</span> {item.note}</p>
	{/if}

	{#if duplicates.length}
		<ul class="mt-3 space-y-1 text-[12.5px]">
			{#each duplicates as d (d.item_id)}
				<li class="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-muted">
					<WarningCircle size={14} weight="fill" class="text-warn" />
					<span class="rounded-full bg-warn/15 px-2 py-0.5 text-[11px] font-semibold text-warn">{DUPLICATE_REASON_LABEL[d.reason]}</span>
					{#if d.same_claim}
						dengan item lain di pengajuan ini ({d.merchant ?? '-'})
					{:else}
						<a href="/reimburse/{d.id}" class="code font-medium text-ink underline underline-offset-2">{d.code}</a>
						{d.employee} · {formatDate(d.transaction_date)} · <span class="num">{formatRupiah(d.amount)}</span>
					{/if}
				</li>
			{/each}
		</ul>
	{/if}

	{#if ocr}
		<details class="group/ocr mt-3 border-t border-line pt-3">
			<summary class="flex cursor-pointer list-none flex-wrap items-center gap-x-2 gap-y-1 text-[12.5px] font-medium text-muted transition-colors hover:text-ink">
				<CaretRight size={12} class="transition-transform duration-200 group-open/ocr:rotate-90" />
				OCR vs diajukan
				<span class="font-normal">· {item.ocr_confirmed ? 'dikonfirmasi karyawan' : 'belum dikonfirmasi'}</span>
				{#if corrected}<span class="rounded-full bg-warn/15 px-2 py-0.5 text-[11px] font-semibold text-warn">ada koreksi</span>{/if}
			</summary>
			<div class="mt-2 overflow-x-auto">
				<table class="table text-[13px]">
					<thead><tr><th class="pl-0!">Field</th><th>Hasil OCR</th><th>Diajukan</th><th class="w-24"></th></tr></thead>
					<tbody>
						{#each compare as c (c.label)}
							<tr>
								<td class="pl-0! text-muted">{c.label}</td>
								<td class="{c.ocr ? 'text-ink-2' : 'text-faint italic'} {c.label === 'Total' ? 'num' : ''}">
									{c.ocr ?? 'tidak terbaca'}
									{#if c.ocr && c.conf != null}
										<span class="num ml-1 text-[11px] {c.conf < OCR_LOW_CONFIDENCE ? 'font-semibold text-warn' : 'text-faint'}" title="Skor keyakinan OCR">{Math.round(c.conf * 100)}%</span>
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
		</details>
	{/if}

	{#if reviewable}
		<div class="mt-3 border-t border-line pt-3">
			{#if flagged}
				<div transition:slide={{ duration: ms(240), easing: ease }}>
					<label class="label" for="flag-{item.id}">Catatan revisi item ini</label>
					<textarea id="flag-{item.id}" rows="2" class="input" bind:value={flagNote}
						placeholder="mis. Struk buram, nominal tidak terbaca"></textarea>
					<button type="button" class="btn btn-ghost btn-sm mt-1.5 text-muted" onclick={() => (flagNote = undefined)}>Batal tandai</button>
				</div>
			{:else}
				<button type="button" class="group btn btn-ghost btn-sm text-muted hover:text-warn" onclick={() => {
					flagNote = '';
					requestAnimationFrame(() => document.getElementById(`flag-${item.id}`)?.focus());
				}}>
					<Flag size={14} class="transition-transform duration-300 ease-spring group-hover:-rotate-12" /> Tandai perlu revisi
				</button>
			{/if}
		</div>
	{/if}
</article>
