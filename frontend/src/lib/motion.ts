import { cubicOut } from 'svelte/easing';
import { crossfade, fade } from 'svelte/transition';

// Transisi Svelte berjalan lewat Web Animations API, jadi aturan CSS reduced-motion tidak menjangkaunya.
export const reduced =
	typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

export const ms = (n: number) => (reduced ? 0 : n);

export const ease = cubicOut;

/** Indikator yang "meluncur" antar item aktif (nav, tab). Pakai key yang sama per grup. */
export function slider() {
	return crossfade({
		duration: ms(260),
		easing: cubicOut,
		fallback: (node) => fade(node, { duration: ms(120) })
	});
}
