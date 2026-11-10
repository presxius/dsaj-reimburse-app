from datetime import date
from decimal import Decimal

from app.ocr.parser import parse_amount, parse_receipt


def test_typical_indonesian_receipt():
    lines = [
        "KOPI SENJA",
        "Jl. Sudirman No. 10 Jakarta",
        "Telp 021-555123",
        "12/03/2026 14:22",
        "Es Kopi Susu 2 x 25.000 50.000",
        "SUBTOTAL 50.000",
        "PPN 10% 5.000",
        "TOTAL Rp 55.000",
        "TUNAI 100.000",
        "KEMBALI 45.000",
    ]
    result = parse_receipt(lines)
    assert result == {
        "merchant": "KOPI SENJA",
        "transaction_date": date(2026, 3, 12),
        "total_amount": Decimal("55000.00"),
    }


def test_total_on_next_line_and_text_month():
    lines = ["GRAB", "5 Mei 2026", "Grand Total", "Rp 32.500"]
    result = parse_receipt(lines)
    assert result["transaction_date"] == date(2026, 5, 5)
    assert result["total_amount"] == Decimal("32500.00")


def test_missing_fields_stay_empty():
    result = parse_receipt(["1234 5678", "blurry ###"])
    assert result == {"merchant": None, "transaction_date": None, "total_amount": None}


def test_ambiguous_values_are_not_guessed():
    lines = ["TOKO A", "01/02/2026", "03/02/2026", "TOTAL 10.000", "TOTAL 12.000"]
    result = parse_receipt(lines)
    assert result["transaction_date"] is None
    assert result["total_amount"] is None


def test_bank_receipt_uses_labeled_merchant():
    # Hasil OCR bukti QRIS SeaBank (data pribadi dianonimkan). Baris pertama = logo bank.
    lines = [
        "SeaBank",
        "Bukti Transaksi",
        "Rp 17.000",
        "Dari Rina Karyawan",
        "SeaBank: ********1234",
        "Ke Nasi Goreng Suroboyo K...",
        "Jakarta Selatan",
        "Nama Acquirer OVO",
        "Metode Pembayaran SeaBank",
        "Jumlah Rp 17.000",
        "No. Transaksi 2026101600000000000000001",
        "Waktu Transaksi 16 Okt 2026, 12:49",
        "Resi ini merupakan bukti transaksi yang sah.",
    ]
    assert parse_receipt(lines) == {
        "merchant": "Nasi Goreng Suroboyo K...",
        "transaction_date": date(2026, 10, 16),
        "total_amount": Decimal("17000.00"),
    }


def test_app_screenshot_uses_service_name():
    # Hasil OCR screenshot email GoRide di dokumen form reimburse (data pribadi dianonimkan).
    lines = [
        "10:53 X … 0,52 73%",
        "KB/d",
        "← FORM REIMBURS...",
        "FORM REIMBURSEMENT",
        "Rabu, 04 - 11 - 2026",
        "gorider CEPAAAT Rabu. 4 November 2026",
        "ID pesanan: RB-0000000-00000000",
        "Makasih udah pesan GoRide CEPAAAT",
        "Total dibayar Rp32.500",
        "Biaya perjalanan Rp27.000",
        "Biaya jasa aplikasi Rp4.500",
        "Total pembayaran Rp32.500",
        "Dibayar pakai GoPay Rp32.500",
        "Budi Driver Dijemput 4 November 2026",
        "Sampai 4 November 2026 jam",
        "Total : 32.500",
    ]
    assert parse_receipt(lines) == {
        "merchant": "GoRide",
        "transaction_date": date(2026, 11, 4),
        "total_amount": Decimal("32500.00"),
    }


def test_screenshot_chrome_is_not_a_merchant():
    lines = ["10:53 X … 0,52 73%", "KB/d", "← Detail Pesanan", "FORM REIMBURSEMENT",
             "Total Rp 20.000"]
    assert parse_receipt(lines)["merchant"] is None


def test_ambiguous_merchant_is_not_guessed():
    assert parse_receipt(["Ke Toko Satu", "Ke Toko Dua"])["merchant"] is None
    assert parse_receipt(["Pesan GoRide", "Promo GoFood"])["merchant"] is None


def test_parse_amount_formats():
    assert parse_amount("25.000") == Decimal("25000.00")
    assert parse_amount("25,000.00") == Decimal("25000.00")
    assert parse_amount("12.500,50") == Decimal("12500.50")
    assert parse_amount("7500") == Decimal("7500.00")


def test_custom_rules():
    lines = ["WARUNG", "BAYAR 15.000"]
    assert parse_receipt(lines)["total_amount"] is None
    assert parse_receipt(lines, {"total_keywords": ["bayar"]})["total_amount"] == Decimal("15000.00")
