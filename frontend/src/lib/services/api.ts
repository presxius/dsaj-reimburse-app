export class ApiError extends Error {
	constructor(
		message: string,
		public status: number
	) {
		super(message);
	}
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
	const init: RequestInit = { method, credentials: 'same-origin', headers: {} };
	if (body instanceof FormData) {
		init.body = body;
	} else if (body !== undefined) {
		init.body = JSON.stringify(body);
		(init.headers as Record<string, string>)['Content-Type'] = 'application/json';
	}
	let res: Response;
	try {
		res = await fetch(`/api${path}`, init);
	} catch {
		throw new ApiError('Tidak dapat terhubung ke server.', 0);
	}
	const data = res.headers.get('content-type')?.includes('application/json')
		? await res.json()
		: null;
	if (!res.ok) throw new ApiError(data?.error ?? `Terjadi kesalahan (${res.status}).`, res.status);
	return data as T;
}

export const api = {
	get: <T>(path: string) => request<T>('GET', path),
	post: <T>(path: string, body?: unknown) => request<T>('POST', path, body ?? {}),
	put: <T>(path: string, body: unknown) => request<T>('PUT', path, body),
	patch: <T>(path: string, body: unknown) => request<T>('PATCH', path, body)
};

export function query(params: Record<string, string | undefined>): string {
	const qs = new URLSearchParams();
	for (const [k, v] of Object.entries(params)) if (v) qs.set(k, v);
	const s = qs.toString();
	return s ? `?${s}` : '';
}
