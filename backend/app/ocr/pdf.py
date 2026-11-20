"""Baca struk PDF dengan pypdfium2. Hanya halaman pertama yang dipakai.

PDF digital (e-receipt, invoice) punya lapisan teks, jadi teksnya dibaca langsung tanpa OCR.
PDF hasil scan hanya berisi gambar; halaman pertama dirender lalu diproses OCR seperti foto.
"""
import os
import threading

import pypdfium2 as pdfium

# PDFium tidak thread-safe, sedangkan gunicorn menjalankan beberapa thread per worker.
_lock = threading.Lock()

MIN_TEXT_CHARS = 20      # lebih sedikit dari ini dianggap PDF scan (tanpa lapisan teks)
TARGET_WIDTH = 1600      # lebar render (px) untuk OCR
MAX_PIXELS = 25_000_000  # batas ukuran render agar halaman yang sangat besar tidak menghabiskan RAM


def is_readable(content):
    """True bila PDF bisa dibuka (tidak rusak, tidak berpassword) dan punya minimal satu halaman."""
    with _lock:
        try:
            pdf = pdfium.PdfDocument(content)
        except pdfium.PdfiumError:
            return False
        try:
            return len(pdf) > 0
        finally:
            pdf.close()


def text_lines(path):
    """Baris teks dari lapisan teks halaman pertama, atau [] bila PDF tidak punya teks."""
    with _lock:
        pdf = pdfium.PdfDocument(path)
        try:
            text = pdf[0].get_textpage().get_text_range()
        finally:
            pdf.close()
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return lines if sum(map(len, lines)) >= MIN_TEXT_CHARS else []


def render_first_page(path):
    """Render halaman pertama menjadi array BGR (format OpenCV)."""
    with _lock:
        pdf = pdfium.PdfDocument(path)
        try:
            page = pdf[0]
            w, h = page.get_size()  # dalam point (1/72 inci)
            scale = min(TARGET_WIDTH / w, (MAX_PIXELS / (w * h)) ** 0.5)
            return page.render(scale=scale).to_numpy()
        finally:
            pdf.close()


PREVIEW_WIDTH = 800  # lebar thumbnail pratinjau (px)


def save_preview(path, out_path):
    """Simpan halaman pertama sebagai PNG untuk pratinjau di browser (butuh Pillow, bukan numpy)."""
    with _lock:
        pdf = pdfium.PdfDocument(path)
        try:
            page = pdf[0]
            w, h = page.get_size()
            scale = min(PREVIEW_WIDTH / w, (MAX_PIXELS / (w * h)) ** 0.5)
            image = page.render(scale=scale).to_pil()
        finally:
            pdf.close()
    tmp = f"{out_path}.tmp"
    image.save(tmp, "PNG")
    os.replace(tmp, out_path)  # atomik: request lain tidak membaca file setengah jadi
