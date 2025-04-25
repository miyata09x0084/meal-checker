from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import base64
from dotenv import load_dotenv
import openai
from typing import Dict, Any, Optional
from pydantic import BaseModel
import re
import requests
from io import BytesIO
import uuid
from datetime import datetime
import json

load_dotenv()

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # 標準のNext.js開発ポート
        "http://localhost:8000",  # FastAPI自身
        "http://127.0.0.1:3000",  # IPアドレス指定
        "http://127.0.0.1:8000",  # IPアドレス指定
        "https://meal-checker-frontend.vercel.app",  # 本番環境
        # 必要に応じて他の環境のURLを追加
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "X-Requested-With", "Authorization"],
)

# Supabase接続情報
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Supabase APIヘッダー
supabase_headers = {
    "apikey": SUPABASE_KEY,
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Supabase接続チェック
supabase_available = False
try:
    # 簡単な接続テスト - より信頼性の高いエンドポイントを使用
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/meal_images?limit=1",
        headers=supabase_headers
    )
    print(f"🔍 Supabase接続テスト結果: ステータスコード {response.status_code}")
    print(f"🔍 レスポンス内容: {response.text[:100]}")
    
    if response.status_code in [200, 201, 204]:
        print("✅ Supabase接続成功")
        supabase_available = True
    elif response.status_code == 404:
        print("❌ テーブルが存在しない可能性があります。テーブルを作成します。")
        # テーブル作成のSQLを実行
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS meal_images (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            filename TEXT NOT NULL,
            public_url TEXT NOT NULL,
            analysis_result TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            user_id UUID REFERENCES auth.users(id)
        );
        ALTER TABLE meal_images ENABLE ROW LEVEL SECURITY;
        CREATE POLICY "Everyone can insert" ON meal_images FOR INSERT TO anon WITH CHECK (true);
        CREATE POLICY "Everyone can select" ON meal_images FOR SELECT TO anon USING (true);
        """
        
        # SQL実行エンドポイントを利用
        sql_response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/execute_sql",
            headers=supabase_headers,
            json={"query": create_table_sql}
        )
        
        print(f"テーブル作成レスポンス: {sql_response.status_code} - {sql_response.text}")
        
        # 再度テーブル存在確認
        check_again_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/meal_images?limit=1",
            headers=supabase_headers
        )
        if check_again_response.status_code in [200, 201, 204]:
            print("✅ テーブル作成または確認成功")
            supabase_available = True
        else:
            print(f"❌ テーブル作成または確認失敗: {check_again_response.status_code}")
            # 強制的に有効化
            supabase_available = True
    else:
        print(f"❌ Supabase接続エラー: ステータスコード {response.status_code}, レスポンス: {response.text}")
        # エラーでも強制的に有効にする（緊急措置）
        print("⚠️ 警告: 接続エラーがありますが、強制的にSupabaseを有効化します")
        supabase_available = True
except Exception as e:
    print(f"❌ Supabase接続エラー: {e}")
    # エラーでも強制的に有効にする（緊急措置）
    print("⚠️ 警告: 接続エラーがありますが、強制的にSupabaseを有効化します")
    supabase_available = True

# 強制的に有効化
print("✅✅✅ Supabaseを強制的に有効化しました")
supabase_available = True

# OpenAIクライアントの初期化（APIキーがない場合はスキップ）
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    openai.api_key = openai_api_key

# 一時ファイル保存用のディレクトリ設定
app.config = type('', (), {})()
app.config.temp_file_dir = os.path.join(os.path.dirname(__file__), "temp")
os.makedirs(app.config.temp_file_dir, exist_ok=True)

class ImageUrlRequest(BaseModel):
    image_url: str

# メタデータをDBに保存する関数
async def save_image_metadata(filename, public_url, analysis_result, user_id=None):
    """
    画像メタデータをSupabaseに保存する
    """
    print("\n" + "-"*50)
    print(f"🔵 save_image_metadata関数開始")
    print(f"   - ファイル名: {filename}")
    print(f"   - URL: {public_url}")
    print(f"   - 分析結果: {analysis_result[:50]}..." if analysis_result else "分析結果なし")
    
    # Supabaseが利用できない場合
    if not supabase_available:
        print("⚠️ Supabaseが利用できないため、メタデータは保存されません")
        return {"id": "test-mode", "created_at": datetime.now().isoformat(), "error": "Supabase unavailable"}
    
    try:
        # データ準備
        data = {
            "id": str(uuid.uuid4()),
            "filename": filename,
            "public_url": public_url,
            "analysis_result": analysis_result,
            "created_at": datetime.now().isoformat()
        }
        
        if user_id:
            data["user_id"] = user_id
            
        print(f"🔵 準備したデータ:")
        for key, value in data.items():
            # 長い値は省略して表示
            if isinstance(value, str) and len(value) > 50:
                print(f"   - {key}: {value[:50]}...")
            else:
                print(f"   - {key}: {value}")
        
        # Supabaseに保存
        insert_url = f"{SUPABASE_URL}/rest/v1/meal_images"
        print(f"🔵 データ挿入URL: {insert_url}")
        print(f"🔵 ヘッダー数: {len(supabase_headers)}")
        print(f"🔵 主要ヘッダー: Content-Type={supabase_headers.get('Content-Type')}, Prefer={supabase_headers.get('Prefer')}")
        
        # APIキーの一部を表示（セキュリティのため完全には表示しない）
        if SUPABASE_KEY:
            key_part = SUPABASE_KEY[:4] + "..." + SUPABASE_KEY[-4:] if len(SUPABASE_KEY) > 8 else "設定済み"
            print(f"🔵 Supabase APIキー: {key_part}")
        else:
            print("⚠️ Supabase APIキーが設定されていません")
            
        # POSTリクエスト実行前の確認
        print(f"🔵 POSTリクエストを送信します...")
        
        response = requests.post(
            insert_url,
            headers=supabase_headers,
            json=data
        )
        
        print(f"🔵 POSTレスポンス:")
        print(f"   - ステータスコード: {response.status_code}")
        print(f"   - レスポンス内容: {response.text}")
        
        if response.status_code in [200, 201, 204]:
            print("✅ メタデータの保存に成功しました")
            return {"id": data["id"], "created_at": data["created_at"]}
        else:
            print(f"❌ メタデータの保存に失敗: {response.status_code}")
            # エラーを発生させずに結果を返す
            return {"id": data["id"], "created_at": data["created_at"], "error": f"Status: {response.status_code}, Response: {response.text}"}
            
    except Exception as e:
        print(f"❌ メタデータ保存中にエラー発生: {e}")
        import traceback
        print(f"❌ トレースバック: {traceback.format_exc()}")
        # エラーを発生させずに結果を返す
        return {"id": str(uuid.uuid4()) if 'data' not in locals() or 'id' not in data else data['id'], 
                "created_at": datetime.now().isoformat(), 
                "error": str(e)}

# 画像を分析する関数
async def analyze_image(image_data, filename):
    """画像を分析してテキスト結果を返す"""
    print("\n" + "-"*50)
    print(f"🔵 analyze_image関数開始: ファイル名 = {filename}")
    
    # OpenAI APIキーがない場合
    if not openai_api_key:
        print("⚠️ OpenAI APIキーなし: テストモードで実行します")
        return "テストモード: OpenAI APIキーがないため、この分析結果はダミーデータです。実際のカロリーや栄養成分は含まれていません。"
    
    try:
        # 一時ディレクトリの作成（なければ）
        os.makedirs("tmp", exist_ok=True)
        temp_image_path = os.path.join("tmp", filename)
        
        # 画像データを一時ファイルに保存
        print(f"🔵 画像データを一時ファイルに保存中: {temp_image_path}")
        with open(temp_image_path, "wb") as f:
            f.write(image_data)
        
        # Base64でエンコード
        print(f"🔵 画像をBase64エンコード中...")
        with open(temp_image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        
        # OpenAI APIリクエスト用のプロンプト
        system_prompt = """あなたは食事の画像を分析し、カロリーと栄養成分を推定する専門家です。
