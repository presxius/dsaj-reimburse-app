<script lang="ts">
	import '../app.css';
	import favicon from '#lib/assets/favicon.svg';
	import Toasts from '#lib/components/Toasts.svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { ROLE_LABEL } from '#lib/labels.ts';
	import { api } from '#lib/services/api.ts';
	import { auth, notifyError } from '#lib/session.svelte.ts';
	import type { Role, User } from '#lib/types/index.ts';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();
	let menuOpen = $state(false);

	const NAV: { href: string; label: string; roles: Role[] }[] = [
		{ href: '/dashboard', label: 'Dashboard', roles: ['employee', 'admin_transport', 'admin_consumption', 'approver', 'finance', 'super_admin'] },
		{ href: '/reimburse/new', label: 'Ajukan Reimburse', roles: ['employee'] },
		{ href: '/reimburse', label: 'Riwayat Pengajuan', roles: ['employee'] },
		{ href: '/verification', label: 'Verifikasi', roles: ['admin_transport', 'admin_consumption'] },
		{ href: '/approval', label: 'Persetujuan', roles: ['approver'] },
		{ href: '/finance', label: 'Pembayaran', roles: ['finance'] },
		{ href: '/reimburse', label: 'Semua Pengajuan', roles: ['super_admin'] },
		{ href: '/reports', label: 'Laporan', roles: ['admin_transport', 'admin_consumption', 'finance', 'super_admin'] },
		{ href: '/users', label: 'Pengguna & Departemen', roles: ['super_admin'] },
		{ href: '/activity', label: 'Log Aktivitas', roles: ['super_admin'] },
		{ href: '/profile', label: 'Profil', roles: ['employee', 'admin_transport', 'admin_consumption', 'approver', 'finance', 'super_admin'] }
	];

	const isLogin = $derived(page.url.pathname === '/login');
	const nav = $derived(NAV.filter((n) => auth.user && n.roles.includes(auth.user.role)));

	$effect(() => {
		if (auth.loaded) return;
		api
			.get<User>('/auth/me')
			.then((u) => (auth.user = u))
			.catch(() => (auth.user = null))
			.finally(() => (auth.loaded = true));
	});

	$effect(() => {
		if (!auth.loaded) return;
		if (!auth.user && !isLogin) goto('/login');
		else if (auth.user && isLogin) goto('/dashboard');
	});

	function isActive(href: string) {
		const p = page.url.pathname;
		if (href === '/reimburse') return p === '/reimburse';
		return p === href || p.startsWith(href + '/');
	}

	async function logout() {
		try {
			await api.post('/auth/logout');
			auth.user = null;
			goto('/login');
		} catch (e) {
			notifyError(e);
		}
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Reimburse DSAJ</title>
</svelte:head>

<Toasts />

{#if !auth.loaded}
	<div class="grid min-h-screen place-items-center text-slate-400">Memuat...</div>
{:else if isLogin}
	{@render children()}
{:else if auth.user}
	<div class="min-h-screen bg-slate-50 lg:flex">
		<!-- Bar atas (mobile) -->
		<header class="flex items-center justify-between bg-brand-900 px-4 py-3 text-white lg:hidden">
			<span class="font-semibold">Reimburse DSAJ</span>
			<button class="rounded px-2 py-1 hover:bg-white/10" onclick={() => (menuOpen = !menuOpen)}
				aria-label="Menu">☰</button
			>
		</header>

		<aside
			class="{menuOpen ? 'block' : 'hidden'} w-full shrink-0 bg-brand-900 text-slate-200 lg:sticky lg:top-0 lg:flex lg:h-screen lg:w-64 lg:flex-col"
		>
			<div class="hidden px-5 py-5 lg:block">
				<div class="text-lg font-bold text-white">Reimburse DSAJ</div>
				<div class="text-xs text-slate-400">PT. Duta Sarana Abadi Jaya</div>
			</div>
			<nav class="flex-1 space-y-1 px-3 py-2">
				{#each nav as item (item.label)}
					<a
						href={item.href}
						onclick={() => (menuOpen = false)}
						class="block rounded-lg px-3 py-2 text-sm {isActive(item.href)
							? 'bg-white/15 font-medium text-white'
							: 'hover:bg-white/10'}">{item.label}</a
					>
				{/each}
			</nav>
			<div class="border-t border-white/10 px-5 py-4 text-sm">
				<div class="font-medium text-white">{auth.user.name}</div>
				<div class="text-xs text-slate-400">{ROLE_LABEL[auth.user.role]}</div>
				<button class="mt-3 text-xs text-slate-300 underline hover:text-white" onclick={logout}
					>Keluar</button
				>
			</div>
		</aside>

		<main class="min-w-0 flex-1 p-4 lg:p-8">
			{@render children()}
		</main>
	</div>
{/if}
