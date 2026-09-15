FROM python:3.11.16-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Cloud Run は PORT 環境変数でポートを渡す（既定 8080）。
# $PORT を展開させるためシェル形式で書く（JSON 配列で書くと文字列 "$PORT" のまま渡る）。
ENV PORT=8080
CMD streamlit run main.py --server.port=$PORT --server.address=0.0.0.0
