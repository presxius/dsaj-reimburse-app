<script lang="ts">
	import { goto } from '$app/navigation';
	import ReimbursementForm from '#lib/components/ReimbursementForm.svelte';
	import PageHeader from '#lib/components/PageHeader.svelte';
</script>

<PageHeader
	eyebrow="Pengajuan baru"
	title="Ajukan Reimburse"
	description="Unggah struk transportasi atau konsumsi. OCR akan mencoba mengisi formulir; periksa lagi sebelum mengirim."
/>
<ReimbursementForm onsaved={(r) => goto(`/reimburse/${r.id}`)} />
