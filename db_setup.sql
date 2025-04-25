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
-- すべてのユーザーが読み取り可能
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

-- コメント
COMMENT ON TABLE meal_images IS '食事画像のメタデータを保存するテーブル';
COMMENT ON COLUMN meal_images.id IS '一意のID';
COMMENT ON COLUMN meal_images.filename IS '画像のファイル名';
COMMENT ON COLUMN meal_images.public_url IS '公開URL';
COMMENT ON COLUMN meal_images.analysis_result IS 'GPT-4oによる分析結果';
COMMENT ON COLUMN meal_images.created_at IS '作成日時';
COMMENT ON COLUMN meal_images.user_id IS 'ユーザーID（認証済みの場合）'; 