<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '#lib/services/api.ts';
	import { auth, notifyError } from '#lib/session.svelte.ts';
	import type { User } from '#lib/types/index.ts';

	let email = $state('');
	let password = $state('');
	let loading = $state(false);

	async function submit(e: SubmitEvent) {
		e.preventDefault();
		loading = true;
		try {
			auth.user = await api.post<User>('/auth/login', { email, password });
			goto('/dashboard');
		} catch (err) {
			notifyError(err);
		} finally {
			loading = false;
		}
	}
</script>

<div class="grid min-h-screen place-items-center bg-gradient-to-br from-brand-900 to-brand-700 p-4">
	<form class="w-full max-w-sm space-y-4 rounded-2xl bg-white p-8 shadow-xl" onsubmit={submit}>
		<div class="text-center">
			<h1 class="text-xl font-bold text-slate-800">Sistem Reimburse</h1>
			<p class="text-sm text-slate-500">PT. Duta Sarana Abadi Jaya</p>
		</div>
		<div>
			<label class="label" for="email">Email</label>
			<input id="email" type="email" class="input" bind:value={email} required autocomplete="username" />
		</div>
		<div>
			<label class="label" for="password">Password</label>
			<input id="password" type="password" class="input" bind:value={password} required
				autocomplete="current-password" />
		</div>
		<button class="btn btn-primary w-full" disabled={loading}>{loading ? 'Memproses...' : 'Masuk'}</button>
	</form>
</div>
