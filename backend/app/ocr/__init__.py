from .engine import OcrUnavailable, read_text
from .parser import field_confidence, parse_receipt_with_sources
from .preprocessing import preprocess


def run_ocr(path, model_size="small"):
    """Jalankan pipeline lengkap. Mengembalikan (raw_lines, fields).

    fields berisi merchant, transaction_date, total_amount, dan confidence (skor per field).
    """
    try:
        image = preprocess(path)
    except ImportError as e:
        raise OcrUnavailable("OpenCV belum terpasang di server.") from e
    lines, scores = read_text(image, model_size=model_size)
    fields, sources = parse_receipt_with_sources(lines)
    fields["confidence"] = field_confidence(sources, scores)
    return lines, fields
