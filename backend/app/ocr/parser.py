"""Parser rule-based: teks OCR -> kandidat merchant, tanggal, total (FR-034, FR-040).

Prinsip (Business Rule 21): jika field tidak ditemukan atau ambigu, kembalikan None.
Parser tidak boleh menebak nilai.

Aturan bisa diganti lewat argumen `rules` (mis. dari konfigurasi aplikasi).
"""
import re
from datetime import date
from decimal import Decimal

DEFAULT_RULES = {
    # Urutan = prioritas. Kata kunci di depan lebih diutamakan.
    "total_keywords": ["grand total", "total bayar", "total belanja", "total tagihan",
                       "total", "jumlah", "tagihan"],
    # Baris yang mengandung kata ini bukan total akhir.
    "total_exclude": ["subtotal", "sub total", "sub-total", "total item", "total qty",
                      "total disc", "diskon", "kembali", "kembalian", "change", "tunai", "cash"],
    # Nama layanan aplikasi yang tertulis di struk/screenshot (mis. "pesan GoRide").
    # Sengaja tanpa "Gojek"/"Grab": sering muncul juga di bukti bayar GoPay/OVO ke merchant lain.
    "merchant_brands": ["GoRide", "GoCar", "GoFood", "GrabBike", "GrabCar", "GrabFood",
                        "ShopeeFood", "Maxim", "inDrive"],
    # Label nama merchant pada bukti transaksi bank/e-wallet (mis. SeaBank: "Ke <merchant>").
    "merchant_labels": ["nama merchant", "merchant", "nama penerima", "penerima", "ke"],
    # Baris yang tidak mungkin berupa nama merchant.
    "merchant_exclude": ["jl.", "jl ", "jalan", "telp", "tel.", "phone", "npwp", "struk",
                         "receipt", "invoice", "no.", "kasir", "cashier", "www", "http",
                         "bukti", "reimburs"],
    "merchant_scan_lines": 5,
}

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "mei": 5, "may": 5, "jun": 6, "jul": 7,
    "agu": 8, "agt": 8, "aug": 8, "sep": 9, "okt": 10, "oct": 10, "nov": 11, "des": 12, "dec": 12,
}

_DATE_NUMERIC = re.compile(r"\b(\d{1,4})[/.\-](\d{1,2})[/.\-](\d{2,4})\b")
_DATE_TEXT = re.compile(r"\b(\d{1,2})[\s\-]+([A-Za-z]{3,9})[\s\-]+(\d{2,4})\b")
_AMOUNT = re.compile(r"\d[\d.,]*")
_WORD = re.compile(r"[^\W\d_]{3,}")  # kata minimal 3 huruf


def parse_receipt(lines, rules=None):
    return parse_receipt_with_sources(lines, rules)[0]


def parse_receipt_with_sources(lines, rules=None):
    """Seperti parse_receipt, plus indeks baris (pada `lines` asli) tempat tiap nilai dibaca.

    Mengembalikan (fields, sources); sources hanya berisi field yang ditemukan.
    """
    rules = {**DEFAULT_RULES, **(rules or {})}
    kept = [(i, ln.strip()) for i, ln in enumerate(lines) if ln and ln.strip()]
    original = [i for i, _ in kept]
    lines = [ln for _, ln in kept]
    found = {
        "merchant": find_merchant(lines, rules),
        "transaction_date": find_date(lines),
        "total_amount": find_total(lines, rules),
    }
    fields = {k: value for k, (value, _) in found.items()}
    sources = {k: [original[i] for i in idxs] for k, (value, idxs) in found.items() if value is not None}
    return fields, sources


def field_confidence(sources, scores):
    """Skor per field = skor terbaik dari baris asalnya (nilai bisa terbaca di beberapa baris)."""
    result = {}
    for field, idxs in sources.items():
        known = [scores[i] for i in idxs if i < len(scores) and scores[i] is not None]
        result[field] = round(max(known), 3) if known else None
    return result


def _single(hits):
    """{nilai: indeks baris}: satu nilai -> (nilai, baris); kosong atau ambigu -> (None, [])."""
    if len(hits) != 1:
        return None, []
    (value, idxs), = hits.items()
    return value, sorted(idxs)


