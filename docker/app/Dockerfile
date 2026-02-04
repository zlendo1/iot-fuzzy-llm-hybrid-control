FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


FROM python:3.12-slim

WORKDIR /app

RUN useradd --create-home --shell /bin/bash appuser

COPY --from=builder /root/.local /home/appuser/.local

COPY src/ ./src/
COPY config/ ./config/
COPY rules/ ./rules/
COPY docker/app/entrypoint.sh /entrypoint.sh

RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app && \
    chmod +x /entrypoint.sh

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

USER appuser

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "src.main"]
