"use client";

import { useState } from "react";

import { Box, Container, Flex, Heading, Text } from "@chakra-ui/react";
import ImageUploader from "@/components/ImageUploader";

interface AnalysisResult {
  staple: number;
  main: number;
  side: number;
  comment: string;
}

export default function Home() {
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [uploadedImageUrl, setUploadedImageUrl] = useState<string | null>(null);

  const handleImageUploaded = (url: string) => {
    setUploadedImageUrl(url);
  };

  const analyzeImage = async () => {
    if (!uploadedImageUrl) {
      alert("画像をアップロードしてください");
      return;
    }

    setAnalyzing(true);
    setResult(null);

    try {
      const response = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ image_url: uploadedImageUrl }),
      });

      if (!response.ok) {
        throw new Error("分析に失敗しました");
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Error:", error);
      alert("分析に失敗しました");
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

        {uploadedImageUrl && (
          <Box mb={4}>
            <Text fontWeight="bold" mb={2}>
              アップロードされた画像:
            </Text>
            <Box
              as="button"
              onClick={analyzeImage}
              aria-disabled={analyzing}
              _disabled={{ bg: "gray.300", cursor: "not-allowed" }}
              borderWidth="1px"
              borderRadius="lg"
              borderColor="gray.200"
              p={2}
              w="full"
              textAlign="center"
              bg={analyzing ? "gray.300" : "teal.500"}
              color="white"
              _hover={{ bg: analyzing ? "gray.300" : "teal.600" }}
              cursor={analyzing ? "not-allowed" : "pointer"}
            >
              {analyzing ? "分析中..." : "分析する"}
            </Box>
          </Box>
        )}

        {result && (
          <Box borderWidth={1} borderRadius="lg" p={6} bg="gray.50">
            <Heading as="h2" size="md" mb={4}>
              分析結果
            </Heading>
            <Flex justify="space-between" mb={4}>
              <Box
                textAlign="center"
                p={2}
                bg="orange.100"
                borderRadius="md"
                flex={1}
                mx={1}
              >
                <Text fontWeight="bold">主食</Text>
                <Text fontSize="xl">{result.staple}%</Text>
              </Box>
              <Box
                textAlign="center"
                p={2}
                bg="red.100"
                borderRadius="md"
                flex={1}
                mx={1}
              >
                <Text fontWeight="bold">主菜</Text>
                <Text fontSize="xl">{result.main}%</Text>
              </Box>
              <Box
                textAlign="center"
                p={2}
                bg="green.100"
                borderRadius="md"
                flex={1}
                mx={1}
              >
                <Text fontWeight="bold">副菜</Text>
                <Text fontSize="xl">{result.side}%</Text>
              </Box>
            </Flex>
            <Box>
              <Text fontWeight="bold">コメント:</Text>
              <Text>{result.comment}</Text>
            </Box>
          </Box>
        )}
      </Box>
    </Container>
  );
}
