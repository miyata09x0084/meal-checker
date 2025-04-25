"""
Supabaseへの接続とテーブル操作をテストするスクリプト
"""
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime
import requests
import json

# 環境変数の読み込み
load_dotenv()

# Supabase接続情報の表示
supabase_url = os.getenv("SUPABASE_URL", "")
supabase_key = os.getenv("SUPABASE_KEY", "")

print("=== Supabase接続情報 ===")
print(f"URL: {supabase_url}")
print(f"KEY: {supabase_key[:10]}...{supabase_key[-5:] if supabase_key else ''}")

try:
    # 直接HTTPリクエストを使ってSupabaseにアクセス
    print("\n接続試行中...")
    
    # テスト用データの作成
    test_id = str(uuid.uuid4())
    test_data = {
        "id": test_id,
        "filename": "test_image.jpg",
        "public_url": "https://example.com/test_image.jpg",
        "analysis_result": "テスト分析結果",
        "created_at": datetime.now().isoformat()
    }

    print(f"\n=== テストデータ ===")
    print(f"ID: {test_id}")
    
    # Supabaseのテーブル一覧を取得するエンドポイント
    tables_url = f"{supabase_url}/rest/v1/information_schema/tables?select=table_name&table_schema=eq.public"
    
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json"
    }
    
    # テーブル一覧の取得
    print("\n=== テーブル一覧の取得 ===")
    tables_response = requests.get(tables_url, headers=headers)
    
    if tables_response.status_code == 200:
        tables_data = tables_response.json()
        tables = [table["table_name"] for table in tables_data]
        print(f"テーブル一覧: {tables}")
        
        # meal_imagesテーブル存在確認
        if "meal_images" in tables:
            print("✅ meal_imagesテーブルが存在します")
        else:
            print("❌ meal_imagesテーブルが存在しません")
    else:
        print(f"❌ テーブル一覧取得エラー: {tables_response.status_code} - {tables_response.text}")
    
    # テストデータの挿入
    print("\n=== テストデータ挿入 ===")
    insert_url = f"{supabase_url}/rest/v1/meal_images"
    
    insert_response = requests.post(
        insert_url,
        headers=headers,
        json=test_data
    )
    
    if insert_response.status_code in [200, 201]:
        print(f"✅ データ挿入成功: {insert_response.text}")
        
        # 挿入したデータの取得
        print("\n=== 挿入データの確認 ===")
        get_url = f"{supabase_url}/rest/v1/meal_images?id=eq.{test_id}"
        
        get_response = requests.get(get_url, headers=headers)
        
        if get_response.status_code == 200:
            retrieved_data = get_response.json()
            print(f"✅ 取得データ: {retrieved_data}")
        else:
            print(f"❌ データ取得エラー: {get_response.status_code} - {get_response.text}")
    else:
        print(f"❌ 挿入エラー: {insert_response.status_code} - {insert_response.text}")

except Exception as e:
    print(f"❌ エラーが発生しました: {e}")

print("\n=== テスト完了 ===") 