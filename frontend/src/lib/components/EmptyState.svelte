<script lang="ts">
	import type { Snippet } from 'svelte';

	let { title, hint, children }: { title: string; hint?: string; children?: Snippet } = $props();
</script>

<div class="flex flex-col items-center px-6 py-14 text-center">
	<!-- Potongan struk kosong, digambar tipis. -->
	<svg viewBox="0 0 48 56" class="mb-4 h-14 w-12 text-line-strong" fill="none" aria-hidden="true">
		<path
			d="M6 4h36v44l-4.5-3-4.5 3-4.5-3-4.5 3-4.5-3-4.5 3-4.5-3L6 48V4Z"
			stroke="currentColor"
			stroke-width="1.5"
			stroke-linejoin="round"
			fill="var(--surface)"
		/>
		<path d="M13 15h22M13 22h14M13 33h22" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"
			stroke-dasharray="2 3" />
	</svg>
	<p class="display text-lg text-ink">{title}</p>
	{#if hint}<p class="mt-1.5 max-w-xs text-sm text-muted">{hint}</p>{/if}
	{#if children}<div class="mt-5">{@render children()}</div>{/if}
</div>
