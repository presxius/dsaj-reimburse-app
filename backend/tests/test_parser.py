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


def test_parse_amount_formats():
    assert parse_amount("25.000") == Decimal("25000.00")
    assert parse_amount("25,000.00") == Decimal("25000.00")
    assert parse_amount("12.500,50") == Decimal("12500.50")
    assert parse_amount("7500") == Decimal("7500.00")


def test_custom_rules():
    lines = ["WARUNG", "BAYAR 15.000"]
    assert parse_receipt(lines)["total_amount"] is None
    assert parse_receipt(lines, {"total_keywords": ["bayar"]})["total_amount"] == Decimal("15000.00")
