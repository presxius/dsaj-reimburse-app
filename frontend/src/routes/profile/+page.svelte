<script lang="ts">
	import { ROLE_LABEL } from '#lib/labels.ts';
	import { auth } from '#lib/session.svelte.ts';

	const u = auth.user!;
</script>

<h1 class="mb-6 text-2xl font-semibold tracking-tight">Profil</h1>
<div class="card max-w-lg">
	<dl class="space-y-3 text-sm">
		<div><dt class="text-muted">Nama</dt><dd class="font-medium">{u.name}</dd></div>
		<div><dt class="text-muted">Email</dt><dd>{u.email}</dd></div>
		<div><dt class="text-muted">Role</dt><dd>{ROLE_LABEL[u.role]}</dd></div>
		<div><dt class="text-muted">Departemen</dt><dd>{u.department?.name ?? '-'}</dd></div>
		{#if u.role === 'employee'}
			<div><dt class="text-muted">Atasan langsung</dt><dd>{u.approver?.name ?? 'Belum diatur'}</dd></div>
		{/if}
	</dl>
</div>
