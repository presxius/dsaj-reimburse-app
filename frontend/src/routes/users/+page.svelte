<script lang="ts">
	import { slide } from 'svelte/transition';
	import Plus from 'phosphor-svelte/lib/PlusIcon';
	import { ROLE_LABEL } from '#lib/labels.ts';
	import { ease, ms } from '#lib/motion.ts';
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
	let form = $state<Form | null>(null);
	let newDept = $state('');
	let search = $state('');

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
		}
	}

	$effect(() => {
		load();
	});

	function edit(u: User) {
		form = {
			id: u.id, name: u.name, email: u.email, password: '', role: u.role,
			department_id: u.department?.id ?? null, approver_id: u.approver?.id ?? null,
			is_active: u.is_active
		};
	}

	async function save(e: SubmitEvent) {
		e.preventDefault();
		if (!form) return;
		const { id, ...body } = form;
		try {
			if (id) await api.patch(`/users/${id}`, body);
			else await api.post('/users', body);
			notify('Data pengguna tersimpan.');
			form = null;
			load();
		} catch (err) {
			notifyError(err);
		}
	}

	async function toggleActive(u: User) {
		try {
			await api.patch(`/users/${u.id}`, { is_active: !u.is_active });
			notify(u.is_active ? 'Akun dinonaktifkan.' : 'Akun diaktifkan.');
			load();
		} catch (err) {
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

<div class="mb-6 flex items-center justify-between">
	<h1 class="text-2xl font-semibold tracking-tight">Pengguna & Departemen</h1>
	<button class="group btn btn-primary" onclick={() => (form = empty())}><Plus size={16} weight="bold" class="transition-transform duration-300 group-hover:rotate-90" /> Tambah pengguna</button>
</div>

{#if form}
	<form class="card mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3" onsubmit={save} transition:slide={{ duration: ms(260), easing: ease }}>
		<h2 class="font-semibold text-fg sm:col-span-2 lg:col-span-3">
			{form.id ? 'Ubah pengguna' : 'Pengguna baru'}
		</h2>
		<div><label class="label" for="n">Nama</label><input id="n" class="input" bind:value={form.name} required /></div>
		<div><label class="label" for="e">Email</label><input id="e" type="email" class="input" bind:value={form.email} required /></div>
		<div>
			<label class="label" for="p">Password {form.id ? '(kosongkan jika tidak diubah)' : ''}</label>
			<input id="p" type="password" class="input" minlength="8" bind:value={form.password} required={!form.id} />
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
			<div>
				<label class="label" for="a">Atasan langsung</label>
				<select id="a" class="input" bind:value={form.approver_id}>
					<option value={null}>Tidak ada</option>
					{#each approvers as a (a.id)}<option value={a.id}>{a.name}</option>{/each}
				</select>
			</div>
		{/if}
		<div class="flex justify-end gap-2 sm:col-span-2 lg:col-span-3">
			<button type="button" class="btn btn-secondary" onclick={() => (form = null)}>Batal</button>
			<button class="btn btn-primary">Simpan</button>
		</div>
	</form>
{/if}

<div class="grid gap-6 lg:grid-cols-4">
	<div class="card overflow-x-auto p-0 lg:col-span-3">
		<div class="p-3"><input class="input max-w-xs" placeholder="Cari nama / email..." bind:value={search} /></div>
		<table class="table-base">
			<thead>
				<tr><th>Nama</th><th>Role</th><th>Departemen</th><th>Atasan</th><th>Status</th><th></th></tr>
			</thead>
			<tbody>
				{#each shown as u (u.id)}
					<tr class={u.is_active ? '' : 'opacity-50'}>
						<td><div class="font-medium">{u.name}</div><div class="text-xs text-muted">{u.email}</div></td>
						<td>{ROLE_LABEL[u.role]}</td>
						<td>{u.department?.name ?? '-'}</td>
						<td>{u.approver?.name ?? '-'}</td>
						<td>{u.is_active ? 'Aktif' : 'Nonaktif'}</td>
						<td class="num text-right whitespace-nowrap">
							<button class="text-accent hover:underline" onclick={() => edit(u)}>Ubah</button>
							<button class="ml-3 text-muted hover:underline" onclick={() => toggleActive(u)}>
								{u.is_active ? 'Nonaktifkan' : 'Aktifkan'}
							</button>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>

	<div class="card">
		<h2 class="mb-3 font-semibold text-fg">Departemen</h2>
		<ul class="mb-4 space-y-1 text-sm">
			{#each departments as d (d.id)}<li class="border-b border-line py-1">{d.name}</li>{/each}
		</ul>
		<form class="flex gap-2" onsubmit={addDept}>
			<input class="input" placeholder="Nama departemen" bind:value={newDept} required />
			<button class="btn btn-primary px-2.5" aria-label="Tambah departemen"><Plus size={16} weight="bold" /></button>
		</form>
	</div>
</div>
