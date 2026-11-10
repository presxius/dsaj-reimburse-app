<script lang="ts">
	import ReimbursementTable from '#lib/components/ReimbursementTable.svelte';
	import PageHeader from '#lib/components/PageHeader.svelte';
</script>

<PageHeader
	eyebrow="Atasan langsung"
	title="Persetujuan Pengajuan"
	description="Pengajuan tim Anda yang sudah diverifikasi admin dan menunggu keputusan."
/>

<ReimbursementTable
	tabs={[
		{ label: 'Menunggu persetujuan', status: 'pending_approval' },
		{ label: 'Disetujui', status: 'approved,processing_payment,paid' },
		{ label: 'Ditolak / dikembalikan', status: 'rejected,revision_required' },
		{ label: 'Semua', status: '' }
	]}
/>
