<script lang="ts">
	import '../app.css';
	import favicon from '#lib/assets/favicon.svg';
	import Toasts from '#lib/components/Toasts.svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { ROLE_LABEL } from '#lib/labels.ts';
	import { api } from '#lib/services/api.ts';
	import { auth, notify, notifyError } from '#lib/session.svelte.ts';
	import { ALL_ROLES, canAccess } from '#lib/access.ts';
	import type { Role, User } from '#lib/types/index.ts';
	import { untrack, type Component } from 'svelte';
	import { fly } from 'svelte/transition';
	import { ease, ms, slider } from '#lib/motion.ts';
	import Receipt from 'phosphor-svelte/lib/ReceiptIcon';
	import type { LayoutProps } from './$types';
	import SquaresFour from 'phosphor-svelte/lib/SquaresFourIcon';
	import PlusCircle from 'phosphor-svelte/lib/PlusCircleIcon';
	import ClockCounterClockwise from 'phosphor-svelte/lib/ClockCounterClockwiseIcon';
	import ClipboardText from 'phosphor-svelte/lib/ClipboardTextIcon';
	import CheckSquare from 'phosphor-svelte/lib/CheckSquareIcon';
	import Wallet from 'phosphor-svelte/lib/WalletIcon';
	import Stack from 'phosphor-svelte/lib/StackIcon';
	import ChartBar from 'phosphor-svelte/lib/ChartBarIcon';
	import UsersThree from 'phosphor-svelte/lib/UsersThreeIcon';
	import ListMagnifyingGlass from 'phosphor-svelte/lib/ListMagnifyingGlassIcon';
	import UserCircle from 'phosphor-svelte/lib/UserCircleIcon';
	import Sun from 'phosphor-svelte/lib/SunIcon';
	import Moon from 'phosphor-svelte/lib/MoonIcon';
	import SignOut from 'phosphor-svelte/lib/SignOutIcon';
	import List from 'phosphor-svelte/lib/ListIcon';
	import X from 'phosphor-svelte/lib/XIcon';

	let { children }: LayoutProps = $props();
	let menuOpen = $state(false);
	let theme = $state<'light' | 'dark'>('light');

	const ALL = ALL_ROLES;
	const [send, receive] = slider();
	// svelte-ignore non_reactive_update
	const NAV: { href: string; label: string; icon: Component<any>; roles: Role[] }[] = [
		{ href: '/dashboard', label: 'Dashboard', icon: SquaresFour, roles: ALL },
		{ href: '/reimburse/new', label: 'Ajukan Reimburse', icon: PlusCircle, roles: ['employee'] },
		{ href: '/reimburse', label: 'Riwayat Pengajuan', icon: ClockCounterClockwise, roles: ['employee'] },
		{ href: '/verification', label: 'Verifikasi', icon: ClipboardText, roles: ['admin_transport', 'admin_consumption'] },
		{ href: '/approval', label: 'Persetujuan', icon: CheckSquare, roles: ['approver'] },
		{ href: '/finance', label: 'Pembayaran', icon: Wallet, roles: ['finance'] },
		{ href: '/reimburse', label: 'Semua Pengajuan', icon: Stack, roles: ['super_admin'] },
		{ href: '/reports', label: 'Laporan', icon: ChartBar, roles: ['admin_transport', 'admin_consumption', 'finance', 'super_admin'] },
		{ href: '/users', label: 'Pengguna', icon: UsersThree, roles: ['super_admin'] },
		{ href: '/activity', label: 'Log Aktivitas', icon: ListMagnifyingGlass, roles: ['super_admin'] },
		{ href: '/profile', label: 'Profil', icon: UserCircle, roles: ALL }
	];

	const isLogin = $derived(page.url.pathname === '/login');
	const nav = $derived(NAV.filter((n) => auth.user && n.roles.includes(auth.user.role)));
	// Halaman di luar kewenangan role tidak dirender sama sekali (lihat access.ts).
	const allowed = $derived(!auth.user || canAccess(page.url.pathname, auth.user.role));

	$effect(() => {
		theme = document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';
	});

	function toggleTheme() {
		theme = theme === 'dark' ? 'light' : 'dark';
		document.documentElement.dataset.theme = theme;
		try {
			localStorage.setItem('theme', theme);
		} catch {
			/* penyimpanan diblokir; tema tetap berlaku untuk sesi ini */
		}
	}

	$effect(() => {
		if (auth.loaded) return;
		api
			.get<User>('/auth/me')
			.then((u) => {
				auth.user = u;
			})
			.catch(() => {
				auth.user = null;
			})
			.finally(() => (auth.loaded = true));
	});

	$effect(() => {
		if (!auth.loaded) return;
		if (!auth.user && !isLogin) goto('/login');
		else if (auth.user && isLogin) goto('/dashboard');
		else if (auth.user && !allowed) {
			// notify menulis ke state toast; jangan dilacak efek ini agar tidak terpicu berulang.
			untrack(() => notify('Anda tidak memiliki akses ke halaman tersebut.', 'error'));
			goto('/dashboard', { replace: true });
		}
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

{#snippet themeButton()}
	<button
		class="grid h-8 w-8 place-items-center rounded-lg text-muted transition-colors hover:bg-subtle hover:text-fg"
		onclick={toggleTheme}
		aria-label={theme === 'dark' ? 'Gunakan tema terang' : 'Gunakan tema gelap'}
	>
		{#key theme}
			<span class="grid" in:fly={{ y: 8, duration: ms(240), easing: ease }}>
				{#if theme === 'dark'}<Sun size={18} />{:else}<Moon size={18} />{/if}
			</span>
		{/key}
	</button>
{/snippet}

{#snippet mark()}
	<span class="grid h-7 w-7 place-items-center rounded-lg bg-accent text-on-accent">
		<Receipt size={16} weight="bold" />
	</span>
{/snippet}

{#if !auth.loaded}
	<div class="grid min-h-[100dvh] place-items-center">
		<span class="h-1 w-24 skeleton" aria-label="Memuat"></span>
	</div>
{:else if isLogin}
	{@render children()}
{:else if auth.user}
	<div class="min-h-[100dvh] lg:flex">
		<!-- Bar atas (mobile) -->
		<header class="sticky top-0 z-30 flex items-center justify-between border-b border-line bg-surface px-4 py-2.5 lg:hidden">
			<span class="flex items-center gap-2 font-semibold tracking-tight">{@render mark()} Reimburse</span>
			<div class="flex items-center gap-1">
				{@render themeButton()}
				<button
					class="grid h-8 w-8 place-items-center rounded-lg text-muted hover:bg-subtle"
					onclick={() => (menuOpen = !menuOpen)}
					aria-label={menuOpen ? 'Tutup menu' : 'Buka menu'}
					aria-expanded={menuOpen}
				>
					{#if menuOpen}<X size={20} />{:else}<List size={20} />{/if}
				</button>
			</div>
		</header>

		<aside
			class="{menuOpen ? 'flex' : 'hidden'} z-20 w-full shrink-0 flex-col border-r border-line bg-surface lg:sticky lg:top-0 lg:flex lg:h-[100dvh] lg:w-60"
		>
			<div class="hidden items-center justify-between px-5 py-5 lg:flex">
				<div class="flex items-center gap-2.5">
					{@render mark()}
					<div>
						<div class="leading-tight font-semibold tracking-tight">Reimburse</div>
						<div class="text-xs text-faint">PT. Duta Sarana Abadi Jaya</div>
					</div>
				</div>
			</div>

			<nav class="flex-1 space-y-0.5 overflow-y-auto px-3 py-2">
				{#each nav as item (item.label)}
					{@const active = isActive(item.href)}
					<a
						href={item.href}
						onclick={() => (menuOpen = false)}
						aria-current={active ? 'page' : undefined}
						class="group relative flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors {active
							? 'font-medium text-fg'
							: 'text-muted hover:bg-subtle/60 hover:text-fg'}"
					>
						{#if active}
							<span
								class="absolute inset-0 rounded-lg border border-line bg-subtle"
								in:receive={{ key: 'nav' }}
								out:send={{ key: 'nav' }}
							></span>
						{/if}
						<item.icon
							size={18}
							weight={active ? 'fill' : 'regular'}
							class="relative transition-transform duration-200 group-hover:scale-110 {active ? 'text-accent' : ''}"
						/>
						<span class="relative">{item.label}</span>
					</a>
				{/each}
			</nav>

			<div class="border-t border-line p-3">
				<button
					class="mb-1 hidden w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-muted transition-colors hover:bg-subtle/60 hover:text-fg lg:flex"
					onclick={toggleTheme}
				>
					{#key theme}
						<span class="grid" in:fly={{ y: 8, duration: ms(240), easing: ease }}>
							{#if theme === 'dark'}<Sun size={18} />{:else}<Moon size={18} />{/if}
						</span>
					{/key}
					{theme === 'dark' ? 'Tema terang' : 'Tema gelap'}
				</button>
				<div class="flex items-center gap-3 rounded-lg px-2 py-1.5">
					<div class="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-accent-soft text-xs font-semibold text-accent">
						{auth.user.name.slice(0, 1)}
					</div>
					<div class="min-w-0 flex-1">
						<div class="truncate text-sm font-medium">{auth.user.name}</div>
						<div class="truncate text-xs text-faint">{ROLE_LABEL[auth.user.role]}</div>
					</div>
					<button
						class="grid h-8 w-8 place-items-center rounded-lg text-muted transition-colors hover:bg-subtle hover:text-fg"
						onclick={logout}
						aria-label="Keluar"
						title="Keluar"
					>
						<SignOut size={18} />
					</button>
				</div>
			</div>
		</aside>

		<main class="min-w-0 flex-1 px-4 py-6 lg:px-10 lg:py-8">
			<div class="mx-auto max-w-6xl">
				{#if allowed}
					{#key page.url.pathname}
						<div in:fly|global={{ y: 10, duration: ms(320), easing: ease }}>
							{@render children()}
						</div>
					{/key}
				{/if}
			</div>
		</main>
	</div>
{/if}
