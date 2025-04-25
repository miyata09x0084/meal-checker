-- =============================================
-- Supabaseデバッグ用SQL
-- =============================================

-- テーブルの存在確認
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public'
    AND table_name = 'meal_images'
);

-- テーブル構造の確認
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'meal_images';

-- 既存レコードの確認
SELECT * FROM meal_images 
ORDER BY created_at DESC 
LIMIT 5;

-- RLSポリシーの確認
SELECT * FROM pg_policies 
WHERE tablename = 'meal_images';

-- =============================================
-- 問題修正用SQL
-- =============================================

-- 1. RLSポリシーを一時的に無効化（テストのみ）
ALTER TABLE meal_images DISABLE ROW LEVEL SECURITY;

-- 2. 匿名ユーザーのINSERT権限を修正
DROP POLICY IF EXISTS "匿名ユーザーの挿入を許可" ON meal_images;
CREATE POLICY "匿名ユーザーの全アクセスを許可" ON meal_images
    FOR ALL TO anon
    USING (true)
    WITH CHECK (true);

-- 3. サービスロールポリシーを確認・修正
DROP POLICY IF EXISTS "管理者はすべてのデータにアクセス可能" ON meal_images;
CREATE POLICY "管理者はすべてのデータにアクセス可能" ON meal_images
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

-- 4. テストデータ挿入
INSERT INTO meal_images (id, filename, public_url, analysis_result, created_at)
VALUES (
    gen_random_uuid(), 
    'test_sql_fix.jpg', 
    'https://example.com/test_sql_fix.jpg', 
    'SQLから直接挿入したテストデータ', 
    now()
);

-- 挿入確認
SELECT * FROM meal_images 
WHERE filename = 'test_sql_fix.jpg'; 