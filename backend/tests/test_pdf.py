import pytest

from app.ocr import OcrUnavailable, pdf, run_ocr

from .conftest import upload


def make_pdf(lines=(), width=226, height=400):
    """PDF satu halaman dengan baris teks Helvetica (lines kosong = seperti PDF hasil scan)."""
    text = "".join(f"BT /F1 10 Tf 10 {height - 20 - 14 * i} Td ({line}) Tj ET\n"
                   for i, line in enumerate(lines)).encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] "
        f"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>".encode(),
        b"<< /Length %d >>\nstream\n" % len(text) + text + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = b"%PDF-1.4\n", []
    for i, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + obj + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
    return out


RECEIPT_LINES = ["KOPI SENJA", "Jl. Merdeka 10", "12/11/2026 09:15",
                 "Kopi Susu 2 x 25.000", "TOTAL 50.000"]


def test_text_pdf_is_read_without_ocr(tmp_path):
    path = tmp_path / "struk.pdf"
    path.write_bytes(make_pdf(RECEIPT_LINES))
    lines, fields = run_ocr(str(path))
    assert lines == RECEIPT_LINES
    assert fields["merchant"] == "KOPI SENJA"
    assert fields["total_amount"] == 50000
    assert fields["confidence"]["total_amount"] == 1.0


def test_scanned_pdf_is_rendered_for_ocr(tmp_path):
    pytest.importorskip("numpy")  # ikut terpasang bersama paket OCR
    path = tmp_path / "scan.pdf"
    path.write_bytes(make_pdf())
    assert pdf.text_lines(str(path)) == []
    image = pdf.render_first_page(str(path))
    assert image.shape == (round(400 * 1600 / 226), 1600, 3)  # BGR, lebar TARGET_WIDTH


def test_upload_pdf(login):
    emp = login("karyawan")
    res = upload(emp, content=make_pdf(RECEIPT_LINES), name="struk.pdf")
    assert res.status_code == 201, res.json
    assert res.json["file_type"] == "application/pdf"
    file = emp.get(f"/api/receipts/{res.json['id']}/file")
    assert file.mimetype == "application/pdf" and file.data.startswith(b"%PDF-")


def test_scan_text_pdf_fills_fields(login):
    emp = login("karyawan")
    res = upload(emp, path="/api/ocr/scan", content=make_pdf(RECEIPT_LINES), name="struk.pdf")
    assert res.status_code == 201, res.json
    assert res.json["ocr"]["status"] == "completed"
    assert res.json["ocr"]["merchant"] == "KOPI SENJA"


def test_reject_broken_pdf(login):
    emp = login("karyawan")
    res = upload(emp, content=b"%PDF-1.4\nbukan pdf", name="rusak.pdf")
    assert res.status_code == 400
    assert "PDF tidak dapat dibaca" in res.json["error"]


def test_reject_extension_content_mismatch(login):
    emp = login("karyawan")
    res = upload(emp, content=make_pdf(RECEIPT_LINES), name="struk.png")
    assert res.status_code == 400
    assert "tidak sesuai" in res.json["error"]


def test_scanned_pdf_without_numpy_reports_ocr_unavailable(tmp_path, monkeypatch):
    def no_numpy(path):
        raise ImportError("numpy")
    monkeypatch.setattr(pdf, "render_first_page", no_numpy)
    path = tmp_path / "scan.pdf"
    path.write_bytes(make_pdf())
    with pytest.raises(OcrUnavailable):
        run_ocr(str(path))


def test_pdf_preview_png(login, app):
    emp = login("karyawan")
    receipt = upload(emp, content=make_pdf(RECEIPT_LINES), name="struk.pdf").json
    for _ in range(2):  # kedua kalinya dari file yang sudah tersimpan
        res = emp.get(f"/api/receipts/{receipt['id']}/preview")
        assert res.status_code == 200
        assert res.mimetype == "image/png" and res.data.startswith(b"\x89PNG")
    # Pengguna lain tidak boleh melihat pratinjau struk orang lain.
    assert login("karyawan2").get(f"/api/receipts/{receipt['id']}/preview").status_code == 403


def test_preview_only_for_pdf(login):
    emp = login("karyawan")
    receipt = upload(emp).json
    assert emp.get(f"/api/receipts/{receipt['id']}/preview").status_code == 404
