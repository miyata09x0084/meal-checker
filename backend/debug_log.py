"""
Supabase接続のデバッグ用スクリプト
"""
import os
import requests
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# Supabase接続情報
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Supabase APIヘッダー
supabase_headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"  # 挿入したデータを返す
}

def debug_supabase_connection():
    """Supabaseへの接続をテスト"""
    print("="*60)
    print("🔍 Supabase接続診断")
    print("="*60)
    
    # 接続情報表示（一部マスク）
    print(f"URL: {SUPABASE_URL}")
    print(f"API Key: {SUPABASE_KEY[:5]}...{SUPABASE_KEY[-5:] if SUPABASE_KEY else ''}")
    
    try:
        # テーブル一覧取得テスト
        print("\n📋 テーブル一覧取得テスト")
        tables_url = f"{SUPABASE_URL}/rest/v1/information_schema/tables?select=table_name&table_schema=eq.public"
        response = requests.get(tables_url, headers=supabase_headers)
        
        print(f"ステータス: {response.status_code}")
        if response.status_code == 200:
            tables = response.json()
            table_names = [table['table_name'] for table in tables]
            print(f"テーブル一覧: {table_names}")
            
            if 'meal_images' in table_names:
                print("✅ meal_imagesテーブルが存在します")
            else:
                print("❌ meal_imagesテーブルが見つかりません")
        else:
            print(f"❌ テーブル一覧取得エラー: {response.text}")
        
        # テストデータ作成
        print("\n📝 テストデータ作成")
        test_id = str(uuid.uuid4())
        test_data = {
            "id": test_id,
            "filename": "debug_test.jpg",
            "public_url": "https://debug-test-image-url.example.com/debug_test.jpg",
            "analysis_result": "デバッグ用テストデータです",
            "created_at": datetime.now().isoformat()
        }
        print(f"テストデータID: {test_id}")
        
        # データ挿入テスト
        print("\n💾 データ挿入テスト")
        insert_url = f"{SUPABASE_URL}/rest/v1/meal_images"
        print(f"挿入URL: {insert_url}")
        print(f"ヘッダー: {json.dumps(supabase_headers)}")
        
        insert_response = requests.post(
            insert_url,
            headers=supabase_headers,
            json=test_data
        )
        
        print(f"挿入レスポンスステータス: {insert_response.status_code}")
        print(f"挿入レスポンス: {insert_response.text}")
        
        if insert_response.status_code in [200, 201, 204]:
            print("✅ データ挿入成功!")
            
            # データ確認テスト
            print("\n🔎 挿入データ確認テスト")
            get_url = f"{SUPABASE_URL}/rest/v1/meal_images?id=eq.{test_id}"
            get_response = requests.get(get_url, headers=supabase_headers)
            
            print(f"確認レスポンスステータス: {get_response.status_code}")
            if get_response.status_code == 200:
                data = get_response.json()
                if data:
                    print("✅ 挿入データの取得に成功!")
                    print(f"取得データ: {json.dumps(data, indent=2)}")
                else:
                    print("❌ データは挿入されましたが、取得できませんでした")
            else:
                print(f"❌ データ確認エラー: {get_response.text}")
        else:
            print(f"❌ データ挿入エラー: {insert_response.text}")
    
    except Exception as e:
        print(f"❌ 例外が発生しました: {str(e)}")
    
    print("\n="*60)
    print("🏁 診断完了")
    print("="*60)

if __name__ == "__main__":
    debug_supabase_connection() 