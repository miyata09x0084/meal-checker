#!/bin/bash

# 変数設定
PROJECT_ID="meal-checker" # GCPプロジェクトID
SERVICE_NAME="meal-checker-api" # Cloud Runサービス名
REGION="asia-northeast1" # デプロイするリージョン
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}" # コンテナイメージ名

# ビルドとプッシュ
echo "🏗️ Dockerイメージをビルド中..."
docker build -t ${IMAGE_NAME} .

echo "🚀 Google Container Registryにプッシュ中..."
docker push ${IMAGE_NAME}

# Cloud Runへデプロイ
echo "🌐 Cloud Runにデプロイ中..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars="SUPABASE_URL=$(grep SUPABASE_URL ../.env | cut -d '=' -f2)" \
  --set-env-vars="SUPABASE_KEY=$(grep SUPABASE_KEY ../.env | cut -d '=' -f2)" \
  --set-env-vars="OPENAI_API_KEY=$(grep OPENAI_API_KEY ../.env | cut -d '=' -f2)"

echo "✅ デプロイ完了！" 