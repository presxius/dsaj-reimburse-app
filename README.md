# Sistem Reimburse – PT. Duta Sarana Abadi Jaya

Implementasi MVP dari [docs/prd.md](docs/prd.md): pengajuan reimburse transportasi & konsumsi,
OCR struk, verifikasi admin, persetujuan atasan, pembayaran Finance, laporan, dan manajemen pengguna.

| Bagian | Teknologi |
|---|---|
| Frontend | Svelte 5 + SvelteKit 3 (SPA, adapter-static) + TypeScript + Tailwind CSS 4 |
| Backend | Python 3.11 + Flask + SQLAlchemy (REST API JSON di `/api`) |
| OCR | OpenCV (preprocessing) + PaddleOCR + parser rule-based Python — **opsional** |
| Database | PostgreSQL 18; migrasi dengan Flask-Migrate (Alembic) |
| Deployment | Docker Compose: PostgreSQL + Flask (gunicorn) + Nginx |

## Deployment dengan Docker

```bash
cp .env.example .env        # isi POSTGRES_PASSWORD dan SECRET_KEY
docker compose up -d --build
```

Aplikasi terbuka di `http://localhost` (port diatur `HTTP_PORT`). Tiga service berjalan:

| Service | Isi |
|---|---|
| `db` | PostgreSQL 18; data di volume `pgdata`, tidak dibuka ke host |
| `backend` | Flask + gunicorn; saat start menjalankan `flask db upgrade` otomatis. Struk di volume `receipts` |
| `nginx` | Build frontend (multi-stage) + proxy `/api/` ke backend ([default.conf](deployment/nginx/default.conf)) |

Opsi di `.env`: `SEED_DEMO=1` mengisi akun contoh, `WITH_OCR=1` memasang PaddleOCR + OpenCV di image
backend, `SESSION_COOKIE_SECURE=1` bila sudah HTTPS, `WEB_CONCURRENCY` untuk jumlah worker (default 1, masing-masing 4 thread).

Perintah berguna:

```bash
docker compose logs -f backend
docker compose exec backend flask --app wsgi seed                           # akun contoh
```

## Backup & restore

[deployment/backup.sh](deployment/backup.sh) membackup database (`pg_dump` format custom, diverifikasi
dengan `pg_restore --list`) dan volume `receipts` (file struk asli), lalu menghapus backup yang lebih
tua dari `KEEP_DAYS` hari (default 14). Tujuan default `/var/backups/reimburse`, bisa diganti lewat `BACKUP_DIR`.

```bash
sudo ./deployment/backup.sh                              # jalankan manual
sudo BACKUP_DIR=/mnt/nas/reimburse KEEP_DAYS=30 ./deployment/backup.sh
```

Jadwalkan harian lewat crontab root (`sudo crontab -e`), mis. setiap pukul 01.30:

```cron
30 1 * * * /opt/apps/dsaj-reimburse-app/deployment/backup.sh >> /var/log/reimburse-backup.log 2>&1
```

Backup di disk VM yang sama tidak menolong bila VM/disknya rusak. Salin juga secara berkala ke
mesin lain atau NAS (mis. `BACKUP_DIR` di mount NAS, atau `rsync` terjadwal).

Restore (menimpa data saat ini; ganti `<waktu>` dengan nama file backup):

```bash
docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner' \
  < /var/backups/reimburse/db-<waktu>.dump
docker compose exec -T backend tar -C /app/storage -xzf - < /var/backups/reimburse/receipts-<waktu>.tar.gz
```

Uji restore sesekali di server/VM lain agar yakin backup benar-benar bisa dipakai.

## Database & migrasi

Aplikasi hanya memakai PostgreSQL. Koneksi diatur lewat `DATABASE_URL` (wajib), contoh:
`postgresql+psycopg://user:pass@host:5432/reimburse`. Di Docker variabel ini diisi otomatis.

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

Memulai database dari nol (menghapus **semua** data dan struk di volume Docker):

```bash
docker compose down -v
docker compose up -d --build      # skema dibuat ulang oleh `flask db upgrade`
```

