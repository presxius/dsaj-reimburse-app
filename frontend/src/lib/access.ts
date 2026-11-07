import type { Role } from './types/index.ts';

/**
 * Role yang boleh membuka tiap halaman. Hanya untuk UX: backend tetap menjadi
 * penjaga sebenarnya dan menolak API di luar kewenangan dengan 403.
 * Aturan pertama yang cocok berlaku; halaman yang tidak terdaftar terbuka untuk semua role.
 */
const ALL: Role[] = [
	'employee',
	'admin_transport',
	'admin_consumption',
	'approver',
	'finance',
	'super_admin'
];
const ADMINS: Role[] = ['admin_transport', 'admin_consumption'];

const RULES: { match: RegExp; roles: Role[] }[] = [
	{ match: /^\/reimburse\/new\/?$/, roles: ['employee'] },
	{ match: /^\/reimburse\/\d+\/edit\/?$/, roles: ['employee'] },
	{ match: /^\/reimburse\/?$/, roles: ['employee', 'super_admin'] },
	{ match: /^\/verification(\/|$)/, roles: ADMINS },
	{ match: /^\/approval(\/|$)/, roles: ['approver'] },
	{ match: /^\/finance(\/|$)/, roles: ['finance'] },
	{ match: /^\/reports(\/|$)/, roles: [...ADMINS, 'finance', 'super_admin'] },
	{ match: /^\/users(\/|$)/, roles: ['super_admin'] },
	{ match: /^\/activity(\/|$)/, roles: ['super_admin'] }
];

export const ALL_ROLES = ALL;

export function canAccess(path: string, role: Role): boolean {
	const rule = RULES.find((r) => r.match.test(path));
	return rule ? rule.roles.includes(role) : true;
}
