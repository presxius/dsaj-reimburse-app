"""Pengajuan dengan beberapa item pengeluaran."""
from app.models import MAX_ITEMS, MAX_RECEIPTS_PER_ITEM, Receipt

from .conftest import PNG, item, new_submission, upload


def act(client, rid, action, **body):
    return client.post(f"/api/reimbursements/{rid}/actions/{action}", json=body)


def items_payload(detail, **overrides):
    """Payload PUT yang mempertahankan item dan struk yang ada."""
    return [{"id": i["id"], "merchant": i["merchant"], "transaction_date": i["transaction_date"],
             "amount": i["amount"], "note": i["note"],
             "receipt_ids": [rc["id"] for rc in i["receipts"]], **overrides} for i in detail["items"]]


def test_total_is_sum_of_items(login):
    emp = login("karyawan")
    res = new_submission(emp, items=[
        item(emp, merchant="GoRide", transaction_date="2026-11-04", amount=32500, content=PNG + b"1"),
        item(emp, merchant="GoRide", transaction_date="2026-11-05", amount=28000, content=PNG + b"2"),
        item(emp, merchant="Grab", transaction_date="2026-11-06", amount=41000, content=PNG + b"3",
             note="Pulang lembur"),
    ])
    assert res.status_code == 201, res.json
    r = res.json
    assert r["amount"] == 101500 and r["item_count"] == 3
    assert r["merchants"] == ["GoRide", "Grab"]
    assert (r["date_from"], r["date_to"]) == ("2026-11-04", "2026-11-06")
    assert [i["note"] for i in r["items"]] == [None, None, "Pulang lembur"]

    listed = emp.get("/api/reimbursements").json[0]
    assert listed["item_count"] == 3 and "items" not in listed


def test_item_can_have_several_receipts(login):
    emp = login("karyawan")
    ids = [upload(emp, content=PNG + bytes([n])).json["id"] for n in range(2)]
    res = new_submission(emp, items=[item(emp, receipt=False, receipt_ids=ids)])
    assert [rc["id"] for rc in res.json["items"][0]["receipts"]] == ids

    too_many = [upload(emp, content=PNG + bytes([n])).json["id"] for n in range(MAX_RECEIPTS_PER_ITEM + 1)]
    res = new_submission(emp, items=[item(emp, receipt=False, receipt_ids=too_many)])
    assert res.status_code == 400 and f"Maksimal {MAX_RECEIPTS_PER_ITEM}" in res.json["error"]


def test_item_limit(login):
    emp = login("karyawan")
    rows = [item(emp, receipt=False) for _ in range(MAX_ITEMS + 1)]
    res = new_submission(emp, submit=False, items=rows)
    assert res.status_code == 400 and f"Maksimal {MAX_ITEMS} item" in res.json["error"]


def test_error_names_the_item(login):
    emp = login("karyawan")
    res = new_submission(emp, items=[item(emp), item(emp, amount="abc")])
    assert res.status_code == 400 and res.json["error"].startswith("Item 2:")


def test_receipt_cannot_be_used_twice(login):
    emp = login("karyawan")
    rid = upload(emp).json["id"]
    both = [item(emp, receipt=False, receipt_ids=[rid]), item(emp, receipt=False, receipt_ids=[rid])]
    assert new_submission(emp, items=both).status_code == 400

    assert new_submission(emp, items=[item(emp, receipt=False, receipt_ids=[rid])]).status_code == 201
    # Struk yang sudah terpasang di pengajuan lain tidak bisa dipakai lagi.
    again = new_submission(emp, items=[item(emp, receipt=False, receipt_ids=[rid])])
    assert again.status_code == 400 and "Struk tidak valid" in again.json["error"]
    # Struk milik karyawan lain juga tidak.
    other = login("karyawan2")
    assert new_submission(other, items=[item(other, receipt=False, receipt_ids=[upload(emp).json["id"]])]).status_code == 400


def test_update_adds_removes_and_moves(app, login):
    emp = login("karyawan")
    draft = new_submission(emp, submit=False, items=[
        item(emp, merchant="A", content=PNG + b"a"), item(emp, merchant="B", content=PNG + b"b")]).json
    a, b = draft["items"]
    b_receipt = b["receipts"][0]["id"]

    # Hapus item B, pindahkan struknya ke item A, tambah item C baru.
    new = item(emp, merchant="C", amount=12000, content=PNG + b"c")
    body = {"category": "transport", "purpose": "Revisi",
            "items": [{**items_payload(draft)[0], "receipt_ids": [a["receipts"][0]["id"], b_receipt]}, new]}
    res = emp.put(f"/api/reimbursements/{draft['id']}", json=body)
    assert res.status_code == 200, res.json
    items = res.json["items"]
    assert [i["merchant"] for i in items] == ["A", "C"]
    assert items[0]["id"] == a["id"]
    assert [rc["id"] for rc in items[0]["receipts"]] == [a["receipts"][0]["id"], b_receipt]
    assert res.json["amount"] == 62000

    # Struk yang dilepas tetap ada di storage, hanya tidak terpasang ke item mana pun.
    c_receipt = items[1]["receipts"][0]["id"]
    body["items"] = [body["items"][0], {**new, "id": items[1]["id"], "receipt_ids": []}]
    assert emp.put(f"/api/reimbursements/{draft['id']}", json=body).status_code == 200
    assert app.extensions["sqlalchemy"].session.get(Receipt, c_receipt).item_id is None


