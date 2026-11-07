<script lang="ts">
	import { STATUS_COLOR, STATUS_LABEL } from '#lib/labels.ts';
	import type { Status } from '#lib/types/index.ts';

	let { status }: { status: Status } = $props();
</script>

<span
	class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap {STATUS_COLOR[
		status
	]}"
>
	{STATUS_LABEL[status]}
</span>
