"use client";

import { useState } from "react";
import { Box, Button, Image, Text } from "@chakra-ui/react";
import { supabase } from "../utils/supabase";

type ImageUploaderProps = {
  onImageUploaded?: (url: string) => void;
};

// エラーの型定義
interface UploadError {
  message?: string;
  statusCode?: string;
  error?: string;
  [key: string]: unknown;
}

export default function ImageUploader({ onImageUploaded }: ImageUploaderProps) {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // アラート表示機能
  const showToast = (title: string, status: "success" | "error") => {
    alert(
      `${title}: ${
        status === "success" ? "成功しました" : "エラーが発生しました"
      }`
    );
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMessage(null);
    if (e.target.files?.[0]) {
      const file = e.target.files[0];
      setSelectedImage(file);

      // プレビュー用のURLを作成
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const uploadImage = async () => {
    if (!selectedImage) {
      showToast("画像を選択してください", "error");
      return;
    }

    setUploading(true);
    setErrorMessage(null);

    try {
      // ファイル名をユニークにするために現在のタイムスタンプを追加
      const fileExt = selectedImage.name.split(".").pop();
      const fileName = `${Math.random()
        .toString(36)
        .substring(2, 15)}_${Date.now()}.${fileExt}`;
      const filePath = `${fileName}`;

      console.log("Uploading to bucket: meals, file:", filePath);

      // Supabaseにアップロード
      const { data, error } = await supabase.storage
        .from("meals")
        .upload(filePath, selectedImage, {
          cacheControl: "3600",
          upsert: false,
        });

      if (error) {
        console.error("アップロードエラー詳細:", error);
        throw error;
      }

      console.log("Upload successful, data:", data);

      // 公開URLを取得
      const { data: urlData } = supabase.storage
        .from("meals")
        .getPublicUrl(filePath);

      console.log("URL data:", urlData);

      if (urlData?.publicUrl) {
        // 親コンポーネントに通知
        onImageUploaded?.(urlData.publicUrl);
        showToast("画像がアップロードされました", "success");
      } else {
        throw new Error("画像URLの取得に失敗しました");
      }
    } catch (error: unknown) {
      console.error("エラー:", error);

      // エラーメッセージの抽出
      let errorMsg = "アップロード中にエラーが発生しました";
      if (error instanceof Error) {
        errorMsg = error.message;
      } else if (typeof error === "object" && error !== null) {
        const uploadError = error as UploadError;
        errorMsg = uploadError.message || uploadError.error || errorMsg;
      }

      setErrorMessage(errorMsg);
      showToast(`画像のアップロードに失敗しました: ${errorMsg}`, "error");
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box>
      <Box>
        <Button
          variant="solid"
          colorScheme="blue"
          w="full"
          onClick={() => document.getElementById("image-upload")?.click()}
        >
          写真を選択する
        </Button>
        <input
          id="image-upload"
          type="file"
          accept="image/*"
          onChange={handleImageChange}
          style={{ display: "none" }}
        />
      </Box>

      {errorMessage && (
        <Box mt={2} p={2} bg="red.100" borderRadius="md">
          <Text color="red.600" fontSize="sm">
            エラー: {errorMessage}
          </Text>
        </Box>
      )}

      {previewUrl && (
        <Box mt={4}>
          <Text mb={2}>プレビュー</Text>
          <Image
            src={previewUrl}
            maxH="300px"
            objectFit="contain"
            borderRadius="md"
          />
          <Button
            mt={4}
            colorScheme="teal"
            onClick={uploadImage}
            disabled={uploading}
            w="full"
          >
            {uploading ? "アップロード中..." : "Supabaseにアップロード"}
          </Button>
        </Box>
      )}
    </Box>
  );
}
