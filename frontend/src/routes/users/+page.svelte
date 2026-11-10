<script lang="ts">
	import { tick } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import Plus from 'phosphor-svelte/lib/PlusIcon';
	import X from 'phosphor-svelte/lib/XIcon';
	import MagnifyingGlass from 'phosphor-svelte/lib/MagnifyingGlassIcon';
	import PencilSimple from 'phosphor-svelte/lib/PencilSimpleIcon';
	import PageHeader from '#lib/components/PageHeader.svelte';
	import Spinner from '#lib/components/Spinner.svelte';
	import { ROLE_LABEL, initials } from '#lib/labels.ts';
	import { ease, ms } from '#lib/motion.ts';
	import { portal } from '#lib/portal.ts';
	import { api } from '#lib/services/api.ts';
	import { notify, notifyError } from '#lib/session.svelte.ts';
	import type { Department, Role, User } from '#lib/types/index.ts';

	type Form = {
		id: number | null;
		name: string;
		email: string;
		password: string;
		role: Role;
		department_id: number | null;
		approver_id: number | null;
		is_active: boolean;
	};

	const empty = (): Form => ({
		id: null, name: '', email: '', password: '', role: 'employee',
		department_id: null, approver_id: null, is_active: true
	});

	let users = $state<User[]>([]);
	let departments = $state<Department[]>([]);
	let loaded = $state(false);
	let form = $state<Form | null>(null);
	let saving = $state(false);
	let newDept = $state('');
	let search = $state('');
	let firstField = $state<HTMLInputElement>();

	const approvers = $derived(users.filter((u) => u.role === 'approver' && u.is_active));
	const shown = $derived(
		users.filter((u) => (u.name + u.email).toLowerCase().includes(search.toLowerCase()))
	);

	async function load() {
		try {
			[users, departments] = await Promise.all([
				api.get<User[]>('/users'),
				api.get<Department[]>('/departments')
			]);
		} catch (e) {
			notifyError(e);
		} finally {
			loaded = true;
		}
	}

	$effect(() => {
		load();
	});

	async function open(f: Form) {
		form = f;
		await tick();
		firstField?.focus();
	}

	function edit(u: User) {
		open({
			id: u.id, name: u.name, email: u.email, password: '', role: u.role,
			department_id: u.department?.id ?? null, approver_id: u.approver?.id ?? null,
			is_active: u.is_active
		});
	}

	async function save(e: SubmitEvent) {
		e.preventDefault();
		if (!form) return;
		const { id, ...body } = form;
		saving = true;
		try {
			if (id) await api.patch(`/users/${id}`, body);
			else await api.post('/users', body);
			notify('Data pengguna tersimpan.');
			form = null;
			load();
		} catch (err) {
			notifyError(err);
		} finally {
			saving = false;
		}
	}

	async function toggleActive(u: User) {
		// Langsung berubah di layar; dikembalikan bila server menolak.
		u.is_active = !u.is_active;
		try {
			await api.patch(`/users/${u.id}`, { is_active: u.is_active });
			notify(u.is_active ? 'Akun diaktifkan.' : 'Akun dinonaktifkan.');
		} catch (err) {
			u.is_active = !u.is_active;
			notifyError(err);
		}
	}

	async function addDept(e: SubmitEvent) {
		e.preventDefault();
		try {
			await api.post('/departments', { name: newDept });
			newDept = '';
			notify('Departemen ditambahkan.');
			load();
		} catch (err) {
			notifyError(err);
		}
	}
</script>

<svelte:window onkeydown={(e) => e.key === 'Escape' && form && (form = null)} />

