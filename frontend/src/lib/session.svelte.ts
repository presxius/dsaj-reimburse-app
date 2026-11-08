import type { Role, User } from './types/index.ts';

export const auth = $state<{ user: User | null; loaded: boolean }>({ user: null, loaded: false });

export function hasRole(...roles: Role[]): boolean {
	return !!auth.user && roles.includes(auth.user.role);
}

type Toast = { id: number; kind: 'success' | 'error'; message: string };
export const toasts = $state<Toast[]>([]);
let nextId = 1;

export function notify(message: string, kind: Toast['kind'] = 'success') {
	const id = nextId++;
	toasts.push({ id, kind, message });
	setTimeout(() => dismiss(id), TOAST_MS);
}

export const TOAST_MS = 4000;

export function dismiss(id: number) {
	const i = toasts.findIndex((t) => t.id === id);
	if (i >= 0) toasts.splice(i, 1);
}

export function notifyError(e: unknown) {
	notify(e instanceof Error ? e.message : 'Terjadi kesalahan.', 'error');
}
