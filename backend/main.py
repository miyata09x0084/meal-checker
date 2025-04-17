from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
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
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "この食事写真を分析し、主食・主菜・副菜の割合を数値で教えてください。また、バランスに関するコメントもお願いします。"
                    },
                    {
                        "type": "image_url",
                        "image_url": image_url
                    }
                ]
            }
        ],
        max_tokens=300
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