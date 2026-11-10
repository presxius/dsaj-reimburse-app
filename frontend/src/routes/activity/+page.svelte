<script lang="ts">
	import PageHeader from '#lib/components/PageHeader.svelte';
	import EmptyState from '#lib/components/EmptyState.svelte';
	import { api } from '#lib/services/api.ts';
	import { notifyError } from '#lib/session.svelte.ts';
	import type { ActivityLog } from '#lib/types/index.ts';

	let logs = $state<ActivityLog[] | null>(null);

	$effect(() => {
		api
			.get<ActivityLog[]>('/activity-logs')
			.then((l) => (logs = l))
			.catch(notifyError);
	});

	// Waktu dari server dalam UTC tanpa zona; kelompokkan per hari menurut waktu lokal.
	const local = (iso: string) => new Date(iso + 'Z');
	const groups = $derived.by(() => {
		const map = new Map<string, ActivityLog[]>();
		for (const l of logs ?? []) {
			const day = local(l.created_at).toLocaleDateString('id-ID', {
				weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
			});
			map.set(day, [...(map.get(day) ?? []), l]);
		}
		return [...map];
	});
	const time = (iso: string) => local(iso).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });
</script>

<PageHeader eyebrow="Audit" title="Log Aktivitas" description="Jejak setiap tindakan pengguna di sistem, terbaru di atas." />

{#if !logs}
	<div class="panel space-y-3 p-5">{#each { length: 6 }, i (i)}<div class="skeleton h-4 w-full"></div>{/each}</div>
{:else if logs.length === 0}
	<div class="panel"><EmptyState title="Belum ada aktivitas" /></div>
{:else}
	<div class="space-y-6">
		{#each groups as [day, items], g (day)}
			<section class="reveal" style="--d: {120 + g * 60}ms">
				<h2 class="eyebrow mb-2.5 px-1">{day}</h2>
				<ol class="panel divide-y divide-line overflow-hidden">
					{#each items as l (l.id)}
						<li class="grid grid-cols-[3.5rem_1fr] gap-x-4 gap-y-1 px-5 py-3 text-[13.5px] transition-colors hover:bg-sunken/50 sm:grid-cols-[3.5rem_11rem_13rem_1fr] sm:items-center">
							<span class="code text-[12px] text-muted">{time(l.created_at)}</span>
							<span class="truncate font-medium text-ink">{l.user ?? 'Sistem'}</span>
							<span class="col-start-2 sm:col-start-auto"><code class="code rounded-md bg-sunken px-1.5 py-0.5 text-[11.5px] text-ink-2">{l.action}</code></span>
							<span class="col-start-2 truncate text-muted sm:col-start-auto" title={l.detail ?? ''}>{l.detail ?? ''}</span>
						</li>
					{/each}
				</ol>
			</section>
		{/each}
	</div>
{/if}
