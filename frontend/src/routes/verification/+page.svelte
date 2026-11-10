<script lang="ts">
	import ReimbursementTable from '#lib/components/ReimbursementTable.svelte';
	import PageHeader from '#lib/components/PageHeader.svelte';
	import { CATEGORY_LABEL } from '#lib/labels.ts';
	import { auth } from '#lib/session.svelte.ts';

	const category = auth.user?.role === 'admin_transport' ? 'transport' : 'consumption';
</script>

<PageHeader
	eyebrow="Admin · {CATEGORY_LABEL[category]}"
	title="Verifikasi Pengajuan"
	description="Periksa kesesuaian struk dengan data pengajuan, lalu teruskan ke atasan, kembalikan, atau tolak."
/>

<ReimbursementTable
	showCategoryFilter={false}
	tabs={[
		{ label: 'Perlu diverifikasi', status: 'submitted,under_review' },
		{ label: 'Diteruskan ke atasan', status: 'pending_approval' },
		{ label: 'Dikembalikan', status: 'revision_required' },
		{ label: 'Ditolak', status: 'rejected' },
		{ label: 'Semua', status: '' }
	]}
/>
