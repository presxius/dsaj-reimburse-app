<script lang="ts">
	import '../app.css';
	import favicon from '#lib/assets/favicon.svg';
	import Toasts from '#lib/components/Toasts.svelte';
	import Logo from '#lib/components/Logo.svelte';
	import { goto, onNavigate } from '$app/navigation';
	import { page } from '$app/state';
	import { ROLE_LABEL, initials } from '#lib/labels.ts';
	import { api } from '#lib/services/api.ts';
	import { auth, notify, notifyError } from '#lib/session.svelte.ts';
	import { ALL_ROLES, canAccess } from '#lib/access.ts';
	import type { Role, User } from '#lib/types/index.ts';
	import { flushSync, untrack, type Component } from 'svelte';
	import { fly, scale } from 'svelte/transition';
	import { ease, ms, reduced } from '#lib/motion.ts';
	import type { LayoutProps } from './$types';
	import SquaresFour from 'phosphor-svelte/lib/SquaresFourIcon';
	import Plus from 'phosphor-svelte/lib/PlusIcon';
	import ClockCounterClockwise from 'phosphor-svelte/lib/ClockCounterClockwiseIcon';
	import ClipboardText from 'phosphor-svelte/lib/ClipboardTextIcon';
	import SealCheck from 'phosphor-svelte/lib/SealCheckIcon';
	import Wallet from 'phosphor-svelte/lib/WalletIcon';
	import Stack from 'phosphor-svelte/lib/StackIcon';
	import ChartLineUp from 'phosphor-svelte/lib/ChartLineUpIcon';
	import UsersThree from 'phosphor-svelte/lib/UsersThreeIcon';
	import Pulse from 'phosphor-svelte/lib/PulseIcon';
	import UserIcon from 'phosphor-svelte/lib/UserIcon';
	import Sun from 'phosphor-svelte/lib/SunIcon';
	import Moon from 'phosphor-svelte/lib/MoonIcon';
	import SignOut from 'phosphor-svelte/lib/SignOutIcon';

	let { children }: LayoutProps = $props();
	let theme = $state<'light' | 'dark'>('light');
	let menuOpen = $state(false);
	let scrolled = $state(false);
	let menuEl = $state<HTMLElement>();
	let navEl = $state<HTMLElement>();

	const ALL = ALL_ROLES;
	const ADMINS: Role[] = ['admin_transport', 'admin_consumption'];
	// svelte-ignore non_reactive_update
	const NAV: { href: string; label: string; icon: Component<any>; roles: Role[] }[] = [
		{ href: '/dashboard', label: 'Dashboard', icon: SquaresFour, roles: ALL },
		{ href: '/reimburse', label: 'Riwayat', icon: ClockCounterClockwise, roles: ['employee'] },
		{ href: '/verification', label: 'Verifikasi', icon: ClipboardText, roles: ADMINS },
		{ href: '/approval', label: 'Persetujuan', icon: SealCheck, roles: ['approver'] },
		{ href: '/finance', label: 'Pembayaran', icon: Wallet, roles: ['finance'] },
		{ href: '/reimburse', label: 'Pengajuan', icon: Stack, roles: ['super_admin'] },
		{ href: '/reports', label: 'Laporan', icon: ChartLineUp, roles: [...ADMINS, 'finance', 'super_admin'] },
		{ href: '/users', label: 'Pengguna', icon: UsersThree, roles: ['super_admin'] },
		{ href: '/activity', label: 'Aktivitas', icon: Pulse, roles: ['super_admin'] }
	];

	const isLogin = $derived(page.url.pathname === '/login');
	const nav = $derived(NAV.filter((n) => auth.user && n.roles.includes(auth.user.role)));
	const isEmployee = $derived(auth.user?.role === 'employee');
	// Halaman di luar kewenangan role tidak dirender sama sekali (lihat access.ts).
	const allowed = $derived(!auth.user || canAccess(page.url.pathname, auth.user.role));

	$effect(() => {
		theme = document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';
	});

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

	// Pindah halaman: konten lama memudar, konten baru naik pelan (View Transitions API).
	onNavigate((navigation) => {
		if (!document.startViewTransition || reduced) return;
		if (navigation.from?.url.pathname === navigation.to?.url.pathname) return;
		return new Promise((resolve) => {
			document.startViewTransition(async () => {
				resolve();
				await navigation.complete;
			});
		});
	});

	// Ganti tema: tema baru "menyebar" berbentuk lingkaran dari tombol yang diklik.
	function toggleTheme(e: MouseEvent) {
		const next = theme === 'dark' ? 'light' : 'dark';
		const root = document.documentElement;
		const apply = () => {
			root.dataset.theme = next;
			flushSync(() => (theme = next));
			try {
				localStorage.setItem('theme', next);
			} catch {
				/* penyimpanan diblokir; tema tetap berlaku untuk sesi ini */
			}
		};
		if (!document.startViewTransition || reduced) return apply();
		const b = (e.currentTarget as HTMLElement).getBoundingClientRect();
		const x = b.left + b.width / 2;
		const y = b.top + b.height / 2;
		const r = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
		root.classList.add('vt-theme');
		const t = document.startViewTransition(apply);
		t.ready.then(() =>
			root.animate(
				{ clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${r}px at ${x}px ${y}px)`] },
				{ duration: 560, easing: 'cubic-bezier(0.2, 0.9, 0.1, 1)', pseudoElement: '::view-transition-new(root)' }
			)
		);
		t.finished.finally(() => root.classList.remove('vt-theme'));
	}

	function isActive(href: string) {
		const p = page.url.pathname;
		if (href === '/reimburse') return p === '/reimburse' || /^\/reimburse\/\d+/.test(p);
		return p === href || p.startsWith(href + '/');
	}

	// Menu desktop: latar hover mengikuti kursor, garis bawah meluncur ke halaman aktif.
	type Pos = { x: number; w: number };
	let hover = $state<Pos | null>(null);
	let hoverOn = $state(false);
	let activeBar = $state<Pos | null>(null);
	let navReady = $state(false);
	const posOf = (el: HTMLElement): Pos => ({ x: el.offsetLeft, w: el.offsetWidth });

	function measureActive() {
		const el = navEl?.querySelector<HTMLElement>('a[aria-current="page"]');
		activeBar = el ? posOf(el) : null;
	}

	$effect(() => {
		void page.url.pathname;
		void nav;
		measureActive();
	});

	$effect(() => {
		if (!navEl) return;
		const ro = new ResizeObserver(measureActive);
		ro.observe(navEl);
		document.fonts?.ready.then(measureActive);
		const id = requestAnimationFrame(() => (navReady = true));
		return () => {
			ro.disconnect();
			cancelAnimationFrame(id);
		};
	});

	async function logout() {
		try {
			await api.post('/auth/logout');
			menuOpen = false;
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

<svelte:window
	onscroll={() => (scrolled = scrollY > 4)}
	onkeydown={(e) => e.key === 'Escape' && (menuOpen = false)}
	onclick={(e) => {
		if (menuOpen && menuEl && !menuEl.contains(e.target as Node)) menuOpen = false;
	}}
/>

<Toasts />

{#snippet themeIcon()}
	{#key theme}
		<span class="grid" in:fly={{ y: 10, duration: ms(320), easing: ease }}>
			{#if theme === 'dark'}<Sun size={18} />{:else}<Moon size={18} />{/if}
		</span>
	{/key}
{/snippet}

{#snippet userMenu()}
	<div class="relative" bind:this={menuEl}>
		<button
			class="avatar size-9 text-[13px] ring-offset-2 ring-offset-bg transition-[box-shadow,transform] duration-200 hover:ring-2 hover:ring-line-strong active:scale-95 {menuOpen
				? 'ring-2 ring-ink'
				: ''}"
			onclick={() => (menuOpen = !menuOpen)}
			aria-label="Menu akun"
			aria-expanded={menuOpen}
			aria-haspopup="menu"
		>
			{initials(auth.user!.name)}
		</button>
		{#if menuOpen}
			<div
				class="absolute top-[calc(100%+10px)] right-0 z-50 w-72 origin-top-right rounded-2xl border border-line bg-surface p-1.5 shadow-pop"
				role="menu"
				transition:scale={{ start: 0.95, duration: ms(170), easing: ease }}
			>
				<div class="flex items-center gap-3 px-3 pt-3 pb-3.5">
					<span class="avatar size-10 text-sm">{initials(auth.user!.name)}</span>
					<div class="min-w-0">
						<div class="truncate font-semibold text-ink">{auth.user!.name}</div>
						<div class="truncate text-[13px] text-muted">{auth.user!.email}</div>
					</div>
				</div>
				<div class="mx-3 mb-1.5 flex items-center justify-between rounded-lg bg-sunken px-2.5 py-1.5 text-[12px]">
					<span class="text-muted">{ROLE_LABEL[auth.user!.role]}</span>
					<span class="truncate pl-2 text-ink-2">{auth.user!.department?.name ?? ''}</span>
				</div>
				<a href="/profile" role="menuitem" class="menu-item" onclick={() => (menuOpen = false)}>
					<UserIcon size={17} /> Profil
				</a>
				<button role="menuitem" class="menu-item" onclick={toggleTheme}>
					{@render themeIcon()}
					{theme === 'dark' ? 'Tema terang' : 'Tema gelap'}
				</button>
				<div class="my-1.5 h-px bg-line"></div>
				<button role="menuitem" class="menu-item danger" onclick={logout}>
					<SignOut size={17} /> Keluar
				</button>
			</div>
		{/if}
	</div>
{/snippet}

{#if !auth.loaded}
	<div class="grid min-h-[100dvh] place-items-center">
		<span class="animate-pulse"><Logo wordmark={false} /></span>
	</div>
{:else if isLogin}
	{@render children()}
{:else if auth.user}
	<header
		class="sticky top-0 z-40 border-b transition-[background-color,border-color,backdrop-filter] duration-300 {scrolled
			? 'border-line bg-bg/80 backdrop-blur-xl'
			: 'border-transparent bg-bg'}"
	>
		<div class="mx-auto flex h-16 max-w-6xl items-center gap-6 px-4 sm:px-6 lg:px-8">
			<a href="/dashboard" class="group shrink-0 rounded-lg" aria-label="Reimburse DSAJ, ke dashboard"><Logo /></a>

			<!-- Menu utama (desktop) -->
			<nav
				bind:this={navEl}
				class="relative hidden h-16 items-center gap-0.5 lg:flex"
				onpointerleave={() => (hoverOn = false)}
				aria-label="Menu utama"
			>
				{#if hover}
					<span
						class="pointer-events-none absolute top-1/2 h-8 -translate-y-1/2 rounded-full bg-sunken transition-[left,width,opacity] duration-300 ease-snap"
						style="left: {hover.x}px; width: {hover.w}px; opacity: {hoverOn ? 1 : 0}"
						aria-hidden="true"
					></span>
				{/if}
				{#each nav as item (item.label)}
					{@const active = isActive(item.href)}
					<a
						href={item.href}
						aria-current={active ? 'page' : undefined}
						onpointerenter={(e) => {
							hover = posOf(e.currentTarget);
							hoverOn = true;
						}}
						class="relative rounded-full px-3.5 py-1.5 text-[14px] font-medium transition-colors duration-200 {active
							? 'text-ink'
							: 'text-muted hover:text-ink'}">{item.label}</a
					>
				{/each}
				{#if activeBar}
					<span
						class="pointer-events-none absolute bottom-[-1px] left-0 h-[2px] rounded-full bg-ink {navReady
							? 'transition-[transform,width] duration-500 ease-spring'
							: ''}"
						style="width: {activeBar.w - 20}px; transform: translateX({activeBar.x + 10}px)"
						aria-hidden="true"
					></span>
				{/if}
			</nav>

			<div class="ml-auto flex items-center gap-2">
				{#if isEmployee}
					<a href="/reimburse/new" class="group btn btn-primary hidden lg:inline-flex">
						<Plus size={16} weight="bold" class="transition-transform duration-300 ease-spring group-hover:rotate-90" />
						Ajukan reimburse
					</a>
				{/if}
				<button
					class="icon-btn"
					onclick={toggleTheme}
					aria-label={theme === 'dark' ? 'Gunakan tema terang' : 'Gunakan tema gelap'}
					title={theme === 'dark' ? 'Tema terang' : 'Tema gelap'}
				>
					{@render themeIcon()}
				</button>
				{@render userMenu()}
			</div>
		</div>
	</header>

	<main class="vt-page mx-auto w-full max-w-6xl px-4 pt-6 pb-32 sm:px-6 lg:px-8 lg:pt-10 lg:pb-20">
		{#if allowed}
			{@render children()}
		{/if}
	</main>

	<!-- Tab bar (mobile) -->
	<nav
		class="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-surface/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-xl lg:hidden"
		aria-label="Menu utama"
	>
		<div class="mx-auto flex max-w-md items-stretch justify-around px-2">
			{#each nav as item, i (item.label)}
				{@const active = isActive(item.href)}
				{#if isEmployee && i === 1}
					<a href="/reimburse/new" class="group -mt-5 flex flex-1 flex-col items-center gap-1 pb-2 text-[11px] font-medium text-ink"
						aria-label="Ajukan reimburse">
						<span
							class="grid size-13 place-items-center rounded-2xl bg-chip text-on-chip shadow-pop transition-transform duration-300 ease-spring group-active:scale-90 group-hover:-translate-y-0.5"
						>
							<Plus size={24} weight="bold" class="transition-transform duration-300 ease-spring group-hover:rotate-90" />
						</span>
						Ajukan
					</a>
				{/if}
				<a
					href={item.href}
					aria-current={active ? 'page' : undefined}
					class="group flex flex-1 flex-col items-center gap-1 pt-2 pb-2.5 text-[11px]"
				>
					<span
						class="grid h-7 w-12 place-items-center rounded-full transition-[background-color,color,transform] duration-300 ease-spring group-active:scale-90 {active
							? 'bg-lime text-on-lime'
							: 'text-muted'}"
					>
						<item.icon size={20} weight={active ? 'fill' : 'regular'} />
					</span>
					<span class={active ? 'font-semibold text-ink' : 'text-muted'}>{item.label}</span>
				</a>
			{/each}
		</div>
	</nav>
{/if}

<style>
	.menu-item {
		display: flex;
		width: 100%;
		align-items: center;
		gap: 0.65rem;
		padding: 0.55rem 0.75rem;
		border-radius: 10px;
		font-size: 14px;
		color: var(--ink-2);
		cursor: pointer;
		transition:
			background-color 140ms var(--ease),
			color 140ms var(--ease);
	}
	.menu-item:hover {
		background: var(--sunken);
		color: var(--ink);
	}
	.menu-item.danger:hover {
		color: var(--danger);
	}
</style>
