"use client";

import { useState } from "react";
import {
  Box,
  Button,
  Container,
  Flex,
  Heading,
  Image,
  Text,
  VStack,
} from "@chakra-ui/react";
import { useToast } from "@chakra-ui/toast";

export default function Home() {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const toast = useToast();

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedImage(file);

      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const analyzeImage = async () => {
    if (!selectedImage) {
      toast({
        title: "エラー",
        description: "画像を選択してください",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setAnalyzing(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("image", selectedImage);

      const response = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("分析に失敗しました");
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Error:", error);
      toast({
        title: "エラー",
        description: "分析に失敗しました",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <Container maxW="container.md" py={8}>
      <VStack spacing={8} align="stretch">
        <Heading as="h1" size="xl" textAlign="center">
          食事バランスチェッカー
        </Heading>

        <Box>
          <Text mb={2}>
            食事の写真をアップロードして、栄養バランスを分析します
          </Text>
          <Button as="label" htmlFor="image-upload" colorScheme="blue" w="full">
            写真を選択する
            <input
              id="image-upload"
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              style={{ display: "none" }}
            />
          </Button>
        </Box>

        {previewUrl && (
          <Box>
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
              onClick={analyzeImage}
              isLoading={analyzing}
              loadingText="分析中..."
              w="full"
            >
              分析する
            </Button>
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
      </VStack>
    </Container>
  );
}
