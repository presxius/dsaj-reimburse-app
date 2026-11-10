<script lang="ts">
	import PageHeader from '#lib/components/PageHeader.svelte';
	import { ROLE_LABEL, initials } from '#lib/labels.ts';
	import { auth } from '#lib/session.svelte.ts';

	const u = auth.user!;
	const facts = [
		['Role', ROLE_LABEL[u.role]],
		['Departemen', u.department?.name ?? '-'],
		...(u.role === 'employee' ? [['Atasan langsung', u.approver?.name ?? 'Belum diatur']] : []),
		['Status akun', u.is_active ? 'Aktif' : 'Nonaktif']
	];
</script>

<PageHeader eyebrow="Akun" title="Profil" />

<section class="panel reveal max-w-2xl overflow-hidden" style="--d: 120ms">
	<div class="flex items-center gap-5 p-6 sm:p-7">
		<span class="avatar size-16 text-2xl" style="animation: pop-in 520ms var(--spring) 200ms both">{initials(u.name)}</span>
		<div class="min-w-0">
			<h2 class="display truncate text-[1.75rem] text-ink">{u.name}</h2>
			<p class="truncate text-muted">{u.email}</p>
		</div>
	</div>
	<dl class="grid gap-px border-t border-line bg-line sm:grid-cols-2">
		{#each facts as [k, v], i (k)}
			<div class="row-in bg-surface px-6 py-4 sm:px-7" style="--d: {260 + i * 60}ms">
				<dt class="eyebrow">{k}</dt>
				<dd class="mt-1.5 font-medium text-ink">{v}</dd>
			</div>
		{/each}
	</dl>
</section>
