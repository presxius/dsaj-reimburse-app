<script lang="ts">
	import { tick, untrack } from 'svelte';
	import { flip } from 'svelte/animate';
	import { fly, slide } from 'svelte/transition';
	import ArrowRight from 'phosphor-svelte/lib/ArrowRightIcon';
	import Car from 'phosphor-svelte/lib/CarIcon';
	import ForkKnife from 'phosphor-svelte/lib/ForkKnifeIcon';
	import Plus from 'phosphor-svelte/lib/PlusIcon';
	import UploadSimple from 'phosphor-svelte/lib/UploadSimpleIcon';
	import CountUp from './CountUp.svelte';
	import ItemEditor from './ItemEditor.svelte';
	import Segmented from './Segmented.svelte';
	import Spinner from './Spinner.svelte';
	import {
		ACCEPTED_TYPES,
		MAX_FILES_PER_ITEM,
		MAX_FILE_SIZE,
		MAX_ITEMS,
		emptyItem,
		fromSaved,
		newKey,
		submitProblem
	} from '#lib/draft.ts';
	import type { DraftFile, DraftItem } from '#lib/draft.ts';
	import { formatRupiah } from '#lib/labels.ts';
	import { ease, ms } from '#lib/motion.ts';
	import { api } from '#lib/services/api.ts';
	import { notify, notifyError } from '#lib/session.svelte.ts';
	import type { Category, ReimbursementDetail, UploadedReceipt } from '#lib/types/index.ts';

	let {
		initial,
		onsaved
	}: { initial?: ReimbursementDetail; onsaved: (r: ReimbursementDetail) => void } = $props();

	const CATEGORIES: { value: Category; label: string; icon: typeof Car }[] = [
		{ value: 'transport', label: 'Transportasi', icon: Car },
		{ value: 'consumption', label: 'Konsumsi', icon: ForkKnife }
	];

	// Nilai awal hanya dipakai sekali saat form dibuat.
	const init = untrack(() => initial);
	let category = $state<Category>(init?.category ?? 'transport');
	let purpose = $state(init?.purpose ?? '');
	let items = $state<DraftItem[]>(init?.items.map(fromSaved) ?? []);
	let useOcr = $state(true);
	let saving = $state<'draft' | 'submit' | null>(null);
	let dragging = $state(false);
	let triedSubmit = $state(false);
	let purposeShake = $state(false);
	let dropInput = $state<HTMLInputElement>();

	const total = $derived(items.reduce((sum, i) => sum + (i.amount ?? 0), 0));
	const pending = $derived(items.reduce((n, i) => n + i.files.filter((f) => f.status !== 'done').length, 0));
	const problems = $derived(Object.fromEntries(items.map((i) => [i.key, submitProblem(i)])));
	const busy = $derived(!!saving);

	// --- Antrean unggah: satu file per waktu, karena OCR di server berat (RAM & CPU). ---

	type Job = { itemKey: string; fileKey: string; file: File; ocr: boolean; fresh: boolean };
	const queue: Job[] = [];
	let pumping = false;
	let readCount = 0;

	function validFile(file: File) {
		if (!ACCEPTED_TYPES.includes(file.type)) {
			notify(`${file.name}: format harus JPG, PNG, atau PDF.`, 'error');
			return false;
		}
		if (file.size > MAX_FILE_SIZE) {
			notify(`${file.name}: ukuran maksimal 5 MB.`, 'error');
			return false;
		}
		return true;
	}

	function draftFile(file: File): DraftFile {
		const isPdf = file.type === 'application/pdf';
		return { key: newKey(), receipt: null, name: file.name, isPdf, localUrl: URL.createObjectURL(file), status: 'queued' };
	}

	/** Tiap file menjadi satu item baru (satu struk = satu transaksi). */
	function addAsItems(list: FileList | File[] | null | undefined) {
		const files = [...(list ?? [])].filter(validFile);
		const room = MAX_ITEMS - items.length;
		if (files.length > room) notify(`Maksimal ${MAX_ITEMS} item per pengajuan; ${files.length - Math.max(room, 0)} file dilewati.`, 'error');
		for (const file of files.slice(0, Math.max(room, 0))) {
			const item = emptyItem();
			const f = draftFile(file);
			item.files.push(f);
			items.push(item);
			queue.push({ itemKey: item.key, fileKey: f.key, file, ocr: useOcr, fresh: true });
		}
		if (dropInput) dropInput.value = '';
		pump();
	}

	/** File tambahan untuk item yang sama (halaman lanjutan, bukti bayar): tanpa OCR. */
	function addToItem(item: DraftItem, list: File[]) {
		const files = list.filter(validFile);
		const room = MAX_FILES_PER_ITEM - item.files.length;
		if (files.length > room) notify(`Maksimal ${MAX_FILES_PER_ITEM} file per item.`, 'error');
		for (const file of files.slice(0, Math.max(room, 0))) {
			const f = draftFile(file);
			const fresh = item.files.length === 0 && !item.merchant && !item.transaction_date && item.amount == null;
			item.files.push(f);
			queue.push({ itemKey: item.key, fileKey: f.key, file, ocr: useOcr && fresh, fresh });
		}
		pump();
	}

	async function pump() {
		if (pumping) return;
		pumping = true;
		try {
			while (queue.length) await upload(queue.shift()!);
		} finally {
			pumping = false;
		}
		if (readCount) {
			notify(readCount === 1 ? 'Struk terbaca. Periksa hasil OCR sebelum mengirim.' : `${readCount} struk terbaca. Periksa hasil OCR tiap item.`);
			readCount = 0;
		}
	}

	async function upload(job: Job) {
		const item = items.find((i) => i.key === job.itemKey);
		const f = item?.files.find((x) => x.key === job.fileKey);
		if (!item || !f) return; // item/file sudah dihapus sebelum giliran diunggah
		f.status = 'uploading';
		try {
			const fd = new FormData();
			fd.append('file', job.file);
			const uploaded = await api.post<UploadedReceipt>(job.ocr ? '/ocr/scan' : '/receipts', fd);
			f.receipt = uploaded;
			f.status = 'done';
			// Saat merevisi, pengajuan ini sendiri bukan duplikat.
			item.duplicates.push(...(uploaded.duplicates ?? []).filter((d) => d.id !== init?.id));
			const r = uploaded.ocr;
			if (r?.status === 'completed' && job.fresh) {
				// Isi hanya field yang berhasil dibaca; sisanya biarkan untuk diisi manual.
				if (r.merchant) item.merchant = r.merchant;
				if (r.transaction_date) item.transaction_date = r.transaction_date;
				if (r.total_amount != null) item.amount = r.total_amount;
				item.fromOcr = { merchant: !!r.merchant, date: !!r.transaction_date, amount: r.total_amount != null };
				item.ocrConfirmed = false;
				readCount++;
			}
		} catch (err) {
			item.files = item.files.filter((x) => x.key !== f.key);
			// Item yang dibuat khusus untuk file ini dan masih kosong ikut dihapus.
			if (job.fresh && item.files.length === 0 && !item.merchant && !item.transaction_date && item.amount == null)
				items = items.filter((i) => i.key !== item.key);
			notifyError(err);
		}
	}

	function removeItem(key: string) {
		items = items.filter((i) => i.key !== key);
	}

	function addManual() {
		if (items.length >= MAX_ITEMS) return notify(`Maksimal ${MAX_ITEMS} item per pengajuan.`, 'error');
		const item = emptyItem();
		items.push(item);
		tick().then(() => document.getElementById(`m-${item.key}`)?.focus());
	}

	// --- Simpan ---

	async function focusFirstProblem() {
		await tick();
		const key = items.find((i) => problems[i.key])?.key;
		document.querySelector(`[data-item="${key}"]`)?.scrollIntoView({ behavior: ms(1) ? 'smooth' : 'auto', block: 'center' });
	}

	async function save(submit: boolean) {
		if (!purpose.trim()) {
			purposeShake = false;
			requestAnimationFrame(() => (purposeShake = true));
			document.getElementById('purpose')?.focus();
			return notify('Keperluan pengajuan wajib diisi.', 'error');
		}
		if (pending) return notify('Tunggu sampai semua struk selesai diunggah.', 'error');
		if (submit) {
			triedSubmit = true;
			if (items.length === 0) return notify('Tambahkan minimal satu item pengeluaran.', 'error');
			const bad = items.findIndex((i) => problems[i.key]);
			if (bad >= 0) {
				focusFirstProblem();
				return notify(`Item ${bad + 1}: ${problems[items[bad].key]}`, 'error');
			}
		}
		saving = submit ? 'submit' : 'draft';
		try {
			const body = {
				category,
				purpose,
				submit,
				items: items.map((i) => ({
					id: i.id,
					merchant: i.merchant,
					transaction_date: i.transaction_date,
					amount: i.amount,
					note: i.note,
					ocr_confirmed: i.ocrConfirmed,
					receipt_ids: i.files.flatMap((f) => (f.receipt ? [f.receipt.id] : []))
				}))
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

	const dropHandlers = {
		ondragenter: (e: DragEvent) => {
			e.preventDefault();
			dragging = true;
		},
		ondragover: (e: DragEvent) => e.preventDefault(),
		ondragleave: (e: DragEvent & { currentTarget: HTMLElement }) => {
			if (!e.currentTarget.contains(e.relatedTarget as Node)) dragging = false;
		},
		ondrop: (e: DragEvent) => {
			e.preventDefault();
			dragging = false;
			addAsItems(e.dataTransfer?.files);
		}
	};
</script>

{#snippet step(n: string, title: string)}
	<h2 class="flex items-center gap-3">
		<span class="code grid size-7 place-items-center rounded-lg bg-chip text-[11px] text-on-chip">{n}</span>
		<span class="display text-[1.35rem] text-ink">{title}</span>
	</h2>
{/snippet}

<form
	class="space-y-5"
	onsubmit={(e) => {
		e.preventDefault();
		save(true);
	}}
>
	<section class="panel reveal p-5 sm:p-6" style="--d: 120ms">
		{@render step('01', 'Pengajuan')}
		<div class="mt-5 grid gap-5 md:grid-cols-[auto_minmax(0,1fr)]">
			<div>
				<span class="label">Kategori</span>
				<Segmented options={CATEGORIES} bind:value={category} label="Kategori" />
				<p class="mt-2 text-[12px] text-muted">Satu pengajuan untuk satu kategori.</p>
			</div>
			<div class={purposeShake ? 'shake' : ''}>
				<label class="label" for="purpose">Keperluan <span class="text-danger">*</span></label>
				<textarea id="purpose" rows="2" class="input" bind:value={purpose}
					placeholder="mis. Kunjungan klien PT ABC di Bekasi, 4–6 Nov"></textarea>
			</div>
		</div>
	</section>

	<section class="reveal space-y-4" style="--d: 180ms">
		<div class="flex flex-wrap items-center justify-between gap-3 px-1">
			{@render step('02', 'Item pengeluaran')}
			<label class="flex cursor-pointer items-center gap-2.5 text-[13px] text-muted select-none">
				Baca otomatis (OCR)
				<button type="button" role="switch" aria-checked={useOcr} class="switch" onclick={() => (useOcr = !useOcr)}
					aria-label="Baca struk otomatis dengan OCR"></button>
			</label>
		</div>

		{#each items as item, i (item.key)}
			<div animate:flip={{ duration: ms(320), easing: ease }} in:fly={{ y: 14, duration: ms(320), easing: ease }}
				out:slide={{ duration: ms(240), easing: ease }}>
				<ItemEditor
					bind:item={items[i]}
					index={i}
					problem={triedSubmit ? problems[item.key] : null}
					onaddfiles={(files) => addToItem(item, files)}
					onremove={() => removeItem(item.key)}
				/>
			</div>
		{/each}

		{#if items.length < MAX_ITEMS}
			<div {...dropHandlers}>
				<label
					class="group relative flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border-[1.5px] border-dashed px-6 text-center transition-[background-color,border-color,transform,padding] duration-300 ease-snap {items.length
						? 'py-7'
						: 'min-h-[16rem] py-10'} {dragging ? 'scale-[1.01] border-ink bg-lime/20' : 'border-line-strong hover:border-faint hover:bg-sunken/60'}"
				>
					<span class="grid size-12 place-items-center rounded-2xl bg-chip text-on-chip shadow-pop transition-transform duration-500 ease-spring group-hover:-translate-y-1 group-hover:-rotate-6 {dragging ? '-translate-y-2 scale-110 -rotate-6' : ''}">
						<UploadSimple size={22} weight="bold" />
					</span>
					<span class="display mt-1 text-lg text-ink">
						{dragging ? 'Lepaskan untuk menambah item' : items.length ? 'Tambah struk lain' : 'Tarik foto atau PDF struk ke sini'}
					</span>
					<span class="text-[13px] text-muted">
						Bisa beberapa sekaligus, tiap struk jadi satu item ·
						<span class="font-medium text-ink underline decoration-line-strong decoration-2 underline-offset-4 transition-colors group-hover:decoration-lime-deep">pilih file</span>
					</span>
					<span class="eyebrow mt-1">JPG · PNG · PDF · maks 5 MB per file</span>
					<input bind:this={dropInput} type="file" multiple accept={ACCEPTED_TYPES.join(',')} class="sr-only"
						onchange={(e) => addAsItems(e.currentTarget.files)} />
				</label>
			</div>
			<div class="flex justify-center">
				<button type="button" class="group btn btn-ghost btn-sm text-muted" onclick={addManual}>
					<Plus size={14} weight="bold" class="transition-transform duration-300 ease-spring group-hover:rotate-90" />
					Tambah item tanpa struk dulu
				</button>
			</div>
		{/if}
	</section>

	<!-- Ringkasan & tombol: tetap terlihat saat menggulir daftar item. -->
	<div class="sticky bottom-24 z-30 lg:bottom-5">
		<div class="panel flex items-center justify-between gap-3 px-4 py-3 shadow-float sm:gap-6 sm:px-5 sm:py-3.5">
			<div class="flex min-w-0 flex-col sm:flex-row sm:items-baseline sm:gap-3">
				<span class="display num text-[1.3rem] text-ink sm:text-[1.6rem]"><CountUp value={total} format={formatRupiah} /></span>
				<span class="truncate text-[12px] text-muted sm:text-[13px]">
					{items.length} item
					{#if pending}
						<span class="inline-flex items-center gap-1.5 text-ink" transition:slide={{ axis: 'x', duration: ms(200) }}>
							· <Spinner size={12} /> {pending} file diunggah
						</span>
					{/if}
				</span>
			</div>
			<div class="flex shrink-0 gap-2">
				<button type="button" class="btn btn-secondary" disabled={busy || pending > 0} onclick={() => save(false)}>
					{#if saving === 'draft'}<Spinner size={14} />{/if} <span class="max-sm:hidden">Simpan draft</span><span class="sm:hidden">Draft</span>
				</button>
				<button type="submit" class="group btn btn-primary" disabled={busy || pending > 0}>
					{#if saving === 'submit'}
						<Spinner size={14} /> Mengirim…
					{:else}
						<span class="max-sm:hidden">Kirim pengajuan</span><span class="sm:hidden">Kirim</span>
						<ArrowRight size={15} weight="bold" class="transition-transform duration-300 ease-spring group-hover:translate-x-1" />
					{/if}
				</button>
			</div>
		</div>
	</div>
</form>
