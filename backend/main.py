from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import os
import base64
from dotenv import load_dotenv
from supabase import create_client, Client
import openai
from typing import Dict, Any
from pydantic import BaseModel
import re
import requests
from io import BytesIO

load_dotenv()

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://meal-checker-frontend.vercel.app"],
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

class ImageUrlRequest(BaseModel):
    image_url: str

@app.get("/")
async def root():
    return {"message": "Meal Checker API is working!"}

@app.post("/analyze", response_model=dict)
async def analyze_image(request: ImageUrlRequest):
    try:
        # 画像URLの取得
        image_url = request.image_url
        print(f"受信したイメージURL: {image_url}")
        
        # Supabaseが初期化されていない場合
        if supabase is None:
            return {
                "comment": "テストモード: Supabase接続がないため、テストデータを返しています。"
            }
        
        try:
            # 画像URLが正しいか検証
            if not image_url.startswith('http'):
                print(f"警告: URLが不正な形式です: {image_url}")
                return {
                    "comment": "エラー: 無効な画像URLです。"
                }
            
            # OpenAI APIキーがない場合
            if not openai_api_key:
                return {
                    "comment": "テストモード: OpenAI APIキーがないため、テストデータを返しています。"
                }
            
            print(f"OpenAI APIを呼び出し中... image_url = {image_url}")
            
            try:
                # 画像をダウンロードしてbase64エンコード
                try:
                    # 画像をダウンロード
                    response = requests.get(image_url, timeout=10)
                    response.raise_for_status()  # エラーチェック
                    
                    # 画像データをBase64エンコード
                    image_data = response.content
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                    
                    print(f"画像のダウンロードとエンコードに成功しました。サイズ: {len(image_data)} bytes")
                except Exception as download_error:
                    print(f"画像のダウンロードに失敗しました: {str(download_error)}")
                    return {
                        "comment": f"エラー: 画像のダウンロードに失敗しました。{str(download_error)}"
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
                
                return {"comment": response_text}
                
            except Exception as e:
                print(f"OpenAI API呼び出しエラー: {e}")
                return {
                    "comment": f"エラー: OpenAI APIの呼び出しに失敗しました。{str(e)}"
                }
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            return {
                "comment": f"エラーが発生しました: {str(e)}"
            } 
    except Exception as e:
        print(f"エラーが発生しました: {e}")
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
        
        return {"comment": response_text}
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return {
            "comment": f"エラーが発生しました: {str(e)}"
        } 