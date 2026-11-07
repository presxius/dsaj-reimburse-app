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
	draft: 'bg-subtle text-muted',
	submitted: 'bg-sky-500/10 text-sky-700 dark:text-sky-300',
	under_review: 'bg-blue-500/10 text-blue-700 dark:text-blue-300',
	revision_required: 'bg-amber-500/10 text-amber-700 dark:text-amber-300',
	rejected: 'bg-red-500/10 text-red-700 dark:text-red-300',
	pending_approval: 'bg-cyan-500/10 text-cyan-700 dark:text-cyan-300',
	approved: 'bg-accent-soft text-accent',
	processing_payment: 'bg-orange-500/10 text-orange-700 dark:text-orange-300',
	paid: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300'
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
