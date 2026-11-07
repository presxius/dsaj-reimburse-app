<script lang="ts">
	import { toasts } from '#lib/session.svelte.ts';
</script>

<div class="fixed right-4 bottom-4 z-50 flex w-80 flex-col gap-2" aria-live="polite">
	{#each toasts as t (t.id)}
		<div
			class="rounded-lg px-4 py-3 text-sm text-white shadow-lg {t.kind === 'success'
				? 'bg-green-600'
				: 'bg-red-600'}"
		>
			{t.message}
		</div>
	{/each}
</div>
