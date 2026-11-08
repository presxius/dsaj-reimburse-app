# Sistem Reimburse – PT. Duta Sarana Abadi Jaya

Implementasi MVP dari [docs/prd.md](docs/prd.md): pengajuan reimburse transportasi & konsumsi,
OCR struk, verifikasi admin, persetujuan atasan, pembayaran Finance, laporan, dan manajemen pengguna.

| Bagian | Teknologi |
|---|---|
| Frontend | Svelte 5 + SvelteKit 3 (SPA, adapter-static) + TypeScript + Tailwind CSS 4 |
| Backend | Python 3.11 + Flask + SQLAlchemy (REST API JSON di `/api`) |
| OCR | OpenCV (preprocessing) + PaddleOCR + parser rule-based Python — **opsional** |
| Database | PostgreSQL 16 (production/Docker), SQLite (development); migrasi dengan Flask-Migrate (Alembic) |
| Deployment | Docker Compose: PostgreSQL + Flask (gunicorn) + Nginx |

## Deployment dengan Docker

```bash
cp .env.example .env        # isi POSTGRES_PASSWORD dan SECRET_KEY
docker compose up -d --build
```

Aplikasi terbuka di `http://localhost` (port diatur `HTTP_PORT`). Tiga service berjalan:

| Service | Isi |
|---|---|
| `db` | PostgreSQL 16; data di volume `pgdata`, tidak dibuka ke host |
| `backend` | Flask + gunicorn; saat start menjalankan `flask db upgrade` otomatis. Struk di volume `receipts` |
| `nginx` | Build frontend (multi-stage) + proxy `/api/` ke backend ([default.conf](deployment/nginx/default.conf)) |

Opsi di `.env`: `SEED_DEMO=1` mengisi akun contoh, `WITH_OCR=1` memasang PaddleOCR + OpenCV di image
backend, `SESSION_COOKIE_SECURE=1` bila sudah HTTPS, `WEB_CONCURRENCY` untuk jumlah worker.

Perintah berguna:

```bash
docker compose logs -f backend
docker compose exec backend flask --app wsgi seed                           # akun contoh
docker compose exec db pg_dump -U reimburse reimburse > backup.sql          # backup database
docker compose exec -T db psql -U reimburse reimburse < backup.sql          # restore
```

Volume `receipts` berisi file struk asli; ikut sertakan dalam backup bersama database.

## Database & migrasi

Koneksi diatur lewat `DATABASE_URL` (default SQLite di `backend/instance/reimburse.db`).
Contoh PostgreSQL: `postgresql+psycopg://user:pass@host:5432/reimburse`.

```powershell
cd backend
.\.venv\Scripts\flask --app wsgi db upgrade     # buat/naikkan skema ke versi terbaru
.\.venv\Scripts\flask --app wsgi seed           # akun contoh (dilewati bila sudah ada pengguna)
```

Setelah mengubah model di `app/models.py`, buat migrasi baru lalu periksa isinya sebelum di-commit:

```powershell
.\.venv\Scripts\flask --app wsgi db migrate -m "keterangan perubahan"
.\.venv\Scripts\flask --app wsgi db upgrade
```

Database SQLite lama yang dibuat dengan `flask init-db` (sebelum ada migrasi) cukup ditandai sekali
dengan `flask --app wsgi db stamp head`. Tes dapat dijalankan terhadap PostgreSQL dengan
`TEST_DATABASE_URL=postgresql+psycopg://...`.

## Menjalankan (development)

**Backend** (terminal 1):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
$env:FLASK_APP = "wsgi.py"
.\.venv\Scripts\flask db upgrade     # buat tabel (lihat "Database & migrasi")
.\.venv\Scripts\flask seed           # akun contoh
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

- Ganti `SECRET_KEY`, set `SESSION_COOKIE_SECURE=1` (HTTPS), dan `DATABASE_URL` ke PostgreSQL.
  Jangan aktifkan `SEED_DEMO` (akun contoh memakai password yang diketahui umum).
- HTTPS: pasang di depan service `nginx` (mis. reverse proxy/load balancer perusahaan) atau
  tambahkan blok `listen 443 ssl` di [default.conf](deployment/nginx/default.conf).
- Tanpa Docker: jalankan `flask db upgrade`, lalu gunicorn (`gunicorn -b 127.0.0.1:5000 --timeout 120 wsgi:app`)
  dan Nginx dengan [deployment/nginx/reimburse.conf](deployment/nginx/reimburse.conf).
- File struk disimpan di `backend/storage/receipts` (di luar folder publik) dan hanya bisa diakses
  lewat API yang memeriksa hak akses.
