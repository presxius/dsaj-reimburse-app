FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# WITH_OCR=1 memasang PaddleOCR + OpenCV (image jauh lebih besar).
# Tanpa OCR aplikasi tetap jalan; form diisi manual.
ARG WITH_OCR=0

WORKDIR /app

COPY requirements.txt requirements-ocr.txt ./
RUN pip install -r requirements.txt \
    && if [ "$WITH_OCR" = "1" ]; then \
         apt-get update && apt-get install -y --no-install-recommends libgomp1 libglib2.0-0 \
         && rm -rf /var/lib/apt/lists/* \
         && pip install -r requirements-ocr.txt; \
       fi

COPY . .

RUN useradd --system --uid 1000 --home /app app \
    && mkdir -p /app/storage/receipts \
    && chown -R app:app /app/storage \
    && chmod +x /app/docker-entrypoint.sh
USER app

EXPOSE 5000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
# Jumlah worker dari WEB_CONCURRENCY. Timeout panjang karena OCR berjalan sinkron.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "--access-logfile", "-", "wsgi:app"]
