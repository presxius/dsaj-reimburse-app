<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '#lib/services/api.ts';
	import { auth, notifyError } from '#lib/session.svelte.ts';
	import type { User } from '#lib/types/index.ts';
	import Receipt from 'phosphor-svelte/lib/ReceiptIcon';

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

<div class="grid min-h-[100dvh] lg:grid-cols-[1.1fr_1fr]">
	<aside class="hidden flex-col justify-between bg-accent-soft p-12 lg:flex">
		<div class="flex items-center gap-2.5 font-semibold tracking-tight">
			<Receipt size={22} class="text-accent" />
			Reimburse DSAJ
		</div>
		<div class="max-w-md">
			<h2 class="text-4xl leading-[1.1] font-semibold tracking-tight text-balance">
				Foto struknya, sisanya kami bantu.
			</h2>
			<p class="mt-4 text-muted">
				Ajukan reimburse transportasi dan konsumsi, pantau statusnya, tanpa cetak dokumen.
			</p>
		</div>
		<div class="text-xs text-muted">PT. Duta Sarana Abadi Jaya</div>
	</aside>

	<main class="flex items-center px-6 py-12 sm:px-12">
		<form class="mx-auto w-full max-w-sm space-y-5" onsubmit={submit}>
			<div>
				<h1 class="text-2xl font-semibold tracking-tight">Masuk</h1>
				<p class="mt-1 text-sm text-muted">Gunakan akun perusahaan Anda.</p>
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
	</main>
</div>
