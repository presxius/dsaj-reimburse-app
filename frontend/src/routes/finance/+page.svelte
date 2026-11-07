<script lang="ts">
	import ReimbursementTable from '#lib/components/ReimbursementTable.svelte';
</script>

<h1 class="mb-6 text-2xl font-semibold tracking-tight">Pembayaran Reimburse</h1>

<ReimbursementTable
	tabs={[
		{ label: 'Siap dibayar', status: 'approved' },
		{ label: 'Sedang diproses', status: 'processing_payment' },
		{ label: 'Riwayat pembayaran', status: 'paid' }
	]}
/>
