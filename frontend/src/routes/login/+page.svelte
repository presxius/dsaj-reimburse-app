<script lang="ts">
	import { goto } from '$app/navigation';
	import { fly } from 'svelte/transition';
	import { api } from '#lib/services/api.ts';
	import { auth } from '#lib/session.svelte.ts';
	import { ease, ms } from '#lib/motion.ts';
	import type { User } from '#lib/types/index.ts';
	import Logo from '#lib/components/Logo.svelte';
	import Spinner from '#lib/components/Spinner.svelte';
	import ArrowRight from 'phosphor-svelte/lib/ArrowRightIcon';
	import Eye from 'phosphor-svelte/lib/EyeIcon';
	import EyeSlash from 'phosphor-svelte/lib/EyeSlashIcon';
	import WarningCircle from 'phosphor-svelte/lib/WarningCircleIcon';
	import Car from 'phosphor-svelte/lib/CarIcon';

	let email = $state('');
	let password = $state('');
	let loading = $state(false);
	let reveal = $state(false);
	let shake = $state(false);
	let error = $state('');

	async function submit(e: SubmitEvent) {
		e.preventDefault();
		loading = true;
		error = '';
		try {
			auth.user = await api.post<User>('/auth/login', { email, password });
			goto('/dashboard');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Terjadi kesalahan.';
			// Lepas lalu pasang lagi kelasnya agar animasi bisa diulang pada percobaan berikutnya.
			shake = false;
			requestAnimationFrame(() => (shake = true));
		} finally {
			loading = false;
		}
	}

	const DEMO_STEPS = ['Submitted', 'Under Review', 'Approved', 'Paid'];
</script>

