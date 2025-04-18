from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
import base64
from dotenv import load_dotenv
from supabase import create_client, Client
import openai
from typing import Dict, Any

load_dotenv()

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# テスト用にSupabase初期化をスキップ
try:
    # Supabaseクライアントの初期化
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL", ""),
        os.getenv("SUPABASE_KEY", "")
    )
except Exception as e:
    print(f"Supabase初期化エラー: {e}")
    supabase = None

# OpenAIクライアントの初期化（APIキーがない場合はスキップ）
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    openai.api_key = openai_api_key

@app.get("/")
async def root():
    return {"message": "Meal Checker API is working!"}

@app.post("/analyze")
async def analyze_meal(image: UploadFile = File(...)) -> Dict[str, Any]:
    # Supabaseが初期化されていない場合
    if supabase is None:
        return {
            "staple": 40,
            "main": 30,
            "side": 30,
            "comment": "テストモード: Supabase接続がないため、テストデータを返しています。"
        }
    
    try:
        # 画像をSupabase Storageにアップロード
        file_content = await image.read()
        file_path = f"meal_images/{image.filename}"
        
        supabase.storage.from_("meal-images").upload(
            file_path,
            file_content,
            {"content-type": "image/jpeg"}
        )
        
        # アップロードした画像のURLを取得
        image_url = supabase.storage.from_("meal-images").get_public_url(file_path)
        
        # OpenAI APIキーがない場合
        if not openai_api_key:
            return {
                "staple": 40,
                "main": 30,
                "side": 30,
                "comment": "テストモード: OpenAI APIキーがないため、テストデータを返しています。"
            }
        
        # GPT-4 Vision APIで画像分析
        response = openai.chat.completions.create(
            model="gpt-4o",  # 最新のGPT-4モデル
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """この食事写真を詳細に分析してください。

1. 写真に写っている食材をすべて特定してください。
2. 主食・主菜・副菜の割合を以下の形式で具体的な数値で示してください：
   - 主食：○○%
   - 主菜：○○%
   - 副菜：○○%
3. その割合の根拠となる視覚的な特徴や食材の量を説明してください。
4. 栄養バランスの観点から評価してください。
5. 改善点があれば具体的に提案してください。

なお、主食とは炭水化物を多く含む食品（米、パン、麺類など）、主菜はタンパク質源となる食品（肉、魚、豆製品など）、副菜は野菜、海藻、きのこなどのビタミン・ミネラル源となる食品を指します。

必ず上記1〜5の内容を含めて回答してください。"""
                        },
                        {
                            "type": "image_url",
                            "image_url": image_url
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        # 分析結果をパース
        analysis_text = response.choices[0].message.content
        # ここで分析結果を適切な形式にパースする処理が必要です
        # 例: 正規表現や文字列処理を使用して数値とコメントを抽出
        
        # 仮の結果を返す
        return {
            "staple": 40,
            "main": 30,
            "side": 30,
            "comment": "バランスの取れた食事です。"
        }
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return {
            "staple": 40,
            "main": 30,
            "side": 30,
            "comment": f"エラーが発生しました: {str(e)}"
        } 

@app.post("/analyze-direct")
async def analyze_meal_direct(image: UploadFile = File(...)) -> Dict[str, Any]:
    """Supabaseを使わずに直接OpenAI APIを使用して食事画像を分析するエンドポイント"""
    try:
        # OpenAI APIキーがない場合
        if not openai_api_key:
            return {
                "staple": 40,
                "main": 30,
                "side": 30,
                "comment": "テストモード: OpenAI APIキーがないため、テストデータを返しています。"
            }
        
        # 画像をbase64エンコードして直接OpenAI APIに送信
        file_content = await image.read()
        base64_image = base64.b64encode(file_content).decode('utf-8')
        
        # GPT-4 Vision APIで画像分析
        response = openai.chat.completions.create(
            model="gpt-4o",  # 最新のGPT-4モデル
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """この食事写真を詳細に分析してください。

1. 写真に写っている食材をすべて特定してください。
2. 主食・主菜・副菜の割合を以下の形式で具体的な数値で示してください：
   - 主食：○○%
   - 主菜：○○%
   - 副菜：○○%
3. その割合の根拠となる視覚的な特徴や食材の量を説明してください。
4. 栄養バランスの観点から評価してください。
5. 改善点があれば具体的に提案してください。

なお、主食とは炭水化物を多く含む食品（米、パン、麺類など）、主菜はタンパク質源となる食品（肉、魚、豆製品など）、副菜は野菜、海藻、きのこなどのビタミン・ミネラル源となる食品を指します。

必ず上記1〜5の内容を含めて回答してください。"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        # 分析結果を取得
        analysis_text = response.choices[0].message.content
        print(f"分析結果: {analysis_text}")
        
        # 実際の分析結果をそのまま返す
        return {
            "analysis": analysis_text,
            "staple": 40,  # ここは本来、分析結果から抽出した値を設定
            "main": 30,    # ここは本来、分析結果から抽出した値を設定
            "side": 30,    # ここは本来、分析結果から抽出した値を設定
            "comment": analysis_text
        }
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return {
            "staple": 40,
            "main": 30,
            "side": 30,
            "comment": f"エラーが発生しました: {str(e)}"
        } 