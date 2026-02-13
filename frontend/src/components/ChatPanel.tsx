"use client";

import { useEffect, useRef, useState } from "react";
import { MessageSquare, Send, Loader2, Zap, Cpu } from "lucide-react";
import { type ChatMessage } from "@/hooks/useChat";

interface ChatPanelProps {
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
  activePaperTitle: string | null;
  onSend: (message: string) => void;
}

export default function ChatPanel({
  messages,
  loading,
  error,
  activePaperTitle,
  onSend,
}: ChatPanelProps) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    onSend(input.trim());
    setInput("");
  };

  return (
    <div className="flex h-full flex-col border-l border-gray-800 bg-gray-900">
      {/* Header */}
      <div className="border-b border-gray-800 px-4 py-3">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-brand-500" />
          <h2 className="font-semibold text-gray-100">Paper Q&A</h2>
        </div>
        {activePaperTitle && (
          <p className="mt-1 text-xs text-gray-400 line-clamp-1">
            Chatting about: {activePaperTitle}
          </p>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !loading && (
          <p className="text-center text-sm text-gray-500 mt-8">
            {activePaperTitle
              ? "Ask a question about this paper."
              : "Click a paper node to start chatting."}
          </p>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                msg.role === "user"
                  ? "bg-brand-600 text-white"
                  : "bg-gray-800 text-gray-200"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.source && (
                <span
                  className={`mt-1.5 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                    msg.source === "cache"
                      ? "bg-green-900/50 text-green-300"
                      : "bg-blue-900/50 text-blue-300"
                  }`}
                >
                  {msg.source === "cache" ? (
                    <><Zap className="h-3 w-3" /> Cached</>
                  ) : (
                    <><Cpu className="h-3 w-3" /> AI Generated</>
                  )}
                </span>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center gap-2 rounded-lg bg-gray-800 px-3 py-2 text-sm text-gray-400">
              <Loader2 className="h-4 w-4 animate-spin" />
              Thinking...
            </div>
          </div>
        )}

        {error && (
          <p className="text-center text-sm text-red-400">{error}</p>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t border-gray-800 p-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={activePaperTitle ? "Ask about this paper..." : "Select a paper first"}
            disabled={!activePaperTitle || loading}
            className="flex-1 rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-brand-500 focus:outline-none disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading || !activePaperTitle}
            className="rounded-lg bg-brand-600 px-3 py-2 text-white hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </form>
    </div>
  );
}
