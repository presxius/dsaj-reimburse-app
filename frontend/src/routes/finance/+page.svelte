<script lang="ts">
	import ReimbursementTable from '#lib/components/ReimbursementTable.svelte';
	import PageHeader from '#lib/components/PageHeader.svelte';
</script>

<PageHeader
	eyebrow="Finance"
	title="Pembayaran Reimburse"
	description="Pengajuan yang sudah disetujui atasan, siap diproses dan dicatat pembayarannya."
/>

<ReimbursementTable
	tabs={[
		{ label: 'Siap dibayar', status: 'approved' },
		{ label: 'Sedang diproses', status: 'processing_payment' },
		{ label: 'Riwayat pembayaran', status: 'paid' }
	]}
/>
