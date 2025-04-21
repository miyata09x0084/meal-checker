import { createClient } from "@supabase/supabase-js";

// Supabase URL と匿名キーを取得
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_KEY || "";

if (!supabaseUrl || !supabaseAnonKey) {
  console.error("Supabaseの環境変数が設定されていません");
}

// 通常の匿名キーでクライアントを初期化
export const supabase = createClient(supabaseUrl, supabaseAnonKey);
