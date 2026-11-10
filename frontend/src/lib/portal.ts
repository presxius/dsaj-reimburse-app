/**
 * Pindahkan elemen ke <body>. Dipakai untuk overlay (drawer) agar lepas dari stacking context
 * halaman: <main> memakai view-transition-name sehingga z-index di dalamnya kalah dari header.
 */
export function portal(node: HTMLElement) {
	document.body.appendChild(node);
	return { destroy: () => node.remove() };
}
