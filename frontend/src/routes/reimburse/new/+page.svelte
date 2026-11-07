<script lang="ts">
	import { goto } from '$app/navigation';
	import ReimbursementForm from '#lib/components/ReimbursementForm.svelte';
</script>

<h1 class="mb-6 text-2xl font-semibold tracking-tight">Ajukan Reimburse</h1>
<ReimbursementForm onsaved={(r) => goto(`/reimburse/${r.id}`)} />
