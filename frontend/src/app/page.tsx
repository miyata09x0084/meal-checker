"use client";

import { useState } from "react";

import {
  Box,
  Container,
  Flex,
  Heading,
  Text,
  Spinner,
  Center,
} from "@chakra-ui/react";
import ImageUploader from "@/components/ImageUploader";

interface AnalysisResult {
  comment: string;
}

export default function Home() {
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [uploadedImageUrl, setUploadedImageUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

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
      const response = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ image_url: urlToAnalyze }),
      });

      if (!response.ok) {
        throw new Error(
          `分析に失敗しました: ${response.status} ${response.statusText}`
        );
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Error:", error);
      setError(error instanceof Error ? error.message : "分析に失敗しました");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <Container maxW="container.md" py={8}>
      <Box>
        <Heading as="h1" size="xl" textAlign="center" mb={8}>
          食事バランスチェッカー
        </Heading>

        <Box mb={6}>
          <Text mb={4}>
            食事の写真をアップロードして、栄養バランスを分析します
          </Text>
          <ImageUploader onImageUploaded={handleImageUploaded} />
        </Box>

        {error && (
          <Box mt={2} p={2} bg="red.100" borderRadius="md" mb={4}>
            <Text color="red.600" fontSize="sm">
              エラー: {error}
            </Text>
          </Box>
        )}

        {analyzing && (
          <Center my={8}>
            <Flex direction="column" align="center">
              <Spinner size="xl" color="blue.500" />
              <Text mt={4}>AIが食事のバランスを分析しています...</Text>
            </Flex>
          </Center>
        )}

        {result && (
          <Box borderWidth={1} borderRadius="md" p={5} bg="white">
            <Heading as="h2" size="md" mb={4}>
              実用的なアドバイス
            </Heading>
            <Box
              p={4}
              bg="gray.50"
              borderRadius="md"
              fontSize="md"
              whiteSpace="pre-wrap"
              lineHeight="1.6"
            >
              {result.comment}
            </Box>
          </Box>
        )}
      </Box>
    </Container>
  );
}
