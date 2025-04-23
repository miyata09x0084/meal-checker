"use client";

import { useState, useEffect } from "react";
import {
  Box,
  Button,
  Image,
  Text,
  Icon,
  VStack,
  Center,
} from "@chakra-ui/react";
import { Camera } from "lucide-react";
import { useTheme } from "next-themes";
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
  const [uploadComplete, setUploadComplete] = useState(false);
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // useEffectでマウント状態を管理
  useEffect(() => {
    setMounted(true);
  }, []);

  // マウント前はデフォルトのlightテーマを使用
  const colorMode = mounted ? resolvedTheme : "light";

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMessage(null);
    setUploadComplete(false);

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
      setErrorMessage("画像を選択してください");
      return;
    }

    setUploading(true);
    setErrorMessage(null);
    setUploadComplete(false);

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
        setUploadComplete(true);
        onImageUploaded?.(urlData.publicUrl);
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
    } finally {
      setUploading(false);
    }
  };

  return (
    <VStack gap={4} w="100%">
      <Center
        w="100%"
        borderWidth={2}
        borderStyle="dashed"
        borderRadius="xl"
        borderColor={colorMode === "dark" ? "gray.600" : "gray.300"}
        bg={colorMode === "dark" ? "gray.700" : "gray.50"}
        py={6}
        px={4}
        minH="150px"
        onClick={() => document.getElementById("image-upload")?.click()}
        cursor="pointer"
        _hover={{
          borderColor: "blue.500",
          bg: colorMode === "dark" ? "gray.600" : "gray.100",
        }}
        transition="all 0.2s"
      >
        <VStack gap={3}>
          <Icon
            as={Camera}
            w={{ base: 10, md: 12 }}
            h={{ base: 10, md: 12 }}
            color={colorMode === "dark" ? "blue.300" : "blue.500"}
          />
          <Text
            fontSize={{ base: "md", md: "lg" }}
            fontWeight="medium"
            textAlign="center"
          >
            タップして食事の写真をアップロード
          </Text>
          <Text
            fontSize="sm"
            color={colorMode === "dark" ? "gray.400" : "gray.500"}
          >
            スマホで撮影した料理の写真を選択
          </Text>
        </VStack>
        <input
          id="image-upload"
          type="file"
          accept="image/*"
          onChange={handleImageChange}
          style={{ display: "none" }}
        />
      </Center>

      {errorMessage && (
        <Box
          mt={2}
          p={3}
          bg={colorMode === "dark" ? "red.900" : "red.100"}
          borderRadius="lg"
          w="100%"
        >
          <Text
            color={colorMode === "dark" ? "red.300" : "red.600"}
            fontSize={{ base: "sm", md: "md" }}
          >
            エラー: {errorMessage}
          </Text>
        </Box>
      )}

      {previewUrl && (
        <Box mt={2} w="100%">
          <Text mb={2} fontSize={{ base: "sm", md: "md" }}>
            プレビュー
          </Text>
          <Box
            borderRadius="xl"
            overflow="hidden"
            boxShadow="md"
            maxH={{ base: "300px", md: "400px" }}
            w="100%"
          >
            <Image
              src={previewUrl}
              objectFit="contain"
              w="100%"
              h="auto"
              maxH={{ base: "300px", md: "400px" }}
            />
          </Box>

          {!uploadComplete && (
            <Button
              mt={4}
              colorScheme="teal"
              onClick={uploadImage}
              disabled={uploading}
              w="100%"
              h={{ base: "50px", md: "56px" }}
              fontSize={{ base: "md", md: "lg" }}
              borderRadius="lg"
              boxShadow="md"
              _hover={{ transform: "translateY(-2px)", boxShadow: "lg" }}
              transition="all 0.2s"
            >
              {uploading ? "アップロード中..." : "アップロードして分析"}
            </Button>
          )}

          {uploadComplete && (
            <Box
              mt={3}
              p={3}
              bg={colorMode === "dark" ? "green.900" : "green.100"}
              borderRadius="lg"
            >
              <Text
                color={colorMode === "dark" ? "green.300" : "green.600"}
                fontSize={{ base: "sm", md: "md" }}
              >
                アップロード完了！分析を開始します...
              </Text>
            </Box>
          )}
        </Box>
      )}
    </VStack>
  );
}
