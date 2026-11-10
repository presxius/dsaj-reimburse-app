"""Pembungkus PaddleOCR. Model dimuat sekali (lazy) saat pertama dipakai."""
import os
import threading

_engine = None
_lock = threading.Lock()


class OcrUnavailable(Exception):
    pass


def _get_engine(model_size):
    global _engine
    with _lock:
        if _engine is None:
            try:
                from paddleocr import PaddleOCR
            except ImportError as e:
                raise OcrUnavailable("PaddleOCR belum terpasang di server.") from e
            _engine = PaddleOCR(
                # Model PP-OCRv6 (tiny/small/medium) mencakup huruf Latin, cukup untuk struk.
                text_detection_model_name=f"PP-OCRv6_{model_size}_det",
                text_recognition_model_name=f"PP-OCRv6_{model_size}_rec",
                # Default pipeline juga memuat model orientasi dokumen, unwarping (UVDoc), dan
                # orientasi baris; tidak perlu untuk struk yang tegak dan memakan banyak RAM.
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                # oneDNN (MKLDNN) di PaddlePaddle 3.3 CPU gagal saat inferensi
                # ("ConvertPirAttribute2RuntimeAttribute not support"); matikan.
                enable_mkldnn=False,
                cpu_threads=os.cpu_count() or 1,  # default 10, berlebihan di server kecil
            )
        return _engine


def read_text(image, model_size="small"):
    """Kembalikan daftar baris teks, berurutan dari atas ke bawah."""
    engine = _get_engine(model_size)
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