def find_merchant(lines, rules):
    # 1) Nama layanan aplikasi. Lebih dari satu layanan berbeda = ambigu.
    hits = {}
    for b in rules["merchant_brands"]:
        pattern = re.compile(rf"(?<![^\W\d_]){re.escape(b)}(?![^\W\d_])", re.IGNORECASE)
        idxs = {i for i, line in enumerate(lines) if pattern.search(line)}
        if idxs:
            hits[b] = idxs
    if hits:
        return _single(hits)

    # 2) Nilai berlabel, mis. "Ke Nasi Goreng Suroboyo" atau "Merchant: Kopi Senja".
    for label in rules["merchant_labels"]:
        pattern = re.compile(rf"{re.escape(label)}(?:\s*:\s*|\s+)(.+)", re.IGNORECASE)
        hits = {}
        for i, line in enumerate(lines):
            m = pattern.match(line)
            if m and _looks_like_merchant(value := m.group(1).strip(), rules):
                hits.setdefault(value[:200], set()).add(i)
        if hits:
            return _single(hits)  # lebih dari satu nilai = ambigu

    # 3) Struk kertas: nama toko biasanya di baris paling atas.
    for i, line in enumerate(lines[: rules["merchant_scan_lines"]]):
        if _looks_like_merchant(line, rules):
            return line[:200], [i]
    return None, []


def _looks_like_merchant(line, rules):
    if line.startswith(("←", "<", "‹", "«")):  # bar navigasi pada screenshot aplikasi
        return False
    # Wajib ada kata >= 3 huruf (menyaring sisa status bar HP seperti "KB/d") dan mayoritas huruf.
    letters = sum(c.isalpha() for c in line)
    if not _WORD.search(line) or letters < len(line.replace(" ", "")) * 0.7:
        return False
    low = line.lower()
    if any(k in low for k in rules["merchant_exclude"]):
        return False
    return not _find_dates_in(line)


def _to_year(y):
    y = int(y)
    return y + 2000 if y < 100 else y


def _safe_date(y, m, d):
    try:
        return date(y, m, d)
    except ValueError:
        return None


def _find_dates_in(line):
    found = []
    for a, b, c in _DATE_NUMERIC.findall(line):
        if len(a) == 4:  # yyyy-mm-dd
            dt = _safe_date(int(a), int(b), int(c))
        else:  # dd/mm/yyyy (format Indonesia)
            dt = _safe_date(_to_year(c), int(b), int(a))
        if dt:
            found.append(dt)
    for d, mon, y in _DATE_TEXT.findall(line):
        m = MONTHS.get(mon[:3].lower())
        if m:
            dt = _safe_date(_to_year(y), m, int(d))
            if dt:
                found.append(dt)
    return found


def find_date(lines):
    hits = {}
    for i, line in enumerate(lines):
        for dt in _find_dates_in(line):
            if 2000 <= dt.year <= date.today().year + 1:
                hits.setdefault(dt, set()).add(i)
    # Lebih dari satu tanggal berbeda = ambigu -> kosongkan.
    return _single(hits)


def parse_amount(token):
    """'25.000' -> 25000, '25,000.00' -> 25000.00, '12.500,50' -> 12500.50."""
    token = token.strip(".,")
    if not token:
        return None
    decimals = "00"
    m = re.search(r"[.,](\d{2})$", token)
    if m and (len(re.findall(r"[.,]", token)) > 1 or re.fullmatch(r"\d+[.,]\d{2}", token)):
        decimals = m.group(1)
        token = token[: m.start()]
    digits = re.sub(r"[.,]", "", token)
    if not digits.isdigit():
        return None
    return Decimal(f"{int(digits)}.{decimals}")


def _amounts_in(line):
    # Abaikan angka yang menempel pada tanggal/jam.
    cleaned = _DATE_NUMERIC.sub(" ", line)
    cleaned = re.sub(r"\b\d{1,2}:\d{2}(:\d{2})?\b", " ", cleaned)
    return [a for a in (parse_amount(t) for t in _AMOUNT.findall(cleaned)) if a and a > 0]


def find_total(lines, rules):
    for keyword in rules["total_keywords"]:
        candidates = {}  # nominal -> baris tempat nominal terbaca
        for i, line in enumerate(lines):
            low = line.lower()
            if keyword not in low or any(x in low for x in rules["total_exclude"]):
                continue
            src = i
            amounts = _amounts_in(line)
            if not amounts and i + 1 < len(lines):  # nominal di baris berikutnya
                src = i + 1
                amounts = _amounts_in(lines[src])
            if amounts:
                candidates.setdefault(amounts[-1], set()).add(src)
        if candidates:
            return _single(candidates)  # lebih dari satu nominal = ambigu
    return None, []
