"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { type ChatResponse, postChat } from "@/lib/api";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  source?: "cache" | "llm";
  context_used?: string[];
}

export function useChat(paperId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const prevPaperId = useRef(paperId);

  // Clear chat when paper changes
  useEffect(() => {
    if (paperId !== prevPaperId.current) {
      setMessages([]);
      setError(null);
      prevPaperId.current = paperId;
    }
  }, [paperId]);

  const sendMessage = useCallback(
    async (question: string) => {
      if (!paperId || !question.trim()) return;

      setMessages((prev) => [...prev, { role: "user", content: question }]);
      setLoading(true);
      setError(null);

      try {
        const res: ChatResponse = await postChat({ paper_id: paperId, question });
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: res.answer,
            source: res.source,
            context_used: res.context_used,
          },
        ]);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Unknown error";
        setError(msg);
      } finally {
        setLoading(false);
      }
    },
    [paperId],
  );

  return { messages, loading, error, sendMessage };
}