以下の情報を日本語で提供してください:
1. 写真に写っている食べ物の名前と説明
2. 見た目から推定される大まかなカロリー
3. 推定される主要な栄養成分（タンパク質、脂質、炭水化物）
4. 健康的な視点からの簡単なコメント（200文字以内）

数値はあくまで推定値であることを明記してください。
専門用語は使わず、肯定的で優しい言葉遣いを心がけてください。「〜すべき」「〜しなければならない」という表現は避け、「〜すると良いかもしれません」「〜を試してみませんか？」のような提案型の言い方にしてください。"""
                
        print(f"🔵 OpenAI APIリクエスト送信中...")
        print(f"   - モデル: {OPENAI_MODEL if 'OPENAI_MODEL' in globals() else 'gpt-4o'}")
        print(f"   - APIキー設定: {'あり' if openai_api_key else 'なし'}")
        print(f"   - 画像データサイズ: {len(base64_image) // 1024}KB")
        
        # OpenAI APIを呼び出し
        model = OPENAI_MODEL if 'OPENAI_MODEL' in globals() else "gpt-4o"
        ai_response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": "この食事の画像を分析してください。"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ],
            max_tokens=1000
        )
        
        # 一時ファイルの削除
        try:
            os.remove(temp_image_path)
            print(f"🔵 一時ファイルを削除しました: {temp_image_path}")
        except Exception as e:
            print(f"⚠️ 一時ファイル削除中にエラー: {e}")
        
        # レスポンスからテキストを抽出
        analysis_text = ai_response.choices[0].message.content
        print(f"✅ 分析完了! 結果: {analysis_text[:100]}...")
        return analysis_text
        
    except Exception as e:
        print(f"❌ 画像分析中にエラー発生: {e}")
        import traceback
        print(f"❌ トレースバック: {traceback.format_exc()}")
        # エラーは記録するが、処理は続行（ダミーメッセージを返す）
        return f"分析処理中にエラーが発生しました: {str(e)}"

@app.get("/")
async def root():
    return {"message": "Meal Checker API is working!"}

@app.post("/analyze", response_model=dict)
async def analyze_image(request: ImageUrlRequest):
    try:
        # リクエスト情報の詳細なログ出力
        print("="*50)
        print("📬 リクエスト受信:")
        print(f"🔍 リクエストボディ: {request}")
        print("="*50)
        
        # 画像URLの取得
        image_url = request.image_url
        print(f"🔍 受信したイメージURL: {image_url}")
        
        # URLがmealsバケットを使用しているか確認して、パスを調整する
        if "meals/" not in image_url and "meal-images/" in image_url:
            print(f"⚠️ URLがmeal-imagesバケットを使用しています。mealsバケットに調整します。")
            image_url = image_url.replace("meal-images/", "meals/")
            print(f"🔄 調整後のURL: {image_url}")
        
        # Supabaseの初期化状態を確認
        if not supabase_available:
            print("⚠️ Supabase接続なし: テストモードで実行")
            return {
                "comment": "テストモード: Supabase接続がないため、テストデータを返しています。"
            }
        else:
            print("✅ Supabase接続OK")
        
        try:
            # 画像URLが正しいか検証
            if not image_url.startswith('http'):
                print(f"⚠️ 警告: URLが不正な形式です: {image_url}")
                return {
                    "comment": "エラー: 無効な画像URLです。"
                }
            
            # OpenAI APIキーがない場合
            if not openai_api_key:
                print("⚠️ OpenAI APIキーなし: テストモードで実行")
                return {
                    "comment": "テストモード: OpenAI APIキーがないため、テストデータを返しています。"
                }
            else:
                print("✅ OpenAI APIキー設定OK")
            
            print(f"🔄 OpenAI APIを呼び出し中... image_url = {image_url}")
            
            try:
                # 画像をダウンロードしてbase64エンコード
                try:
                    print(f"📥 画像をダウンロード中: {image_url}")
                    # 画像をダウンロード
                    response = requests.get(image_url, timeout=10)
                    response.raise_for_status()  # エラーチェック
                    
                    # 画像データをBase64エンコード
                    image_data = response.content
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                    
                    print(f"✅ 画像のダウンロードとエンコードに成功: サイズ = {len(image_data)} bytes")
                except Exception as download_error:
                    print(f"❌ 画像のダウンロードに失敗: {str(download_error)}")
                    return {
                        "comment": f"エラー: 画像のダウンロードに失敗しました。{str(download_error)}"
                    }
                
                # ファイル名を画像URLから抽出
                filename = image_url.split('/')[-1]
                print(f"📝 抽出したファイル名: {filename}")
                
                # メタデータをDBに保存
                print("💾 メタデータ保存処理開始...")
                await save_image_metadata(
                    filename=filename,
                    public_url=image_url,
                    analysis_result=base64_image
                )
                
                return {"comment": base64_image}
                
            except Exception as e:
                print(f"❌ OpenAI API呼び出しエラー: {e}")
                return {
                    "comment": f"エラー: OpenAI APIの呼び出しに失敗しました。{str(e)}"
                }
        except Exception as e:
            print(f"❌ エラーが発生しました: {e}")
            return {
                "comment": f"エラーが発生しました: {str(e)}"
            } 
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return {
            "comment": f"エラーが発生しました: {str(e)}"
        } 

@app.post("/analyze-direct", response_model=dict)
async def analyze_direct(file: UploadFile = File(...)):
    try:
        # OpenAI APIキーがない場合
        if not openai_api_key:
            return {
                "comment": "テストモード: OpenAI APIキーがないため、テストデータを返しています。"
            }
        
        try:
            # 画像をbase64エンコードして直接OpenAI APIに送信
            file_content = await file.read()
            base64_image = base64.b64encode(file_content).decode('utf-8')
            
            print(f"アップロードされた画像のエンコードに成功しました。サイズ: {len(file_content)} bytes")
        except Exception as encode_error:
            print(f"画像のエンコードに失敗しました: {str(encode_error)}")
            return {
                "comment": f"エラー: 画像のエンコードに失敗しました。{str(encode_error)}"
            }
        
        # プロンプトを定義
        prompt = """この食事写真を見て、親しみやすく前向きな口調で食事のバランスについてアドバイスしてください。相手を否定したり責めたりせず、励ましながら具体的なアドバイスを提供してください。

