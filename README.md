# Sistem Reimburse – PT. Duta Sarana Abadi Jaya

Implementasi MVP dari [docs/prd.md](docs/prd.md): pengajuan reimburse transportasi & konsumsi,
OCR struk, verifikasi admin, persetujuan atasan, pembayaran Finance, laporan, dan manajemen pengguna.

| Bagian | Teknologi |
|---|---|
| Frontend | Svelte 5 + SvelteKit 3 (SPA, adapter-static) + TypeScript + Tailwind CSS 4 |
| Backend | Python 3.11 + Flask + SQLAlchemy (REST API JSON di `/api`) |
| OCR | OpenCV (preprocessing) + PaddleOCR + parser rule-based Python — **opsional** |
| Database | SQLite (development); PostgreSQL cukup ganti `DATABASE_URL` |

## Menjalankan (development)

**Backend** (terminal 1):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
$env:FLASK_APP = "wsgi.py"
.\.venv\Scripts\flask init-db        # buat tabel + akun contoh
.\.venv\Scripts\flask run --port 5000
```

**Frontend** (terminal 2):

```powershell
cd frontend
npm install
npm run dev                          # http://localhost:5173 (proxy /api -> Flask)
```

**Tes backend:** `cd backend; .\.venv\Scripts\python -m pytest`

### Akun contoh (password: `password123`)

| Email | Role |
|---|---|
| karyawan@dsaj.co.id, karyawan2@dsaj.co.id | Karyawan (atasan: Budi Atasan) |
| admin.transport@dsaj.co.id | Admin Reimburse Transportasi |
| admin.konsumsi@dsaj.co.id | Admin Reimburse Konsumsi |
| atasan@dsaj.co.id | Atasan |
| finance@dsaj.co.id | Finance |
| superadmin@dsaj.co.id | Super Admin |

## Mengaktifkan OCR

Tanpa paket OCR aplikasi tetap berjalan: endpoint `POST /api/ocr/scan` menyimpan struk,
mencatat status `failed`, dan karyawan mengisi form secara manual (FR-038).

```powershell
cd backend
.\.venv\Scripts\pip install -r requirements-ocr.txt
```

Model PaddleOCR diunduh otomatis saat pertama dipakai. Bahasa model diatur lewat `OCR_LANG`
(default `en`). Aturan parser (kata kunci total, pengecualian, dll.) ada di
`backend/app/ocr/parser.py` (`DEFAULT_RULES`). Parser mengembalikan kosong bila field tidak
ditemukan **atau ambigu** — tidak pernah menebak.

## Alur status

```
Draft → Submitted → Under Review → Pending Approval → Approved → Processing Payment → Paid
                 ↘ Revision Required (kembali ke karyawan)   ↘ Rejected
```

Aturan transisi & otorisasi: `backend/app/services/workflow.py` dan `backend/app/services/access.py`.
Setiap perubahan status tercatat di tabel `approvals` (riwayat) dan `activity_logs`.

## Asumsi (open questions PRD §16)

Disepakati untuk versi ini dan mudah diubah:

1. **Satu struk per pengajuan.** Detail pengeluaran disimpan langsung di tabel `reimbursements`
   (entitas *Reimbursement Details* digabung karena hanya satu item).
2. **Admin boleh menolak secara final** (selain mengembalikan untuk revisi). Alasan wajib.
3. **Atasan = atasan langsung** tiap karyawan (`users.approver_id`), diatur oleh Super Admin.
4. **Export laporan dalam CSV** (bisa dibuka di Excel).
5. Belum ada batas nominal maupun batas waktu pengajuan; tanggal transaksi hanya tidak boleh di masa depan.
6. Kategori tetap dua (Transportasi, Konsumsi) karena terikat pada role admin; belum ada CRUD kategori.

## Catatan untuk produksi

- Ganti `SECRET_KEY`, set `SESSION_COOKIE_SECURE=1` (HTTPS), dan `DATABASE_URL` ke PostgreSQL
  (`pip install psycopg[binary]`, lalu `postgresql+psycopg://user:pass@host/db`).
- Skema dibuat dengan `flask init-db` (`db.create_all`). Tambahkan Flask-Migrate/Alembic
  sebelum skema mulai berubah di produksi.
- Jalankan backend dengan WSGI server (mis. `waitress-serve --port 5000 wsgi:app` di Windows,
  gunicorn di Linux). Contoh Nginx: [deployment/nginx/reimburse.conf](deployment/nginx/reimburse.conf).
- File struk disimpan di `backend/storage/receipts` (di luar folder publik) dan hanya bisa diakses
  lewat API yang memeriksa hak akses.