Tes memakai database terpisah lewat `TEST_DATABASE_URL=postgresql+psycopg://...`
(tanpa variabel ini tes berjalan di SQLite in-memory).

## Menjalankan (development)

**Database** — PostgreSQL dari Docker, dibuka di `localhost:5432` ([docker-compose.dev.yml](docker-compose.dev.yml)):

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db
```

**Backend** (terminal 1):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
$env:FLASK_APP = "wsgi.py"
$env:DATABASE_URL = "postgresql+psycopg://reimburse:<POSTGRES_PASSWORD>@localhost:5432/reimburse"
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

Di server tanpa Python lokal, jalankan tes di image backend dengan kode terbaru di-mount
(folder `tests/` tidak ikut ke image; tes memakai SQLite in-memory, database produksi tidak disentuh):

```bash
sudo docker compose run --rm --no-deps -v "$PWD/backend:/app" --entrypoint python backend -m pytest -q -p no:cacheprovider
```

**CI:** [.github/workflows/ci.yml](.github/workflows/ci.yml) menjalankan tes backend (SQLite dan PostgreSQL 18),
`svelte-check`, dan build frontend + image Docker pada setiap push dan pull request.

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

Model PaddleOCR (PP-OCRv6) diunduh otomatis saat pertama dipakai. Ukurannya diatur lewat
`OCR_MODEL_SIZE`: `tiny`, `small` (default), atau `medium`. Makin besar makin akurat tetapi butuh RAM
lebih banyak; di server ±1 GB RAM pakai `small` atau `tiny` dengan `WEB_CONCURRENCY=1`, karena setiap
worker gunicorn memuat model sendiri. Aturan parser (kata kunci total, pengecualian, dll.) ada di
`backend/app/ocr/parser.py` (`DEFAULT_RULES`). Parser mengembalikan kosong bila field tidak
ditemukan **atau ambigu** — tidak pernah menebak.

Setiap field hasil OCR membawa **skor keyakinan** (0–1, kolom `ocr_results.confidence`), diambil dari
skor PaddleOCR pada baris tempat nilai itu terbaca. Field dengan skor di bawah 90%
(`OCR_LOW_CONFIDENCE` di `frontend/src/lib/labels.ts`) ditandai kuning di form dan halaman detail.

## Deteksi struk duplikat

Pengajuan ditandai "kemungkinan ganda" (peringatan saja, tidak memblokir) bila ada pengajuan lain
yang bukan draft dengan:

- **file struk identik** (hash SHA-256 isi file, kolom `receipts.sha256`), atau
- **kategori, tanggal, dan nominal sama**, dari karyawan yang sama atau dengan merchant yang sama.

Karyawan diperingatkan saat mengunggah struk yang sudah pernah ia ajukan; admin/atasan/finance melihat
banner di halaman detail. Daftar duplikat hanya berisi pengajuan yang boleh dilihat pengguna tersebut.
Logika: `backend/app/services/duplicates.py`.

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

- Ganti `SECRET_KEY` dan set `SESSION_COOKIE_SECURE=1` (HTTPS).
  Jangan aktifkan `SEED_DEMO` (akun contoh memakai password yang diketahui umum).
- Login dikunci sementara per email setelah 5 kali gagal dalam 15 menit (`MAX_FAILED_LOGINS`,
  `LOCKOUT_WINDOW` di `backend/app/routes/auth.py`), dicatat sebagai `auth.login_failed` di log aktivitas.
  Percobaan saat terkunci tidak memperpanjang kunci.
- HTTPS: pasang di depan service `nginx` (mis. reverse proxy/load balancer perusahaan) atau
  tambahkan blok `listen 443 ssl` di [default.conf](deployment/nginx/default.conf).
- Tanpa Docker: jalankan `flask db upgrade`, lalu gunicorn (`gunicorn -b 127.0.0.1:5000 --timeout 120 wsgi:app`)
  dan Nginx dengan [deployment/nginx/reimburse.conf](deployment/nginx/reimburse.conf).
- File struk disimpan di `backend/storage/receipts` (di luar folder publik) dan hanya bisa diakses
  lewat API yang memeriksa hak akses.
