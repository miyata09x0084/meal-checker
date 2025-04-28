# Meal Checker Backend

食事バランス診断アプリのバックエンド API です。

## セットアップ手順

### 1. 環境変数の設定

`.env`ファイルに以下の環境変数を設定してください：

```
# Supabase設定
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# OpenAI設定
OPENAI_API_KEY=your_openai_api_key

# バックエンド設定
BACKEND_PORT=8000
```

### 2. Supabase でテーブルの作成

Supabase ダッシュボードの「SQL Editor」で以下の SQL を実行し、必要なテーブルを作成してください：

```sql
-- meal_images テーブルの作成
CREATE TABLE IF NOT EXISTS meal_images (
    id UUID PRIMARY KEY,
    filename TEXT NOT NULL,
    public_url TEXT NOT NULL,
    analysis_result TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id UUID
);

-- インデックスの作成
CREATE INDEX IF NOT EXISTS meal_images_user_id_idx ON meal_images(user_id);
CREATE INDEX IF NOT EXISTS meal_images_created_at_idx ON meal_images(created_at DESC);

-- RLS (Row Level Security) ポリシーの設定
ALTER TABLE meal_images ENABLE ROW LEVEL SECURITY;

-- 匿名ユーザーの挿入を許可
CREATE POLICY "匿名ユーザーの挿入を許可" ON meal_images
    FOR INSERT TO anon
    WITH CHECK (true);

-- 認証済みユーザーは自分のデータのみ表示
CREATE POLICY "認証済みユーザーは自分のデータのみ表示" ON meal_images
    FOR SELECT TO authenticated
    USING (user_id = auth.uid() OR user_id IS NULL);

-- 管理者はすべてのデータにアクセス可能
CREATE POLICY "管理者はすべてのデータにアクセス可能" ON meal_images
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);
```

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 4. サーバーの起動

```bash
uvicorn main:app --reload --port 8000
```

## API エンドポイント

### 1. `/analyze` (POST)

公開 URL の画像を分析します。

**リクエストボディ**:

```json
{
  "image_url": "https://example.com/image.jpg"
}
```

**レスポンス**:

```json
{
  "comment": "分析結果のテキスト"
}
```

### 2. `/analyze-direct` (POST)

直接アップロードされた画像を分析します。

**リクエスト**:
`multipart/form-data`形式で画像ファイルをアップロード

**レスポンス**:

```json
{
  "comment": "分析結果のテキスト"
}
```

## データベース

### meal_images テーブル

食事画像のメタデータと分析結果を保存するテーブルです。

- `id`: UUID (主キー)
- `filename`: テキスト (ファイル名)
- `public_url`: テキスト (公開 URL)
- `analysis_result`: テキスト (AI 分析結果)
- `created_at`: タイムスタンプ (作成日時)
- `user_id`: UUID (ユーザー ID、オプション)

## デプロイ

```bash
./deploy.sh
```
