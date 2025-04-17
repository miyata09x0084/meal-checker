# Meal Checker

食事の写真をアップロードすると、GPT-4 Vision API を使って「主食・主菜・副菜」のバランス診断を行うアプリケーションです。

## 機能

- 食事の写真をアップロード
- Supabase Storage への画像保存
- GPT-4 Vision API によるバランス診断
- 診断結果の表示（主食・主菜・副菜の比率とコメント）

## 技術スタック

- フロントエンド: Next.js + Chakra UI + TypeScript
- バックエンド: Python + FastAPI
- AI 連携: OpenAI GPT-4 Vision API
- ストレージ: Supabase Storage

## セットアップ

1. リポジトリをクローン

```bash
git clone [repository-url]
cd meal-checker
```

2. 環境変数の設定

```bash
cp .env.example .env
```

`.env`ファイルに必要な環境変数を設定してください。

3. フロントエンドのセットアップ

```bash
cd frontend
npm install
npm run dev
```

4. バックエンドのセットアップ

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windowsの場合は `venv\Scripts\activate`
pip install -r requirements.txt
uvicorn main:app --reload
```

## 使用方法

1. フロントエンド（http://localhost:3000）にアクセス
2. 「画像を選択」ボタンをクリックして食事の写真をアップロード
3. 「バランスを診断」ボタンをクリック
4. 診断結果を確認

## 注意事項

- このアプリケーションは開発環境用の設定になっています
- 本番環境では適切なセキュリティ設定が必要です
- OpenAI API の利用には課金が発生します
