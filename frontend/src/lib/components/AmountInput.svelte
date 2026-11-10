<script lang="ts">
	import { untrack } from 'svelte';

	let {
		value = $bindable(),
		id,
		required = false,
		class: cls = ''
	}: { value: number | null; id?: string; required?: boolean; class?: string } = $props();

	const fmt = new Intl.NumberFormat('id-ID', { maximumFractionDigits: 0 });
	const show = (n: number | null) => (n == null ? '' : fmt.format(n));
	const parse = (s: string) => {
		const digits = s.replace(/\D/g, '');
		return digits ? Number(digits) : null;
	};

	let text = $state(untrack(() => show(value)));

	// Nilai dari luar (mis. diisi OCR) ikut ditampilkan dengan pemisah ribuan.
	$effect(() => {
		const v = value;
		untrack(() => {
			if (parse(text) !== (v == null ? null : Math.round(v))) text = show(v);
		});
	});

	function oninput(e: Event & { currentTarget: HTMLInputElement }) {
		const el = e.currentTarget;
		// Pertahankan posisi kursor: hitung digit di kiri kursor, lalu cari posisi yang sama setelah diformat.
		const digitsLeft = el.value.slice(0, el.selectionStart ?? el.value.length).replace(/\D/g, '').length;
		value = parse(el.value);
		text = show(value);
		el.value = text;
		let pos = 0;
		for (let seen = 0; pos < text.length && seen < digitsLeft; pos++) if (/\d/.test(text[pos])) seen++;
		el.setSelectionRange(pos, pos);
	}
</script>

<div class="relative">
	<span class="pointer-events-none absolute inset-y-0 left-3 grid place-items-center text-sm font-medium text-muted"
		>Rp</span
	>
	<input
		{id}
		class="input num pl-10 {cls}"
		inputmode="numeric"
		autocomplete="off"
		placeholder="0"
		{required}
		value={text}
		{oninput}
	/>
</div>
