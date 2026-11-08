<script lang="ts">
	import { formatDate } from '#lib/labels.ts';
	import { api } from '#lib/services/api.ts';
	import { notifyError } from '#lib/session.svelte.ts';
	import type { ActivityLog } from '#lib/types/index.ts';

	let logs = $state<ActivityLog[]>([]);

	$effect(() => {
		api
			.get<ActivityLog[]>('/activity-logs')
			.then((l) => (logs = l))
			.catch(notifyError);
	});
</script>

<h1 class="mb-6 text-2xl font-semibold tracking-tight">Log Aktivitas</h1>
<div class="card overflow-x-auto p-0">
	<table class="table-base">
		<thead>
			<tr><th>Waktu</th><th>Pengguna</th><th>Aktivitas</th><th>Detail</th></tr>
		</thead>
		<tbody>
			{#each logs as l (l.id)}
				<tr>
					<td class="num whitespace-nowrap text-muted">{formatDate(l.created_at, true)}</td>
					<td>{l.user ?? '-'}</td>
					<td><code class="rounded bg-subtle px-1.5 py-0.5 font-mono text-xs">{l.action}</code></td>
					<td class="text-muted">{l.detail ?? ''}</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>
