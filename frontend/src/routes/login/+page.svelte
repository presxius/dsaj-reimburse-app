<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '#lib/services/api.ts';
	import { auth, notifyError } from '#lib/session.svelte.ts';
	import type { User } from '#lib/types/index.ts';
	import Receipt from 'phosphor-svelte/lib/ReceiptIcon';
	import ArrowRight from 'phosphor-svelte/lib/ArrowRightIcon';
	import Eye from 'phosphor-svelte/lib/EyeIcon';
	import EyeSlash from 'phosphor-svelte/lib/EyeSlashIcon';
	import Stamp from '#lib/components/Stamp.svelte';

	let email = $state('');
	let password = $state('');
	let loading = $state(false);
	let reveal = $state(false);
	let shake = $state(false);

	async function submit(e: SubmitEvent) {
		e.preventDefault();
		loading = true;
		try {
			auth.user = await api.post<User>('/auth/login', { email, password });
			goto('/dashboard');
		} catch (err) {
			notifyError(err);
			// Lepas lalu pasang lagi kelasnya agar animasi bisa diulang pada percobaan berikutnya.
			shake = false;
			requestAnimationFrame(() => (shake = true));
		} finally {
			loading = false;
		}
	}
</script>

<div class="grid min-h-[100dvh] lg:grid-cols-[1.1fr_1fr]">
	<aside class="hidden flex-col justify-between overflow-hidden bg-accent-soft p-12 lg:flex">
		<div class="flex items-center gap-2.5 font-semibold tracking-tight">
			<span class="grid h-7 w-7 place-items-center rounded-lg bg-accent text-on-accent">
				<Receipt size={16} weight="bold" />
			</span>
			Reimburse DSAJ
		</div>

		<!-- Contoh slip: dicetak dari mesin, lalu distempel lunas. -->
		<div class="mx-auto w-72" aria-hidden="true">
			<div class="relative z-10 h-3.5 rounded-full bg-fg shadow-[inset_0_-3px_0_rgb(255_255_255/0.12)]"></div>
			<div class="-mt-1.5 px-3 [clip-path:inset(0_-48px_-48px_-48px)]">
				<div class="print slip-wrap">
					<div class="slip text-sm">
						<div class="text-center font-mono text-[11px] tracking-[0.2em] text-muted">BUKTI REIMBURSE</div>
						<div class="mt-1 text-center font-mono text-xs text-faint">RB-202611-00142</div>
						<hr class="slip-rule" />
						<div class="font-medium">Blue Taxi</div>
						<div class="text-muted">Taksi ke kantor klien</div>
						<div class="mt-2 flex justify-between font-mono text-xs text-muted">
							<span>Transportasi</span><span>06 Nov 2026</span>
						</div>
						<hr class="slip-rule" />
						<div class="flex items-baseline justify-between font-mono">
							<span class="text-xs text-muted">TOTAL</span>
							<span class="text-lg font-semibold">Rp 87.500</span>
						</div>
						<Stamp status="paid" class="absolute top-[4.75rem] right-4 [--stamp-delay:1.5s]" />
					</div>
				</div>
			</div>
		</div>

		<div class="max-w-md">
			<h2 class="text-4xl leading-[1.1] font-semibold tracking-tight text-balance">
				Foto struknya, sisanya kami bantu.
			</h2>
			<p class="mt-4 text-muted">
				Ajukan reimburse transportasi dan konsumsi, lalu pantau statusnya tanpa cetak dokumen.
			</p>
		</div>
	</aside>

	<main class="flex items-center px-6 py-12 sm:px-12">
		<form class="mx-auto w-full max-w-sm space-y-5 {shake ? 'shake' : ''}" onsubmit={submit}>
			<div>
				<span class="mb-6 grid h-9 w-9 place-items-center rounded-lg bg-accent text-on-accent lg:hidden">
					<Receipt size={20} weight="bold" />
				</span>
				<h1 class="text-2xl font-semibold tracking-tight">Masuk</h1>
				<p class="mt-1 text-sm text-muted">Gunakan akun perusahaan Anda.</p>
			</div>
			<div>
				<label class="label" for="email">Email</label>
				<input id="email" type="email" class="input" bind:value={email} required autocomplete="username"
					placeholder="nama@dsaj.co.id" />
			</div>
			<div>
				<label class="label" for="password">Password</label>
				<div class="relative">
					<input id="password" type={reveal ? 'text' : 'password'} class="input pr-10" bind:value={password}
						required autocomplete="current-password" />
					<button
						type="button"
						class="absolute inset-y-0 right-0 grid w-10 place-items-center text-faint transition-colors hover:text-fg"
						onclick={() => (reveal = !reveal)}
						aria-label={reveal ? 'Sembunyikan password' : 'Tampilkan password'}
						aria-pressed={reveal}
					>
						{#if reveal}<EyeSlash size={18} />{:else}<Eye size={18} />{/if}
					</button>
				</div>
			</div>
			<button class="group btn btn-primary w-full py-2.5" disabled={loading}>
				{loading ? 'Memproses...' : 'Masuk'}
				{#if !loading}
					<ArrowRight size={16} class="transition-transform duration-200 group-hover:translate-x-0.5" />
				{/if}
			</button>
		</form>
	</main>
</div>