<PageHeader eyebrow="Super Admin" title="Pengguna & Departemen" description="Kelola akun, role, departemen, dan atasan langsung karyawan.">
	{#snippet actions()}
		<button class="group btn btn-primary" onclick={() => open(empty())}>
			<Plus size={16} weight="bold" class="transition-transform duration-300 ease-spring group-hover:rotate-90" />
			Tambah pengguna
		</button>
	{/snippet}
</PageHeader>

<div class="grid gap-5 lg:grid-cols-[minmax(0,1fr)_18rem] lg:items-start">
	<section class="panel reveal overflow-hidden" style="--d: 140ms">
		<div class="flex items-center gap-3 border-b border-line p-3">
			<div class="relative w-full sm:w-72">
				<MagnifyingGlass size={16} class="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-faint" />
				<input class="input h-9 min-h-9 pl-9" placeholder="Cari nama atau email…" aria-label="Cari pengguna" bind:value={search} />
			</div>
			<span class="num ml-auto hidden text-[12px] text-muted sm:block">{shown.length} pengguna</span>
		</div>
		<div class="overflow-x-auto">
			<table class="table text-[13.5px]">
				<thead>
					<tr><th>Pengguna</th><th>Role</th><th>Departemen</th><th>Atasan</th><th>Aktif</th><th class="w-12"><span class="sr-only">Ubah</span></th></tr>
				</thead>
				<tbody>
					{#if !loaded}
						{#each { length: 5 }, i (i)}
							<tr><td colspan="6"><div class="flex items-center gap-3"><div class="skeleton size-9 rounded-full"></div><div class="skeleton h-3 w-48"></div></div></td></tr>
						{/each}
					{:else}
						{#each shown as u, i (u.id)}
							<tr class="row-in group hover:bg-sunken/50" style="--d: {Math.min(i, 15) * 20}ms">
								<td>
									<div class="flex items-center gap-3 transition-opacity duration-300 {u.is_active ? '' : 'opacity-45'}">
										<span class="avatar size-9 text-[12px] {u.is_active ? '' : 'grayscale'}">{initials(u.name)}</span>
										<div class="min-w-0">
											<div class="font-medium text-ink">{u.name}</div>
											<div class="truncate text-[12px] text-muted">{u.email}</div>
										</div>
									</div>
								</td>
								<td class="whitespace-nowrap text-ink-2">{ROLE_LABEL[u.role]}</td>
								<td class="text-ink-2">{u.department?.name ?? '-'}</td>
								<td class="text-ink-2">{u.approver?.name ?? '-'}</td>
								<td>
									<button class="switch" role="switch" aria-checked={u.is_active} onclick={() => toggleActive(u)}
										aria-label="{u.is_active ? 'Nonaktifkan' : 'Aktifkan'} {u.name}"></button>
								</td>
								<td class="text-right">
									<button class="icon-btn size-8 opacity-60 group-hover:opacity-100" onclick={() => edit(u)} aria-label="Ubah {u.name}" title="Ubah">
										<PencilSimple size={16} />
									</button>
								</td>
							</tr>
						{:else}
							<tr><td colspan="6" class="py-10 text-center text-muted">Tidak ada pengguna yang cocok.</td></tr>
						{/each}
					{/if}
				</tbody>
			</table>
		</div>
	</section>

	<aside class="panel reveal p-5" style="--d: 200ms">
		<h2 class="display text-xl text-ink">Departemen</h2>
		<ul class="mt-3 divide-y divide-line text-[13.5px]">
			{#each departments as d (d.id)}
				<li class="row-in flex items-center justify-between py-2.5">
					<span class="text-ink">{d.name}</span>
					<span class="num text-[12px] text-muted">{users.filter((u) => u.department?.id === d.id).length}</span>
				</li>
			{/each}
		</ul>
		<form class="mt-4 flex gap-2" onsubmit={addDept}>
			<input class="input h-9 min-h-9" placeholder="Departemen baru" aria-label="Nama departemen baru" bind:value={newDept} required />
			<button class="btn btn-primary size-9 shrink-0 px-0" aria-label="Tambah departemen"><Plus size={16} weight="bold" /></button>
		</form>
	</aside>
</div>

{#if form}
	<div use:portal class="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-labelledby="drawer-title">
		<button class="absolute inset-0 h-full w-full cursor-default bg-black/35 backdrop-blur-[2px]" aria-label="Tutup"
			onclick={() => (form = null)} transition:fade={{ duration: ms(200) }}></button>
		<form
			class="absolute inset-y-0 right-0 flex w-full max-w-md flex-col border-l border-line bg-surface shadow-float"
			onsubmit={save}
			transition:fly={{ x: 48, duration: ms(340), easing: ease }}
		>
			<div class="flex items-start justify-between gap-4 border-b border-line p-5">
				<div>
					<p class="eyebrow">{form.id ? 'Ubah akun' : 'Akun baru'}</p>
					<h2 id="drawer-title" class="display mt-2 text-2xl text-ink">{form.id ? form.name || 'Pengguna' : 'Pengguna baru'}</h2>
				</div>
				<button type="button" class="icon-btn" onclick={() => (form = null)} aria-label="Tutup"><X size={18} /></button>
			</div>
			<div class="flex-1 space-y-4 overflow-y-auto p-5">
				<div><label class="label" for="n">Nama</label><input id="n" class="input" bind:value={form.name} bind:this={firstField} required /></div>
				<div><label class="label" for="e">Email</label><input id="e" type="email" class="input" bind:value={form.email} required /></div>
				<div>
					<label class="label" for="p">Password {#if form.id}<span class="font-normal text-muted">· kosongkan jika tidak diubah</span>{/if}</label>
					<input id="p" type="password" class="input" minlength="8" bind:value={form.password} required={!form.id} autocomplete="new-password" />
					<p class="hint">Minimal 8 karakter.</p>
				</div>
				<div>
					<label class="label" for="r">Role</label>
					<select id="r" class="input" bind:value={form.role}>
						{#each Object.entries(ROLE_LABEL) as [value, text] (value)}
							<option {value}>{text}</option>
						{/each}
					</select>
				</div>
				<div>
					<label class="label" for="d">Departemen</label>
					<select id="d" class="input" bind:value={form.department_id}>
						<option value={null}>Tidak ada</option>
						{#each departments as d (d.id)}<option value={d.id}>{d.name}</option>{/each}
					</select>
				</div>
				{#if form.role === 'employee'}
					<div transition:fly={{ y: -6, duration: ms(220), easing: ease }}>
						<label class="label" for="a">Atasan langsung</label>
						<select id="a" class="input" bind:value={form.approver_id}>
							<option value={null}>Tidak ada</option>
							{#each approvers as a (a.id)}<option value={a.id}>{a.name}</option>{/each}
						</select>
					</div>
				{/if}
			</div>
			<div class="flex justify-end gap-2 border-t border-line p-5">
				<button type="button" class="btn btn-secondary" onclick={() => (form = null)}>Batal</button>
				<button class="btn btn-primary" disabled={saving}>{#if saving}<Spinner size={14} />{/if} Simpan</button>
			</div>
		</form>
	</div>
{/if}
