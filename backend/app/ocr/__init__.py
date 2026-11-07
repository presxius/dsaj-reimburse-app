from .engine import OcrUnavailable, read_text
from .parser import parse_receipt
from .preprocessing import preprocess


def run_ocr(path, lang="en"):
    """Jalankan pipeline lengkap. Mengembalikan (raw_lines, fields)."""
    try:
        image = preprocess(path)
    except ImportError as e:
        raise OcrUnavailable("OpenCV belum terpasang di server.") from e
    lines = read_text(image, lang=lang)
    return lines, parse_receipt(lines)
