<script lang="ts">
	import type { Snippet } from 'svelte';
	import Tray from 'phosphor-svelte/lib/TrayIcon';

	let { title, hint, children }: { title: string; hint?: string; children?: Snippet } = $props();
</script>

<div class="flex flex-col items-center px-6 py-12 text-center">
	<div class="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-subtle text-faint">
		<Tray size={22} />
	</div>
	<p class="font-medium text-fg">{title}</p>
	{#if hint}<p class="mt-1 max-w-xs text-sm text-muted">{hint}</p>{/if}
	{#if children}<div class="mt-4">{@render children()}</div>{/if}
</div>
