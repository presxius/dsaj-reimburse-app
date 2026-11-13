export type Role =
	| 'employee'
	| 'admin_transport'
	| 'admin_consumption'
	| 'approver'
	| 'finance'
	| 'super_admin';

export type Category = 'transport' | 'consumption';

export type Status =
	| 'draft'
	| 'submitted'
	| 'under_review'
	| 'revision_required'
	| 'rejected'
	| 'pending_approval'
	| 'approved'
	| 'processing_payment'
	| 'paid';

export type Action =
	| 'submit'
	| 'start_review'
	| 'forward'
	| 'admin_return'
	| 'admin_reject'
	| 'approve'
	| 'approver_return'
	| 'approver_reject'
	| 'process_payment'
	| 'mark_paid';

export interface Department {
	id: number;
	name: string;
}

export interface User {
	id: number;
	name: string;
	email: string;
	role: Role;
	department: Department | null;
	approver: { id: number; name: string } | null;
	is_active: boolean;
}

export interface OcrResult {
	status: 'queued' | 'processing' | 'completed' | 'failed';
	merchant: string | null;
	transaction_date: string | null;
	total_amount: number | null;
	raw_text: string | null;
	/** Skor keyakinan 0-1 per field yang terbaca; null bila engine tidak memberi skor. */
	confidence: Partial<Record<OcrField, number | null>> | null;
	error: string | null;
	processed_at: string | null;
}

export type OcrField = 'merchant' | 'transaction_date' | 'total_amount';

export interface Receipt {
	id: number;
	original_filename: string;
	file_type: string;
	file_size: number;
	uploaded_at: string;
	ocr: OcrResult | null;
}

/** Pengajuan lain yang kemungkinan memakai struk/transaksi yang sama. */
export interface DuplicateMatch {
	id: number;
	code: string;
	status: Status;
	employee: string;
	transaction_date: string;
	amount: number;
	reason: 'same_file' | 'same_data';
}

export interface UploadedReceipt extends Receipt {
	duplicates: DuplicateMatch[];
}

export interface HistoryEntry {
	id: number;
	action: Action;
	from_status: Status | null;
	to_status: Status;
	note: string | null;
	actor: { id: number; name: string; role: Role };
	created_at: string;
}

export interface Payment {
	id: number;
	amount: number | null;
	payment_date: string | null;
	reference: string | null;
	status: 'processing' | 'paid';
	processed_by: string;
}

export interface Reimbursement {
	id: number;
	code: string;
	category: Category;
	merchant: string | null;
	transaction_date: string;
	description: string;
	amount: number;
	status: Status;
	submitted_at: string | null;
	created_at: string;
	employee: { id: number; name: string; department: string | null };
}

export interface ReimbursementDetail extends Reimbursement {
	ocr_confirmed: boolean;
	ocr_corrected: boolean;
	receipt: Receipt | null;
	history: HistoryEntry[];
	payment: Payment | null;
	actions?: Action[];
	duplicates?: DuplicateMatch[];
}

export interface Bucket {
	count: number;
	amount: number;
}

export interface Summary {
	total_count: number;
	total_amount: number;
	by_status: Partial<Record<Status, Bucket>>;
	by_category: Partial<Record<Category, Bucket>>;
}

export interface ReportRow extends Reimbursement {
	payment_date: string | null;
	payment_reference: string | null;
}

export interface ActivityLog {
	id: number;
	user: string | null;
	action: string;
	entity: string | null;
	entity_id: number | null;
	detail: string | null;
	created_at: string;
}
