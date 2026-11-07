<script lang="ts">
	import CheckCircle from 'phosphor-svelte/lib/CheckCircle';
	import WarningCircle from 'phosphor-svelte/lib/WarningCircle';
	import { toasts } from '#lib/session.svelte.ts';
</script>

<div class="fixed right-4 bottom-4 z-50 flex w-[calc(100vw-2rem)] max-w-sm flex-col gap-2" aria-live="polite">
	{#each toasts as t (t.id)}
		<div
			class="flex items-start gap-2.5 rounded-xl border border-line bg-surface px-4 py-3 text-sm text-fg shadow-[0_8px_24px_-12px_rgb(15_24_40/0.25)]"
		>
			{#if t.kind === 'success'}
				<CheckCircle size={18} class="mt-0.5 shrink-0 text-accent" />
			{:else}
				<WarningCircle size={18} class="mt-0.5 shrink-0 text-danger" />
			{/if}
			<span>{t.message}</span>
		</div>
	{/each}
</div>
