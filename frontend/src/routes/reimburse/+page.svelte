<script lang="ts">
	import ReimbursementTable from '#lib/components/ReimbursementTable.svelte';
	import PageHeader from '#lib/components/PageHeader.svelte';
	import { hasRole } from '#lib/session.svelte.ts';

	const isEmployee = hasRole('employee');
</script>

<!-- Tombol "Ajukan" sudah ada di header (desktop) dan tab bar (mobile). -->
<PageHeader
	eyebrow={isEmployee ? 'Pengajuan saya' : 'Seluruh perusahaan'}
	title={isEmployee ? 'Riwayat Pengajuan' : 'Semua Pengajuan'}
	description={isEmployee
		? 'Semua reimburse yang pernah Anda ajukan, dari draft sampai dibayar.'
		: 'Pantau seluruh pengajuan reimburse dari semua departemen.'}
/>

<ReimbursementTable showEmployee={!isEmployee} />