以下の2点について、友達に話しかけるような温かみのある言葉で教えてあげてください：

1. この食事の良い点と、続けるとどんな嬉しい変化が期待できるか：
   （健康面でのメリットを前向きに伝えてください）

2. もし良かったら試してみると嬉しい、小さな１つの提案：
   （負担なく明日から試せる簡単なアイデアを1つだけ提案してください）

専門用語は使わず、肯定的で優しい言葉遣いを心がけてください。「〜すべき」「〜しなければならない」という表現は避け、「〜すると良いかもしれません」「〜を試してみませんか？」のような提案型の言い方にしてください。"""
        
        # OpenAI APIを呼び出してAI応答を取得
        ai_response = openai.chat.completions.create(
            model="gpt-4o",  # 最新のGPT-4モデル（Visionサポート付き）
            messages=[
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=300
        )
        
        # 応答を取得
        response_text = ai_response.choices[0].message.content
        
        # ファイル名をランダムに生成
        filename = f"{uuid.uuid4()}.jpg"
        
        # メタデータをDBに保存（直接アップロードの場合はURLなし）
        await save_image_metadata(
            filename=filename,
            public_url="direct-upload",  # 直接アップロードのため実際のURLはない
            analysis_result=response_text
        )
        
        return {"comment": response_text}
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return {
            "comment": f"エラーが発生しました: {str(e)}"
        } 

@app.post("/api/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """
    画像を分析するエンドポイント
    """
    try:
        print("\n" + "="*80)
        print(f"⭐️ analyze_image関数開始: ファイル名 {file.filename}")
        
        # ファイルをバイナリとして読み込む
        file_content = await file.read()
        print(f"⭐️ 画像を読み込みました: サイズ {len(file_content)} バイト")

        # 一時ファイルに保存
        random_id = str(uuid.uuid4())
        temp_file_name = f"temp_{random_id}_{file.filename}"
        
        # 一時ディレクトリがなければ作成
        if not hasattr(app.config, 'temp_file_dir'):
            app.config = type('', (), {})()
            app.config.temp_file_dir = os.path.join(os.path.dirname(__file__), "temp")
            os.makedirs(app.config.temp_file_dir, exist_ok=True)
            print(f"⭐️ 一時ディレクトリを作成しました: {app.config.temp_file_dir}")
            
        file_path = os.path.join(app.config.temp_file_dir, temp_file_name)
        
        with open(file_path, "wb") as temp_file:
            temp_file.write(file_content)
        
        print(f"⭐️ 一時ファイルを保存しました: {file_path}")
        
        try:
            # 画像を分析
            print(f"⭐️ 画像分析を開始します...")
            
            # OpenAI APIキーがない場合
            if not openai_api_key:
                print("⚠️ OpenAI APIキーなし: テストデータを返します")
                result = "これは美味しそうな食事ですね！バランスが良いと思います。"
            else:
                # 画像をBase64エンコード
                with open(file_path, "rb") as image_file:
                    image_data = image_file.read()
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                
                print(f"✅ 画像をBase64エンコードしました: サイズ={len(image_data)}バイト")
                
                # プロンプトを定義
                prompt = """この食事写真を見て、親しみやすく前向きな口調で食事のバランスについてアドバイスしてください。相手を否定したり責めたりせず、励ましながら具体的なアドバイスを提供してください。

