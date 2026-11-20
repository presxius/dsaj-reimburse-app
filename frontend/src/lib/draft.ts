import { OCR_LOW_CONFIDENCE } from './labels.ts';
import type { DuplicateMatch, OcrField, OcrResult, Receipt, ReimbursementItem } from './types/index.ts';

// Sama dengan MAX_ITEMS dan MAX_RECEIPTS_PER_ITEM di backend/app/models.py.
export const MAX_ITEMS = 30;
export const MAX_FILES_PER_ITEM = 5;
export const MAX_FILE_SIZE = 5 * 1024 * 1024;
export const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'application/pdf'];

/** Satu file bukti di form: sedang diunggah, atau sudah tersimpan di server. */
export interface DraftFile {
	key: string;
	receipt: Receipt | null;
	name: string;
	isPdf: boolean;
	/** URL blob untuk pratinjau sebelum/ketika diunggah. */
	localUrl: string | null;
	status: 'queued' | 'uploading' | 'done';
}

/** Satu item pengeluaran di form. */
export interface DraftItem {
	key: string;
	id?: number;
	merchant: string;
	transaction_date: string;
	amount: number | null;
	note: string;
	files: DraftFile[];
	ocrConfirmed: boolean;
	/** Field yang barusan diisi dari OCR (untuk tag & animasi). */
	fromOcr: { merchant?: boolean; date?: boolean; amount?: boolean };
	duplicates: DuplicateMatch[];
	reviewNote: string | null;
}

let seq = 0;
export const newKey = () => `k${++seq}`;

export function emptyItem(): DraftItem {
	return {
		key: newKey(),
		merchant: '',
		transaction_date: '',
		amount: null,
		note: '',
		files: [],
		ocrConfirmed: false,
		fromOcr: {},
		duplicates: [],
		reviewNote: null
	};
}

export function fromSaved(item: ReimbursementItem): DraftItem {
	return {
		key: newKey(),
		id: item.id,
		merchant: item.merchant ?? '',
		transaction_date: item.transaction_date,
		amount: item.amount,
		note: item.note ?? '',
		files: item.receipts.map((r) => ({
			key: newKey(),
			receipt: r,
			name: r.original_filename,
			isPdf: r.file_type === 'application/pdf',
			localUrl: null,
			status: 'done'
		})),
		ocrConfirmed: item.ocr_confirmed,
		fromOcr: {},
		duplicates: [],
		reviewNote: item.review_note
	};
}

/** Hasil OCR acuan item: file pertama yang berhasil dibaca (sama dengan backend). */
export function ocrOf(item: DraftItem): OcrResult | null {
	return item.files.find((f) => f.receipt?.ocr?.status === 'completed')?.receipt?.ocr ?? null;
}

/** Hasil OCR yang gagal (untuk pesan), bila tidak ada yang berhasil. */
export function failedOcrOf(item: DraftItem): OcrResult | null {
	if (ocrOf(item)) return null;
	return item.files.find((f) => f.receipt?.ocr?.status === 'failed')?.receipt?.ocr ?? null;
}

export function isLow(ocr: OcrResult | null, field: OcrField): boolean {
	const c = ocr?.confidence?.[field];
	return c != null && c < OCR_LOW_CONFIDENCE;
}

/** Thumbnail file: blob lokal, pratinjau PDF dari server, atau file asli. */
export function thumbUrl(f: DraftFile): string | null {
	if (f.receipt) return f.isPdf ? `/api/receipts/${f.receipt.id}/preview` : `/api/receipts/${f.receipt.id}/file`;
	return f.isPdf ? null : f.localUrl;
}

/** Pesan kesalahan item yang menghalangi pengiriman, atau null bila siap. */
export function submitProblem(item: DraftItem): string | null {
	if (item.files.some((f) => f.status !== 'done')) return 'struk masih diunggah.';
	if (item.files.length === 0) return 'bukti transaksi wajib dilampirkan.';
	if (!item.transaction_date) return 'tanggal transaksi wajib diisi.';
	if (item.amount == null || item.amount <= 0) return 'nominal wajib diisi.';
	if (ocrOf(item) && !item.ocrConfirmed) return 'centang konfirmasi pemeriksaan hasil OCR.';
	return null;
}
