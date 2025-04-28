"use client";

import { useState, useEffect } from "react";
import {
  Box,
  Container,
  Flex,
  Heading,
  Text,
  Spinner,
  Center,
  IconButton,
  VStack,
} from "@chakra-ui/react";
import { Sun, Moon } from "lucide-react";
import { useTheme } from "next-themes";
import ImageUploader from "@/components/ImageUploader";

interface AnalysisResult {
  comment: string;
}

export default function Home() {
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [uploadedImageUrl, setUploadedImageUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // useEffectでマウント状態を管理
  useEffect(() => {
    setMounted(true);
  }, []);

  const toggleColorMode = () => {
    setTheme(resolvedTheme === "light" ? "dark" : "light");
  };

  // マウント前はデフォルトのlightテーマを使用
  const colorMode = mounted ? resolvedTheme : "light";

  const API_URL =
    process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  const handleImageUploaded = async (url: string) => {
    setUploadedImageUrl(url);
    // 画像がアップロードされたら自動的に分析を開始
    await analyzeImage(url);
  };

  const analyzeImage = async (imageUrl?: string) => {
    const urlToAnalyze = imageUrl || uploadedImageUrl;

    if (!urlToAnalyze) {
      setError("画像をアップロードしてください");
      return;
    }

    setAnalyzing(true);
    setResult(null);
    setError(null);

    try {
      console.log(`バックエンドAPIを呼び出し中: ${API_URL}/analyze`);
      console.log("送信データ:", { image_url: urlToAnalyze });

      const response = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include", // CORS対応のためにcredentialsを追加
        body: JSON.stringify({ image_url: urlToAnalyze }),
      });

      console.log("レスポンスステータス:", response.status);

      if (!response.ok) {
        throw new Error(
          `分析に失敗しました: ${response.status} ${response.statusText}`
        );
      }

      const data = await response.json();
      console.log("分析結果:", data);
      setResult(data);
    } catch (error) {
      console.error("Error:", error);
      setError(error instanceof Error ? error.message : "分析に失敗しました");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <Container
      maxW={{ base: "100%", md: "container.md" }}
      px={{ base: 4, md: 8 }}
      py={{ base: 6, md: 10 }}
    >
      <Flex justifyContent="flex-end" mb={2}>
        {mounted && (
          <IconButton
            aria-label={`${
              colorMode === "light" ? "ダークモード" : "ライトモード"
            }に切り替え`}
            onClick={toggleColorMode}
            size="md"
            borderRadius="full"
          >
            {colorMode === "light" ? <Moon size={20} /> : <Sun size={20} />}
          </IconButton>
        )}
      </Flex>

      <VStack gap={{ base: 5, md: 8 }} align="stretch">
        <Box textAlign="center">
          <Heading
            as="h1"
            fontSize={{ base: "2xl", md: "3xl" }}
            mb={{ base: 3, md: 5 }}
          >
            食事バランスチェッカー
          </Heading>

          <Text fontSize={{ base: "sm", md: "md" }} maxW="3xl" mx="auto">
            食事の写真をアップロードして、栄養バランスを分析します
          </Text>
        </Box>

        <Box w="100%" mx="auto" mt={{ base: 2, md: 4 }}>
          <ImageUploader onImageUploaded={handleImageUploaded} />
        </Box>

        {error && (
          <Box mt={2} p={3} bg="red.100" borderRadius="lg" mb={4}>
            <Text color="red.600" fontSize={{ base: "sm", md: "md" }}>
              エラー: {error}
            </Text>
          </Box>
        )}

        {analyzing && (
          <Center my={{ base: 6, md: 10 }}>
            <Flex direction="column" align="center">
              <Spinner size="xl" color="blue.500" />
              <Text mt={4} fontSize={{ base: "sm", md: "md" }}>
                AIが食事のバランスを分析しています...
              </Text>
            </Flex>
          </Center>
        )}

        {result && (
          <Box
            borderWidth={1}
            borderRadius="lg"
            p={{ base: 4, md: 6 }}
            bg={colorMode === "dark" ? "gray.700" : "white"}
            shadow="md"
          >
            <Heading as="h2" size="md" mb={4}>
              実用的なアドバイス
            </Heading>
            <Box
              p={4}
              bg={colorMode === "dark" ? "gray.800" : "gray.50"}
              borderRadius="md"
              fontSize={{ base: "sm", md: "md" }}
              whiteSpace="pre-wrap"
              lineHeight="1.6"
            >
              {result.comment}
            </Box>
          </Box>
        )}
      </VStack>
    </Container>
  );
}