<div class="grid min-h-[100dvh] lg:grid-cols-[1.05fr_1fr]">
	<!-- Panggung produk: kartu pengajuan yang berjalan dari diajukan sampai dibayar. -->
	<aside class="relative hidden overflow-hidden bg-[#161613] p-12 text-[#f0efe9] lg:flex lg:flex-col dark:border-r dark:border-line">
		<div class="grid-bg pointer-events-none absolute inset-0" aria-hidden="true"></div>
		<div class="relative"><Logo inverse /></div>

		<div class="relative my-auto py-12" aria-hidden="true">
			<div class="mx-auto w-[22rem]">
				<!-- kartu belakang memberi kedalaman -->
				<div class="mx-6 h-6 rounded-t-2xl border border-b-0 border-white/10 bg-white/[0.04]"></div>
				<div class="demo-card rounded-2xl border border-white/10 bg-[#1f1f1c] p-5 shadow-[0_32px_64px_-24px_rgb(0_0_0/0.8)]">
					<div class="flex items-center gap-3">
						<span class="grid size-10 place-items-center rounded-xl bg-[#d6f25f] text-[#192300]">
							<Car size={20} weight="duotone" />
						</span>
						<div class="min-w-0 flex-1">
							<div class="font-medium">Blue Taxi</div>
							<div class="code text-[12px] text-[#a19f95]">RB-202611-00142 · Transportasi</div>
						</div>
					</div>
					<div class="mt-6 flex items-end justify-between">
						<div>
							<div class="eyebrow text-[#a19f95]">Nominal</div>
							<div class="display num mt-1 text-[2.4rem]">Rp 87.500</div>
						</div>
						<div class="relative mb-1.5 h-6 w-32 text-right text-[13px] font-medium">
							{#each DEMO_STEPS as s, i (s)}
								<span class="demo-label absolute inset-0 flex items-center justify-end gap-1.5" style="--i: {i}">
									{#if s === 'Paid'}
										<span class="grid size-4 place-items-center rounded-full bg-[#d6f25f]">
											<svg viewBox="0 0 16 16" class="size-2.5"><path d="m3.5 8.5 3 3 6-6.5" fill="none"
													stroke="#192300" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" /></svg>
										</span>
									{:else}
										<span class="size-1.5 rounded-full bg-[#f0efe9]/70"></span>
									{/if}
									{s}
								</span>
							{/each}
						</div>
					</div>
					<div class="mt-5 h-1.5 overflow-hidden rounded-full bg-white/10">
						<div class="demo-fill h-full origin-left rounded-full bg-[#d6f25f]"></div>
					</div>
					<div class="mt-2.5 flex justify-between text-[11px] text-[#6f6d65]">
						<span>Diajukan</span><span>Verifikasi</span><span>Disetujui</span><span>Dibayar</span>
					</div>
				</div>
			</div>
		</div>

		<div class="relative max-w-md">
			<h2 class="display text-[3.25rem] leading-[0.98]">
				Struk masuk,<br />uang <span class="mark [--mark-delay:700ms] [--mark-from:80%] [--mark-to:96%]">kembali</span>.
			</h2>
			<p class="mt-5 max-w-sm text-[15px] text-[#a19f95]">
				Foto struk transportasi atau konsumsi, biarkan OCR mengisi formnya, lalu pantau sampai dibayar.
			</p>
		</div>
	</aside>

	<main class="flex flex-col px-6 py-10 sm:px-12">
		<div class="lg:hidden"><Logo /></div>
		<form class="m-auto w-full max-w-sm py-10 {shake ? 'shake' : ''}" onsubmit={submit}>
			<p class="eyebrow reveal">Sistem reimburse internal</p>
			<h1 class="display reveal mt-3 text-[2.5rem] text-ink" style="--d: 40ms">Masuk</h1>
			<p class="reveal mt-2 text-[15px] text-muted" style="--d: 80ms">Gunakan akun perusahaan Anda.</p>

			<div class="reveal mt-8 space-y-4" style="--d: 120ms">
				<div>
					<label class="label" for="email">Email</label>
					<input id="email" type="email" class="input h-11" bind:value={email} required autocomplete="username"
						placeholder="nama@dsaj.co.id" />
				</div>
				<div>
					<label class="label" for="password">Password</label>
					<div class="relative">
						<input id="password" type={reveal ? 'text' : 'password'} class="input h-11 pr-11" bind:value={password}
							required autocomplete="current-password" />
						<button
							type="button"
							class="absolute inset-y-0 right-1 my-auto grid size-9 place-items-center rounded-lg text-faint transition-colors hover:bg-sunken hover:text-ink"
							onclick={() => (reveal = !reveal)}
							aria-label={reveal ? 'Sembunyikan password' : 'Tampilkan password'}
							aria-pressed={reveal}
						>
							{#key reveal}
								<span class="grid" in:fly={{ y: 6, duration: ms(220), easing: ease }}>
									{#if reveal}<EyeSlash size={18} />{:else}<Eye size={18} />{/if}
								</span>
							{/key}
						</button>
					</div>
				</div>
			</div>

			{#if error}
				<p class="mt-4 flex items-start gap-2 text-[13px] text-danger" role="alert" in:fly={{ y: -4, duration: ms(200), easing: ease }}>
					<WarningCircle size={17} weight="fill" class="mt-px shrink-0" />
					{error}
				</p>
			{/if}

			<button class="group btn btn-primary btn-lg reveal mt-6 w-full" style="--d: 160ms" disabled={loading}>
				{#if loading}
					<Spinner /> Memeriksa…
				{:else}
					Masuk
					<ArrowRight size={17} weight="bold" class="transition-transform duration-300 ease-spring group-hover:translate-x-1" />
				{/if}
			</button>
		</form>
		<p class="text-center text-[12px] text-faint">PT. Duta Sarana Abadi Jaya</p>
	</main>
</div>

<style>
	/* Kisi titik halus di panggung produk. */
	.grid-bg {
		background-image: radial-gradient(rgb(255 255 255 / 0.07) 1px, transparent 1px);
		background-size: 22px 22px;
		mask-image: radial-gradient(ellipse at 50% 45%, black 20%, transparent 70%);
	}
	.demo-card {
		animation: float 6s ease-in-out infinite;
	}
	.demo-fill {
		animation: demo-fill 8s var(--ease) infinite;
	}
	.demo-label {
		opacity: 0;
		animation: demo-label 8s var(--ease) infinite;
		animation-delay: calc(var(--i) * 2s);
	}
	@keyframes float {
		50% {
			transform: translateY(-8px);
		}
	}
	@keyframes demo-fill {
		0%,
		20% {
			transform: scaleX(0.12);
		}
		25%,
		45% {
			transform: scaleX(0.42);
		}
		50%,
		70% {
			transform: scaleX(0.72);
		}
		75%,
		100% {
			transform: scaleX(1);
		}
	}
	@keyframes demo-label {
		0% {
			opacity: 0;
			transform: translateY(8px);
		}
		4%,
		22% {
			opacity: 1;
			transform: none;
		}
		25%,
		100% {
			opacity: 0;
			transform: translateY(-8px);
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.demo-label:last-child {
			opacity: 1;
		}
	}
</style>