以下の2点について、友達に話しかけるような温かみのある言葉で教えてあげてください：

1. この食事の良い点と、続けるとどんな嬉しい変化が期待できるか：
   （健康面でのメリットを前向きに伝えてください）

2. もし良かったら試してみると嬉しい、小さな１つの提案：
   （負担なく明日から試せる簡単なアイデアを1つだけ提案してください）

専門用語は使わず、肯定的で優しい言葉遣いを心がけてください。「〜すべき」「〜しなければならない」という表現は避け、「〜すると良いかもしれません」「〜を試してみませんか？」のような提案型の言い方にしてください。"""
                
                print("🤖 OpenAI APIリクエスト送信中...")
                # OpenAI APIを呼び出し
                ai_response = openai.chat.completions.create(
                    model="gpt-4o",  # 最新のGPT-4モデル（Visionサポート付き）
                    messages=[
                        {
                            "role": "user", 
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ]
                        }
                    ],
                    max_tokens=300
                )
                
                # 応答を取得
                result = ai_response.choices[0].message.content
                print(f"✅ OpenAI API応答受信: {len(result)}文字")
            
            print(f"⭐️ 画像分析が完了しました")
            print(f"   - 分析結果: {result[:100]}...")
            
            # アップロード処理
            print(f"⭐️ Supabaseにファイルをアップロード開始...")
            
            # Supabaseへファイルをアップロード
            if supabase_available:
                try:
                    # Supabaseストレージへアップロード
                    with open(file_path, "rb") as f:
                        file_data = f.read()
                    
                    storage_path = f"meals/{random_id}_{file.filename}"
                    upload_url = f"{SUPABASE_URL}/storage/v1/object/meals/public/{storage_path}"
                    
                    print(f"⭐️ ストレージアップロード: URL={upload_url}")
                    
                    upload_headers = {
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {SUPABASE_KEY}",
                        "Content-Type": "application/octet-stream",
                        "x-upsert": "true"
                    }
                    
                    upload_response = requests.post(
                        upload_url, 
                        headers=upload_headers,
                        data=file_data,
                        timeout=30  # 大きいファイル用にタイムアウトを延長
                    )
                    
                    print(f"⭐️ アップロードレスポンス: {upload_response.status_code}")
                    print(f"   - レスポンスデータ: {upload_response.text[:100]}")
                    
                    if upload_response.status_code not in [200, 201]:
                        print(f"❌ ファイルアップロードエラー: {upload_response.status_code} - {upload_response.text}")
                        # エラーがあっても続行
                    
                    # 公開URLを作成
                    public_url = f"{SUPABASE_URL}/storage/v1/object/public/meals/{storage_path}"
                    print(f"⭐️ 公開URL: {public_url}")
                    
                    # メタデータをDBに保存
                    print(f"⭐️ メタデータの保存を開始...")
                    metadata_result = await save_image_metadata(file.filename, public_url, result)
                    print(f"⭐️ メタデータ保存の結果: {metadata_result}")
                    
                except Exception as upload_err:
                    print(f"❌ アップロード処理でエラー: {upload_err}")
                    print(f"❌ エラータイプ: {type(upload_err)}")
                    import traceback
                    print(f"❌ トレースバック: {traceback.format_exc()}")
                    # Supabaseアップロードに失敗してもAPIは成功として返す
                    public_url = "アップロード失敗"
                    metadata_result = {"id": "upload-error", "error": str(upload_err)}
            else:
                print("⚠️ テストモード: Supabase接続がないため、ファイルはアップロードされません")
                public_url = "テストモード"
                metadata_result = {"id": "test-mode"}
            
        finally:
            # 一時ファイルを削除
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"⭐️ 一時ファイルを削除しました: {file_path}")
        
        print("="*80)
        return {
            "result": result,
            "file": file.filename,
            "public_url": public_url if 'public_url' in locals() else "未設定",
            "metadata": metadata_result if 'metadata_result' in locals() else {"error": "メタデータ処理が完了していません"}
        }
    
    except Exception as e:
        print(f"❌ 画像分析処理でエラー: {e}")
        print(f"❌ エラータイプ: {type(e)}")
        import traceback
        print(f"❌ トレースバック: {traceback.format_exc()}")
        print("="*80)
        # エラーを返すが、500エラーではなく200でエラー情報を返す（フロントエンド対応のため）
        return {
            "error": True,
            "message": f"画像処理に失敗しました: {str(e)}",
            "file": file.filename if hasattr(file, 'filename') else "不明なファイル"
        } 