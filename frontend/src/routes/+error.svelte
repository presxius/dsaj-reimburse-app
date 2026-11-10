<script lang="ts">
	import { page } from '$app/state';
	import ArrowLeft from 'phosphor-svelte/lib/ArrowLeftIcon';

	const notFound = $derived(page.status === 404);
</script>

<div class="grid min-h-[60dvh] place-items-center py-16 text-center">
	<div>
		<p class="eyebrow reveal">Error {page.status}</p>
		<h1 class="display reveal mt-4 text-[5rem] leading-none text-ink sm:text-[7rem]" style="--d: 60ms">
			{notFound ? '404' : 'Ups.'}
		</h1>
		<p class="reveal mx-auto mt-4 max-w-sm text-[15px] text-muted" style="--d: 120ms">
			{notFound ? 'Halaman yang Anda cari tidak ada atau sudah dipindahkan.' : (page.error?.message ?? 'Terjadi kesalahan.')}
		</p>
		<a href="/dashboard" class="group btn btn-primary reveal mt-8" style="--d: 180ms">
			<ArrowLeft size={15} class="transition-transform duration-300 ease-spring group-hover:-translate-x-1" />
			Kembali ke dashboard
		</a>
	</div>
</div>
