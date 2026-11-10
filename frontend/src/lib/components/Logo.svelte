<script lang="ts">
	let { wordmark = true, inverse = false }: { wordmark?: boolean; inverse?: boolean } = $props();
</script>

<!-- Tanda: panah "kembali" — uang yang dikeluarkan karyawan kembali ke tangannya. -->
<span class="inline-flex items-center gap-2.5">
	<svg viewBox="0 0 24 24" class="size-7 shrink-0 transition-transform duration-500 ease-spring group-hover:-rotate-12"
		aria-hidden="true">
		<rect width="24" height="24" rx="7" fill={inverse ? 'var(--lime)' : 'var(--chip)'} />
		<g fill="none" stroke={inverse ? '#161613' : 'var(--on-chip)'} stroke-width="2.2" stroke-linecap="round"
			stroke-linejoin="round">
			<path d="M7.5 10h6.75a3.75 3.75 0 0 1 0 7.5H11" />
			<path d="M10.25 7.25 7.5 10l2.75 2.75" />
		</g>
	</svg>
	{#if wordmark}
		<span class="flex items-baseline gap-1.5">
			<span class="display text-[19px] leading-none {inverse ? 'text-[#f0efe9]' : 'text-ink'}">Reimburse</span>
			<span class="code text-[10px] font-medium tracking-wider {inverse ? 'text-[#a19f95]' : 'text-muted'}">DSAJ</span>
		</span>
	{/if}
</span>
