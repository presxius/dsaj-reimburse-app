from . import pdf
from .engine import OcrUnavailable, read_text
from .parser import field_confidence, parse_receipt_with_sources
from .preprocessing import preprocess


def run_ocr(path, model_size="small"):
    """Jalankan pipeline lengkap. Mengembalikan (raw_lines, fields).

    fields berisi merchant, transaction_date, total_amount, dan confidence (skor per field).
    PDF dengan lapisan teks dibaca langsung (skor 1.0, tanpa OCR); PDF scan dirender lalu di-OCR.
    """
    is_pdf = path.lower().endswith(".pdf")
    if is_pdf and (lines := pdf.text_lines(path)):
        return lines, _fields(lines, [1.0] * len(lines))
    try:
        # Render PDF butuh numpy, yang ikut terpasang bersama paket OCR.
        image = preprocess(pdf.render_first_page(path) if is_pdf else path)
    except ImportError as e:
        raise OcrUnavailable("OpenCV belum terpasang di server.") from e
    lines, scores = read_text(image, model_size=model_size)
    return lines, _fields(lines, scores)


def _fields(lines, scores):
    fields, sources = parse_receipt_with_sources(lines)
    fields["confidence"] = field_confidence(sources, scores)
    return fields
