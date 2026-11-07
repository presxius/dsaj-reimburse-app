import type { Action, Category, Role, Status } from './types/index.ts';

export const ROLE_LABEL: Record<Role, string> = {
	employee: 'Karyawan',
	admin_transport: 'Admin Reimburse Transportasi',
	admin_consumption: 'Admin Reimburse Konsumsi',
	approver: 'Atasan',
	finance: 'Finance',
	super_admin: 'Super Admin'
};

export const CATEGORY_LABEL: Record<Category, string> = {
	transport: 'Transportasi',
	consumption: 'Konsumsi'
};

export const STATUS_LABEL: Record<Status, string> = {
	draft: 'Draft',
	submitted: 'Submitted',
	under_review: 'Under Review',
	revision_required: 'Revision Required',
	rejected: 'Rejected',
	pending_approval: 'Pending Approval',
	approved: 'Approved',
	processing_payment: 'Processing Payment',
	paid: 'Paid'
};

export const STATUS_COLOR: Record<Status, string> = {
	draft: 'bg-slate-100 text-slate-700',
	submitted: 'bg-sky-100 text-sky-800',
	under_review: 'bg-indigo-100 text-indigo-800',
	revision_required: 'bg-amber-100 text-amber-800',
	rejected: 'bg-red-100 text-red-800',
	pending_approval: 'bg-violet-100 text-violet-800',
	approved: 'bg-teal-100 text-teal-800',
	processing_payment: 'bg-orange-100 text-orange-800',
	paid: 'bg-green-100 text-green-800'
};

export const ACTION_LABEL: Record<Action, string> = {
	submit: 'Kirim pengajuan',
	start_review: 'Mulai review',
	forward: 'Teruskan ke atasan',
	admin_return: 'Kembalikan untuk revisi',
	admin_reject: 'Tolak',
	approve: 'Setujui',
	approver_return: 'Kembalikan untuk revisi',
	approver_reject: 'Tolak',
	process_payment: 'Proses pembayaran',
	mark_paid: 'Tandai sudah dibayar'
};

export const ALL_STATUSES = Object.keys(STATUS_LABEL) as Status[];

const rupiah = new Intl.NumberFormat('id-ID', {
	style: 'currency',
	currency: 'IDR',
	maximumFractionDigits: 0
});

export const formatRupiah = (n: number | null | undefined) => (n == null ? '-' : rupiah.format(n));

export function formatDate(iso: string | null | undefined, withTime = false): string {
	if (!iso) return '-';
	const d = new Date(withTime ? iso + 'Z' : iso + 'T00:00:00');
	return d.toLocaleString('id-ID', {
		day: '2-digit',
		month: 'short',
		year: 'numeric',
		...(withTime ? { hour: '2-digit', minute: '2-digit' } : {})
	});
}
