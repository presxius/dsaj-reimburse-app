"""Pembungkus PaddleOCR. Model dimuat sekali (lazy) saat pertama dipakai."""
import threading

_engine = None
_lock = threading.Lock()


class OcrUnavailable(Exception):
    pass


def _get_engine(lang):
    global _engine
    with _lock:
        if _engine is None:
            try:
                from paddleocr import PaddleOCR
            except ImportError as e:
                raise OcrUnavailable("PaddleOCR belum terpasang di server.") from e
            _engine = PaddleOCR(lang=lang)
        return _engine


def read_text(image, lang="en"):
    """Kembalikan daftar baris teks, berurutan dari atas ke bawah."""
    engine = _get_engine(lang)
    with _lock:  # instance PaddleOCR tidak thread-safe
        if hasattr(engine, "predict"):  # PaddleOCR 3.x
            result = engine.predict(image)
        else:  # PaddleOCR 2.x
            result = engine.ocr(image, cls=True)
    return _to_lines(result)


def _to_lines(result):
    items = []  # (y, x, text)
    for page in result or []:
        if page is None:
            continue
        if isinstance(page, dict) or hasattr(page, "get"):  # format 3.x
            texts = page.get("rec_texts") or []
            boxes = page.get("rec_polys")
            if boxes is None:
                boxes = page.get("dt_polys")
            for i, text in enumerate(texts):
                box = boxes[i] if boxes is not None and i < len(boxes) else [[0, i]]
                items.append((float(box[0][1]), float(box[0][0]), text))
        else:  # format 2.x: [[box, (text, conf)], ...]
            for box, (text, _conf) in page:
                items.append((float(box[0][1]), float(box[0][0]), text))
    return _group_rows(items)


def _group_rows(items, tolerance=12):
    """Gabungkan potongan teks yang sejajar secara horizontal menjadi satu baris."""
    items.sort()
    rows = []
    for y, x, text in items:
        if rows and abs(rows[-1][0] - y) <= tolerance:
            rows[-1][1].append((x, text))
        else:
            rows.append([y, [(x, text)]])
    return [" ".join(t for _, t in sorted(parts)) for _, parts in rows]
