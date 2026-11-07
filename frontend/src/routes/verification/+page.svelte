<script lang="ts">
	import ReimbursementTable from '#lib/components/ReimbursementTable.svelte';
	import { CATEGORY_LABEL } from '#lib/labels.ts';
	import { auth } from '#lib/session.svelte.ts';

	const category = auth.user?.role === 'admin_transport' ? 'transport' : 'consumption';
</script>

<h1 class="mb-1 text-2xl font-bold text-slate-800">Verifikasi Pengajuan</h1>
<p class="mb-6 text-sm text-slate-500">Kategori {CATEGORY_LABEL[category]}</p>

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
