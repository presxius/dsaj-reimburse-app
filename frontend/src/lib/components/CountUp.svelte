<script lang="ts">
	import { Tween } from 'svelte/motion';
	import { ease, ms } from '#lib/motion.ts';

	let { value, format = (n: number) => String(n) }: { value: number; format?: (n: number) => string } =
		$props();

	const tween = new Tween(0, { duration: ms(700), easing: ease });

	$effect(() => {
		tween.target = value;
	});
</script>

{format(Math.round(tween.current))}
