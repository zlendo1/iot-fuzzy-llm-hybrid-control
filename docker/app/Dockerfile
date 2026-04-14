FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Upgrade protobuf to fix version compatibility with grpcio-reflection
RUN pip install --no-cache-dir --user protobuf==6.31.1

# Install grpcio-tools for protobuf generation
RUN pip install --no-cache-dir --user grpcio-tools==1.70.0

# Copy proto files and generate Python code
COPY protos/ ./protos/
COPY scripts/fix_protobuf_imports.py ./scripts/

RUN mkdir -p src/interfaces/rpc/generated && \
    python -m grpc_tools.protoc \
    --proto_path=./protos \
    --python_out=./src/interfaces/rpc/generated \
    --grpc_python_out=./src/interfaces/rpc/generated \
    ./protos/*.proto && \
    python scripts/fix_protobuf_imports.py

# Reinstall protobuf after grpcio-tools to fix version conflict
RUN pip install --no-cache-dir --user protobuf==6.31.1


FROM python:3.12-slim

WORKDIR /app

RUN useradd --create-home --shell /bin/bash appuser

COPY --from=builder /root/.local /home/appuser/.local

COPY src/ ./src/
COPY config/ ./config/
COPY rules/ ./rules/
COPY docker/app/entrypoint.sh /entrypoint.sh
COPY docker/app/healthcheck.py /app/docker/app/healthcheck.py

RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app && \
    chmod +x /entrypoint.sh

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

USER appuser

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "src.main"]
