FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 環境変数の設定
ENV PORT=8000

# コンテナ起動時に実行されるコマンド
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT} 