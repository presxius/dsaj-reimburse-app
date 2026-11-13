#!/bin/sh
# Backup database PostgreSQL + file struk (volume "receipts"), lalu hapus backup lama.
#
# Jalankan sebagai user yang punya akses docker (mis. root lewat cron):
#   sudo /opt/apps/dsaj-reimburse-app/deployment/backup.sh
#
# Variabel opsional:
#   BACKUP_DIR  folder tujuan (default /var/backups/reimburse)
#   KEEP_DAYS   lama backup disimpan dalam hari (default 14)
#
# Hasil: db-<waktu>.dump (format custom pg_dump) dan receipts-<waktu>.tar.gz.
# Cara restore ada di README.md bagian "Backup & restore".
set -eu

BACKUP_DIR=${BACKUP_DIR:-/var/backups/reimburse}
KEEP_DAYS=${KEEP_DAYS:-14}

# Jalankan dari root repo agar docker compose memakai docker-compose.yml dan .env yang benar.
cd "$(dirname "$0")/.."

stamp=$(date +%Y%m%d-%H%M%S)
db_file="$BACKUP_DIR/db-$stamp.dump"
files_file="$BACKUP_DIR/receipts-$stamp.tar.gz"

umask 077  # backup berisi data pribadi karyawan; hanya pemilik yang boleh membaca
mkdir -p "$BACKUP_DIR"
# File setengah jadi (.tmp) dihapus bila ada langkah yang gagal.
trap 'rm -f "$db_file.tmp" "$files_file.tmp"' EXIT

echo "[$(date '+%F %T')] Backup database..."
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$db_file.tmp"
# Pastikan dump bisa dibaca pg_restore sebelum dianggap berhasil.
docker compose exec -T db pg_restore --list < "$db_file.tmp" > /dev/null
mv "$db_file.tmp" "$db_file"

echo "[$(date '+%F %T')] Backup file struk..."
docker compose exec -T backend tar -C /app/storage -czf - receipts > "$files_file.tmp"
gzip -t "$files_file.tmp"
mv "$files_file.tmp" "$files_file"

find "$BACKUP_DIR" -maxdepth 1 -type f \( -name 'db-*.dump' -o -name 'receipts-*.tar.gz' \) \
    -mtime +"$KEEP_DAYS" -delete

echo "[$(date '+%F %T')] Selesai: $(du -h "$db_file" | cut -f1) database, $(du -h "$files_file" | cut -f1) struk -> $BACKUP_DIR"
