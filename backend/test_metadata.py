import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# バックエンドのベースURL
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
print(f"接続先バックエンドURL: {BASE_URL}")

def test_analyze_with_url():
    """
    URLから画像を分析し、メタデータが保存されるかテストする
    """
    # テスト用の画像URL (Supabaseに既にアップロードされている画像)
    # 注意: これを実際にアップロード済みの画像URLに置き換えてください
    image_url = "https://kiubasephzwcgtimrrxf.supabase.co/storage/v1/object/public/meals//13ni0ntdqbpa_1745290315539.jpg"
    print(f"テスト用画像URL: {image_url}")
    
    # APIリクエストデータの作成
    request_data = {"image_url": image_url}
    print(f"リクエストデータ: {request_data}")
    
    try:
        # APIリクエスト
        print("APIリクエスト送信中...")
        response = requests.post(
            f"{BASE_URL}/analyze",
            json=request_data
        )
        
        print(f"ステータスコード: {response.status_code}")
        
        # レスポンスの検証
        if response.status_code == 200:
            result = response.json()
            print("✅ 分析結果:")
            print(result.get("comment", "コメントなし"))
            print("\n画像メタデータがSupabaseに保存されているはずです。")
        else:
            print(f"❌ エラー ({response.status_code}):")
            print(f"レスポンスボディ: {response.text}")
    except Exception as e:
        print(f"❌ 例外発生: {e}")

def main():
    print("🔍 画像分析とメタデータ保存のテスト開始...\n")
    test_analyze_with_url()
    print("\n✨ テスト完了")

if __name__ == "__main__":
    main() 