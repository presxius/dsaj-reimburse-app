<script lang="ts">
	import ReimbursementTable from '#lib/components/ReimbursementTable.svelte';
</script>

<h1 class="mb-6 text-2xl font-bold text-slate-800">Persetujuan Pengajuan</h1>

<ReimbursementTable
	tabs={[
		{ label: 'Menunggu persetujuan', status: 'pending_approval' },
		{ label: 'Disetujui', status: 'approved,processing_payment,paid' },
		{ label: 'Ditolak / dikembalikan', status: 'rejected,revision_required' },
		{ label: 'Semua', status: '' }
	]}
/>
