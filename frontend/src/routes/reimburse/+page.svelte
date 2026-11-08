<script lang="ts">
	import ReimbursementTable from '#lib/components/ReimbursementTable.svelte';
	import { hasRole } from '#lib/session.svelte.ts';
	import Plus from 'phosphor-svelte/lib/PlusIcon';

	const isEmployee = hasRole('employee');
</script>

<div class="mb-6 flex items-center justify-between">
	<h1 class="text-2xl font-semibold tracking-tight">
		{isEmployee ? 'Riwayat Pengajuan' : 'Semua Pengajuan'}
	</h1>
	{#if isEmployee}
		<a href="/reimburse/new" class="group btn btn-primary"><Plus size={16} weight="bold" class="transition-transform duration-300 group-hover:rotate-90" /> Ajukan reimburse</a>
	{/if}
</div>

<ReimbursementTable showEmployee={!isEmployee} />
