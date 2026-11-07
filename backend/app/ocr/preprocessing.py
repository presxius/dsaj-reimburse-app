"""Preprocessing gambar struk dengan OpenCV sebelum OCR (FR-039).

File asli tidak diubah; fungsi ini bekerja pada salinan di memori.
"""


def preprocess(path):
    import cv2  # import di sini agar backend tetap jalan tanpa OpenCV

    img = cv2.imread(path)
    if img is None:
        raise ValueError("Gambar tidak dapat dibaca.")

    # Normalisasi ukuran: struk kecil diperbesar, foto sangat besar diperkecil.
    h, w = img.shape[:2]
    target_w = min(max(w, 1000), 1800)
    if target_w != w:
        scale = target_w / w
        interp = cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA
        img = cv2.resize(img, (target_w, int(h * scale)), interpolation=interp)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 7, 50, 50)  # kurangi noise, pertahankan tepi huruf
    # PaddleOCR menerima 3 channel.
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