def test_cannot_edit_foreign_item(login):
    emp = login("karyawan")
    first = new_submission(emp, submit=False).json
    second = new_submission(emp, submit=False).json
    body = {"category": "transport", "purpose": "X", "items": items_payload(first)}
    res = emp.put(f"/api/reimbursements/{second['id']}", json=body)
    assert res.status_code == 400


def test_return_with_item_notes(login):
    emp = login("karyawan")
    r = new_submission(emp, items=[item(emp, merchant="GoRide", content=PNG + b"1"),
                                   item(emp, merchant="Grab", content=PNG + b"2")]).json
    first, second = r["items"]
    admin = login("admin.transport")
    assert act(admin, r["id"], "admin_return", item_notes={"99999": "x"}).status_code == 400

    # Catatan per item saja sudah cukup sebagai alasan.
    res = act(admin, r["id"], "admin_return", item_notes={str(second["id"]): "Struk buram"})
    assert res.status_code == 200 and res.json["status"] == "revision_required"
    assert [i["review_note"] for i in res.json["items"]] == [None, "Struk buram"]
    assert "Item 2 (Grab): Struk buram" in res.json["history"][-1]["note"]

    detail = emp.get(f"/api/reimbursements/{r['id']}").json
    body = {"category": "transport", "purpose": "Taksi", "submit": True, "items": items_payload(detail)}
    res = emp.put(f"/api/reimbursements/{r['id']}", json=body)
    assert res.status_code == 200 and res.json["status"] == "submitted"
    assert [i["review_note"] for i in res.json["items"]] == [None, None]
    # Riwayat tetap menyimpan catatannya.
    assert "Struk buram" in res.json["history"][-2]["note"]


def test_duplicate_inside_same_claim(login):
    emp = login("karyawan")
    r = new_submission(emp, items=[item(emp, content=PNG + b"1"), item(emp, content=PNG + b"2")]).json
    dupes = emp.get(f"/api/reimbursements/{r['id']}").json["duplicates"]
    first, second = (str(i["id"]) for i in r["items"])
    assert [(d["item_id"], d["reason"], d["same_claim"]) for d in dupes[first]] == [
        (int(second), "same_data", True)]


def test_filters_use_items(login):
    emp = login("karyawan")
    new_submission(emp, items=[item(emp, merchant="GoRide", transaction_date="2026-11-04", content=PNG + b"1"),
                               item(emp, merchant="Grab", transaction_date="2026-11-20", content=PNG + b"2")])
    fin = login("superadmin")
    assert len(fin.get("/api/reimbursements?q=grab").json) == 1
    assert len(fin.get("/api/reimbursements?q=bluebird").json) == 0
    assert len(fin.get("/api/reimbursements?date_from=2026-11-10&date_to=2026-11-30").json) == 1
    assert len(fin.get("/api/reimbursements?date_from=2026-11-05&date_to=2026-11-19").json) == 0


def test_csv_has_one_row_per_item(login):
    emp = login("karyawan")
    new_submission(emp, items=[item(emp, merchant="GoRide", amount=32500, content=PNG + b"1"),
                               item(emp, merchant="Grab", amount=41000, content=PNG + b"2")])
    lines = login("admin.transport").get("/api/reports/export").data.decode("utf-8-sig").splitlines()
    assert len(lines) == 3
    assert "GoRide" in lines[1] and "32500.00" in lines[1] and "73500.00" in lines[1]
    assert "Grab" in lines[2]


def test_admin_can_view_every_receipt_of_claim(login):
    emp = login("karyawan")
    ids = [upload(emp, content=PNG + bytes([n])).json["id"] for n in range(2)]
    new_submission(emp, items=[item(emp, receipt=False, receipt_ids=ids)])
    admin, other = login("admin.transport"), login("karyawan2")
    for rid in ids:
        assert admin.get(f"/api/receipts/{rid}/file").status_code == 200
        assert other.get(f"/api/receipts/{rid}/file").status_code == 403
