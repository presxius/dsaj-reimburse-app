<script lang="ts">
	import { goto } from '$app/navigation';
	import ReimbursementForm from '#lib/components/ReimbursementForm.svelte';
	import PageHeader from '#lib/components/PageHeader.svelte';
</script>

<PageHeader
	eyebrow="Pengajuan baru"
	title="Ajukan Reimburse"
	description="Satu pengajuan bisa berisi banyak struk dari kategori yang sama. Tiap struk jadi satu item; OCR mencoba mengisinya, periksa lagi sebelum mengirim."
/>
<ReimbursementForm onsaved={(r) => goto(`/reimburse/${r.id}`)} />
