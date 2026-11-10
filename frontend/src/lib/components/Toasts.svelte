<script lang="ts">
	import { flip } from 'svelte/animate';
	import { fly, scale } from 'svelte/transition';
	import { backOut } from 'svelte/easing';
	import X from 'phosphor-svelte/lib/XIcon';
	import { ease, ms } from '#lib/motion.ts';
	import { TOAST_MS, dismiss, toasts } from '#lib/session.svelte.ts';
</script>

<!-- Di atas tab bar pada mobile, pojok kanan bawah pada desktop. -->
<div
	class="pointer-events-none fixed inset-x-0 bottom-24 z-[60] flex flex-col items-center gap-2 px-4 lg:inset-x-auto lg:right-6 lg:bottom-6 lg:items-end"
	aria-live="polite"
>
	{#each toasts as t (t.id)}
		<div
			animate:flip={{ duration: ms(260), easing: ease }}
			in:fly={{ y: 24, duration: ms(420), easing: backOut }}
			out:scale={{ start: 0.92, duration: ms(180), easing: ease }}
			class="pointer-events-auto relative flex w-full max-w-sm items-start gap-3 overflow-hidden rounded-2xl bg-primary py-3 pr-2.5 pl-3.5 text-[13.5px] text-on-primary shadow-float"
			role={t.kind === 'error' ? 'alert' : 'status'}
		>
			<span
				class="mt-px grid size-5 shrink-0 place-items-center rounded-full {t.kind === 'success'
					? 'bg-lime text-on-lime'
					: 'bg-danger text-white'}"
				in:scale={{ start: 0.3, duration: ms(420), delay: ms(120), easing: backOut }}
				aria-hidden="true"
			>
				{#if t.kind === 'success'}
					<svg viewBox="0 0 16 16" class="size-3"><path d="m3.5 8.5 3 3 6-6.5" fill="none" stroke="currentColor"
							stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" /></svg>
				{:else}
					<svg viewBox="0 0 16 16" class="size-3"><path d="M8 3.5v5.5" stroke="currentColor" stroke-width="2.2"
							stroke-linecap="round" /><circle cx="8" cy="12.3" r="1.3" fill="currentColor" /></svg>
				{/if}
			</span>
			<span class="flex-1 leading-snug">{t.message}</span>
			<button
				class="grid size-6 shrink-0 place-items-center rounded-md opacity-60 transition-opacity hover:opacity-100"
				onclick={() => dismiss(t.id)}
				aria-label="Tutup notifikasi"><X size={14} /></button
			>
			<span
				class="absolute bottom-0 left-0 h-[2px] w-full origin-left {t.kind === 'success' ? 'bg-lime' : 'bg-danger'}"
				style="animation: toast-timer {TOAST_MS}ms linear forwards"
				aria-hidden="true"
			></span>
		</div>
	{/each}
</div>
