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

// Deskripsi status sesuai PRD §8.4; tampil sebagai keterangan (tooltip) pada badge.
export const STATUS_HINT: Record<Status, string> = {
	draft: 'Pengajuan masih dalam proses pengisian.',
	submitted: 'Pengajuan telah dikirim oleh karyawan.',
	under_review: 'Pengajuan sedang diperiksa admin.',
	revision_required: 'Pengajuan dikembalikan untuk diperbaiki.',
	rejected: 'Pengajuan ditolak oleh admin atau atasan.',
	pending_approval: 'Pengajuan menunggu persetujuan atasan.',
	approved: 'Pengajuan telah disetujui atasan.',
	processing_payment: 'Finance sedang memproses pembayaran.',
	paid: 'Pembayaran reimburse telah dilakukan.'
};

export const initials = (name: string) =>
	name
		.split(/\s+/)
		.filter(Boolean)
		.slice(0, 2)
		.map((w) => w[0].toUpperCase())
		.join('');

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
