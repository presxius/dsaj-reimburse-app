<script lang="ts">
	import { flip } from 'svelte/animate';
	import { fly } from 'svelte/transition';
	import CheckCircle from 'phosphor-svelte/lib/CheckCircleIcon';
	import WarningCircle from 'phosphor-svelte/lib/WarningCircleIcon';
	import X from 'phosphor-svelte/lib/XIcon';
	import { ease, ms } from '#lib/motion.ts';
	import { TOAST_MS, dismiss, toasts } from '#lib/session.svelte.ts';
</script>

<div class="fixed right-4 bottom-4 z-50 flex w-[calc(100vw-2rem)] max-w-sm flex-col gap-2" aria-live="polite">
	{#each toasts as t (t.id)}
		<div
			animate:flip={{ duration: ms(220), easing: ease }}
			in:fly={{ x: 32, duration: ms(320), easing: ease }}
			out:fly={{ x: 32, duration: ms(180), easing: ease }}
			class="relative flex items-start gap-2.5 overflow-hidden rounded-xl border border-line bg-surface py-3 pr-2.5 pl-4 text-sm text-fg shadow-[0_12px_32px_-12px_var(--shadow)]"
		>
			{#if t.kind === 'success'}
				<CheckCircle size={18} weight="fill" class="mt-0.5 shrink-0 text-accent" />
			{:else}
				<WarningCircle size={18} weight="fill" class="mt-0.5 shrink-0 text-danger" />
			{/if}
			<span class="flex-1">{t.message}</span>
			<button
				class="grid h-6 w-6 shrink-0 place-items-center rounded-md text-faint transition-colors hover:bg-subtle hover:text-fg"
				onclick={() => dismiss(t.id)}
				aria-label="Tutup notifikasi"><X size={14} /></button
			>
			<span
				class="absolute bottom-0 left-0 h-0.5 w-full origin-left {t.kind === 'success'
					? 'bg-accent'
					: 'bg-danger'}"
				style="animation: toast-timer {TOAST_MS}ms linear forwards"
				aria-hidden="true"
			></span>
		</div>
	{/each}
</div>
